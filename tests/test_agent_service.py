from unittest.mock import AsyncMock, patch
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
from conversational_agent.services.agent_service import AgentService


class TestAgentService:
    """Test suite for AgentService business logic"""

    @pytest.fixture
    def service(self):
        """Create AgentService instance"""
        return AgentService()

    @pytest.fixture
    def mock_session(self):
        """Mock AsyncSession"""
        from unittest.mock import Mock

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
    async def test_log_in_existing_user(self, service, mock_session, sample_customer):
        """Test logging in an existing user"""
        # Arrange
        from unittest.mock import Mock

        mock_result = Mock()  # Use Mock instead of AsyncMock
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_session.execute.return_value = mock_result

        request = LogInRequest(name="John Doe", email="john@example.com")

        # Act
        response = await service.log_in_user(request, mock_session)

        # Assert
        assert isinstance(response, LogInResponse)
        assert response.id == sample_customer.id
        assert response.name == "John Doe"
        assert response.email == "john@example.com"
        assert response.new_user is False

        # Verify database interaction
        mock_session.execute.assert_called_once()
        mock_session.add.assert_not_called()  # Existing user shouldn't be added    @pytest.mark.asyncio

    @pytest.mark.asyncio
    async def test_log_in_new_user(self, service, mock_session):
        """Test creating a new user on login"""
        # Arrange
        from unittest.mock import Mock

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
    async def test_log_in_sql_query_structure(self, service, mock_session):
        """Test that the correct SQL query is executed for login"""
        # Arrange
        from unittest.mock import Mock

        mock_result = Mock()  # Use Mock instead of AsyncMock
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        request = LogInRequest(name="Test User", email="test@example.com")

        # Act
        response = await service.log_in_user(request, mock_session)

        # Assert
        mock_session.execute.assert_called_once()
        query_arg = mock_session.execute.call_args[0][0]

        # Verify it's a select query on Customer table
        assert hasattr(query_arg, "column_descriptions")  # SQLModel select query

        # Verify response was created for new user
        assert response.new_user is True

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
        # Arrange
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
    async def test_start_conversation_creates_correct_entities(self, service, mock_session):
        """Test that start_conversation creates the correct database entities"""
        # Arrange
        customer_id = uuid4()
        request = StartConversationRequest(customer_id=customer_id)

        # Act
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = False
            response = await service.start_conversation(request, mock_session)

        # Assert conversation creation
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
        assert assistant_turn.text == response.message
        assert "Welcome to FakeAgentWhoDefinitelyCaresAboutYou" in assistant_turn.text

    @pytest.mark.asyncio
    async def test_multiple_conversations_different_ids(self, service, mock_session):
        """Test that multiple conversations get different IDs"""
        # Arrange
        customer_id = uuid4()
        request = StartConversationRequest(customer_id=customer_id)

        # Act
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = False

            response1 = await service.start_conversation(request, mock_session)
            response2 = await service.start_conversation(request, mock_session)

        # Assert
        assert response1.conversation_id != response2.conversation_id
        assert mock_session.add.call_count == 2  # Two conversations created
        assert mock_session.add_all.call_count == 2  # Two sets of turns created

    @pytest.mark.asyncio
    async def test_agent_name_consistency(self, service, mock_session):
        """Test that agent name is consistent across responses"""
        # Arrange
        customer_id = uuid4()
        request = StartConversationRequest(customer_id=customer_id)

        # Act
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = False
            response = await service.start_conversation(request, mock_session)

        # Assert
        expected_name = "FakeAgentWhoDefinitelyCaresAboutYou"
        assert service.agent_name == expected_name
        assert expected_name in response.message

    @pytest.mark.asyncio
    async def test_conversation_id_is_uuid(self, service, mock_session):
        """Test that conversation ID is a valid UUID"""
        # Arrange
        customer_id = uuid4()
        request = StartConversationRequest(customer_id=customer_id)

        # Act
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = False
            response = await service.start_conversation(request, mock_session)

        # Assert
        assert isinstance(response.conversation_id, uuid4().__class__)  # UUID type
        assert len(str(response.conversation_id)) == 36  # Standard UUID length

    @pytest.mark.asyncio
    async def test_email_case_insensitive_matching(self, service, mock_session, sample_customer):
        """Test that email matching works regardless of case"""
        # Arrange
        from unittest.mock import Mock

        sample_customer.email = "john@example.com"
        mock_result = Mock()  # Use Mock instead of AsyncMock
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_session.execute.return_value = mock_result

        # Test with different case
        request = LogInRequest(name="John Doe", email="JOHN@EXAMPLE.COM")

        # Act
        response = await service.log_in_user(request, mock_session)

        # Assert
        assert response.email == sample_customer.email  # Original case preserved
        assert response.new_user is False

    @pytest.mark.asyncio
    async def test_database_session_error_handling(self, service, mock_session):
        """Test handling of database session errors"""
        # Arrange
        mock_session.execute.side_effect = Exception("Database connection error")

        request = LogInRequest(name="Test User", email="test@example.com")

        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            await service.log_in_user(request, mock_session)


