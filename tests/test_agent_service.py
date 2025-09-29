from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from conversational_agent.data_models.api_models import (
    LogInRequest,
    LogInResponse,
    StartConversationRequest,
    StartConversationResponse,
)
from conversational_agent.data_models.db_models import (
    Conversation,
    Customer,
    Role,
)
from conversational_agent.services.agent_service import AgentService, get_agent_service


class TestAgentService:
    """Test suite for AgentService business logic"""

    @pytest.fixture
    def service(self):
        """Create AgentService instance"""
        return AgentService()

    @pytest.fixture
    def mock_session(self):
        """Mock AsyncSession"""
        session = AsyncMock(spec=AsyncSession)
        # session.add should be synchronous, not async
        session.add = Mock(return_value=None)
        session.add_all = Mock(return_value=None)
        return session

    @pytest.fixture
    def sample_customer(self):
        """Sample customer for testing"""
        return Customer(id=uuid4(), name="John Doe", email="john@example.com")

    @pytest.mark.asyncio
    async def test_log_in_existing_user(self, service, mock_session, sample_customer: Customer):
        """Test logging in an existing user"""

        mock_result = Mock()  # Use Mock instead of AsyncMock
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_session.execute.return_value = mock_result

        request = LogInRequest(name=sample_customer.name, email=sample_customer.email)

        # Act
        response = await service.log_in_user(request, mock_session)

        # Assert
        assert isinstance(response, LogInResponse)
        assert response.id == sample_customer.id
        assert response.name == sample_customer.name
        assert response.email == sample_customer.email
        assert response.new_user is False

        # Verify database interaction
        mock_session.execute.assert_called_once()
        mock_session.add.assert_not_called()  # Existing user shouldn't be added

    @pytest.mark.asyncio
    async def test_log_in_new_user(self, service, mock_session):
        """Test creating a new user on login"""
        mock_result = Mock()  # Use Mock instead of AsyncMock
        mock_result.scalar_one_or_none.return_value = None  # User doesn't exist
        mock_session.execute.return_value = mock_result

        request = LogInRequest(name="Jane Smith", email="jane@example.com")

        # Act
        response = await service.log_in_user(request, mock_session)

        # Assert
        assert isinstance(response, LogInResponse)
        assert response.name == "Jane Smith"
        assert response.email == "jane@example.com"
        assert response.new_user is True

        # Verify new user was added to session
        mock_session.add.assert_called_once()
        added_customer = mock_session.add.call_args[0][0]
        assert isinstance(added_customer, Customer)
        assert added_customer.name == "Jane Smith"
        assert added_customer.email == "jane@example.com"

    @pytest.mark.asyncio
    @patch("conversational_agent.services.agent_service.get_rag_config")
    async def test_start_conversation_with_rag_enabled(
        self, mock_rag_config, service, mock_session
    ):
        """Test starting conversation with RAG enabled"""
        # Arrange
        customer_id = uuid4()
        mock_rag_config.return_value.enabled = True

        request = StartConversationRequest(customer_id=customer_id)

        # Act
        response = await service.start_conversation(request, mock_session)

        # Assert
        assert isinstance(response, StartConversationResponse)
        assert response.conversation_id is not None
        assert "FakeAgentWhoDefinitelyCaresAboutYou" in response.message
        assert "Support Agent" in response.message

        # Verify database operations
        mock_session.add.assert_called_once()  # Conversation added
        mock_session.add_all.assert_called_once()  # System and initial turns added

        # Check what was added via add_all
        turns = mock_session.add_all.call_args[0][0]
        assert len(turns) == 2  # System turn + initial assistant turn

        system_turn = turns[0]
        initial_turn = turns[1]

        assert system_turn.role == Role.SYSTEM
        assert "CONTEXT" in system_turn.text  # RAG system message

        assert initial_turn.role == Role.ASSISTANT
        assert initial_turn.text == response.message

    @pytest.mark.asyncio
    @patch("conversational_agent.services.agent_service.get_rag_config")
    async def test_start_conversation_with_rag_disabled(
        self, mock_rag_config, service, mock_session
    ):
        """Test starting conversation with RAG disabled"""
        customer_id = uuid4()
        mock_rag_config.return_value.enabled = False

        request = StartConversationRequest(customer_id=customer_id)

        # Act
        response = await service.start_conversation(request, mock_session)

        # Assert
        assert isinstance(response, StartConversationResponse)

        # Check that basic system message was used (not RAG)
        turns = mock_session.add_all.call_args[0][0]
        system_turn = turns[0]

        assert system_turn.role == Role.SYSTEM
        assert "CONTEXT" not in system_turn.text  # Basic system message

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_start_conversation_entities_and_validation(self, service, mock_session):
        """Test conversation creation with proper entities, UUID validation, and agent consistency"""
        # Arrange
        customer_id = uuid4()
        request = StartConversationRequest(customer_id=customer_id)

        # Act - Test multiple conversations to verify different IDs
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = False
            response1 = await service.start_conversation(request, mock_session)
            response2 = await service.start_conversation(request, mock_session)

        # Assert conversation creation and database entities
        conversation_call = mock_session.add.call_args[0][0]
        assert isinstance(conversation_call, Conversation)
        assert conversation_call.customer_id == customer_id

        # Assert turns creation
        turns = mock_session.add_all.call_args[0][0]
        assert len(turns) == 2
        system_turn, assistant_turn = turns

        # System turn verification
        assert system_turn.role == Role.SYSTEM
        assert system_turn.conversation_id == conversation_call.id
        assert len(system_turn.text) > 0

        # Assistant turn verification
        assert assistant_turn.role == Role.ASSISTANT
        assert assistant_turn.conversation_id == conversation_call.id
        assert assistant_turn.text == response1.message
        assert "Welcome to FakeAgentWhoDefinitelyCaresAboutYou" in assistant_turn.text

        # Test agent name consistency
        expected_name = "FakeAgentWhoDefinitelyCaresAboutYou"
        assert service.agent_name == expected_name
        assert expected_name in response1.message

        # Test UUID validation and uniqueness
        assert isinstance(response1.conversation_id, uuid4().__class__)
        assert isinstance(response2.conversation_id, uuid4().__class__)
        assert len(str(response1.conversation_id)) == 36
        assert response1.conversation_id != response2.conversation_id
        assert mock_session.add.call_count == 2  # Two conversations created
        assert mock_session.add_all.call_count == 2  # Two sets of turns created


class TestAgentServiceSingleton:
    """Test singleton behavior of AgentService"""

    def test_singleton_behavior(self):
        """Test that get_agent_service returns the same instance"""

        service1 = get_agent_service()
        service2 = get_agent_service()

        assert service1 is service2  # Same object instance
        assert id(service1) == id(service2)  # Same memory address


class TestAgentServiceIntegrationScenarios:
    """Integration-style tests for common user scenarios"""

    @pytest.fixture
    def service(self):
        return AgentService()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        # session.add should be synchronous, not async
        session.add = Mock(return_value=None)
        session.add_all = Mock(return_value=None)
        return session

    def _setup_mock_result(self, return_value):
        """Helper to create consistent mock results"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = return_value
        return mock_result

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "is_new_user,rag_enabled",
        [
            (True, True),  # New user with RAG
            (False, False),  # Existing user without RAG
        ],
    )
    async def test_complete_user_flow(self, service, mock_session, is_new_user, rag_enabled):
        """Test complete flow: login -> start conversation for new and existing users"""
        # Step 1: Setup user login
        if is_new_user:
            existing_customer = None
            name, email = "Alice Johnson", "alice@example.com"
            expected_add_calls = 2  # Customer + Conversation
        else:
            existing_customer = Customer(id=uuid4(), name="Bob Smith", email="bob@example.com")
            name, email = existing_customer.name, existing_customer.email
            expected_add_calls = 1  # Only conversation

        mock_result = self._setup_mock_result(existing_customer)
        mock_session.execute.return_value = mock_result

        # Step 2: User logs in
        login_request = LogInRequest(name=name, email=email)
        login_response = await service.log_in_user(login_request, mock_session)

        assert login_response.new_user == is_new_user
        customer_id = existing_customer.id if existing_customer else login_response.id

        # Step 3: Start conversation
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = rag_enabled

            conv_request = StartConversationRequest(customer_id=customer_id)
            conv_response = await service.start_conversation(conv_request, mock_session)

        # Verify results
        assert conv_response.conversation_id is not None
        assert "FakeAgentWhoDefinitelyCaresAboutYou" in conv_response.message
        assert mock_session.add.call_count == expected_add_calls
        assert mock_session.add_all.call_count == 1  # Turns