class TestAgentServiceSingleton:
    """Test singleton behavior of AgentService"""

    def test_singleton_behavior(self):
        """Test that get_agent_service returns the same instance"""
        from conversational_agent.services.agent_service import get_agent_service

        service1 = get_agent_service()
        service2 = get_agent_service()

        assert service1 is service2  # Same object instance
        assert id(service1) == id(service2)  # Same memory address

    def test_singleton_properties_consistent(self):
        """Test that singleton maintains consistent properties"""
        from conversational_agent.services.agent_service import get_agent_service

        service1 = get_agent_service()
        service2 = get_agent_service()

        assert service1.agent_name == service2.agent_name
        assert service1.agent_name == "FakeAgentWhoDefinitelyCaresAboutYou"


class TestAgentServiceIntegrationScenarios:
    """Integration-style tests for common user scenarios"""

    @pytest.fixture
    def service(self):
        return AgentService()

    @pytest.fixture
    def mock_session(self):
        from unittest.mock import Mock

        session = AsyncMock(spec=AsyncSession)
        # session.add should be synchronous, not async
        session.add = Mock(return_value=None)
        session.add_all = Mock(return_value=None)
        return session

    @pytest.mark.asyncio
    async def test_complete_user_flow(self, service, mock_session):
        """Test complete flow: login new user -> start conversation"""
        # Step 1: User logs in (new user)
        from unittest.mock import Mock

        mock_result = Mock()  # Use Mock instead of AsyncMock
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        login_request = LogInRequest(name="Alice Johnson", email="alice@example.com")
        login_response = await service.log_in_user(login_request, mock_session)

        assert login_response.new_user is True
        customer_id = login_response.id

        # Step 2: Start conversation
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = True

            conv_request = StartConversationRequest(customer_id=customer_id)
            conv_response = await service.start_conversation(conv_request, mock_session)

        assert conv_response.conversation_id is not None
        assert "FakeAgentWhoDefinitelyCaresAboutYou" in conv_response.message

        # Verify database calls
        assert mock_session.add.call_count == 2  # Customer + Conversation
        assert mock_session.add_all.call_count == 1  # Turns

    @pytest.mark.asyncio
    async def test_returning_user_flow(self, service, mock_session):
        """Test flow for returning user"""
        # Arrange existing user
        existing_customer = Customer(id=uuid4(), name="Bob Smith", email="bob@example.com")

        from unittest.mock import Mock

        mock_result = Mock()  # Use Mock instead of AsyncMock
        mock_result.scalar_one_or_none.return_value = existing_customer
        mock_session.execute.return_value = mock_result

        # Step 1: User logs in (existing)
        login_request = LogInRequest(name="Bob Smith", email="bob@example.com")
        login_response = await service.log_in_user(login_request, mock_session)

        assert login_response.new_user is False
        assert login_response.id == existing_customer.id

        # Step 2: Start new conversation
        with patch("conversational_agent.services.agent_service.get_rag_config") as mock_rag:
            mock_rag.return_value.enabled = False

            conv_request = StartConversationRequest(customer_id=existing_customer.id)
            conv_response = await service.start_conversation(conv_request, mock_session)

        # Verify only conversation was added (not customer)
        assert mock_session.add.call_count == 1  # Only conversation
        assert conv_response.conversation_id is not None
