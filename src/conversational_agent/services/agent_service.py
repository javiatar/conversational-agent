from logging import getLogger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from conversational_agent.config.dependencies.rag import get_rag_config
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
    Turn,
)
from conversational_agent.data_models.ml_models import (
    SYSTEM_MESSAGE,
    SYSTEM_MESSAGE_WITH_RAG,
)
from conversational_agent.utils import singleton

logger = getLogger(__name__)


class AgentService:
    agent_name: str = "FakeAgentWhoDefinitelyCaresAboutYou"

    async def log_in_user(self, request: LogInRequest, session: AsyncSession) -> LogInResponse:
        # Check if user exists
        result = await session.execute(select(Customer).where(Customer.email == request.email))
        customer = result.scalar_one_or_none()
        new_user = False

        if customer is None:
            # Customer is new (didn't previously exist), create them
            new_user = True
            customer = Customer(name=request.name, email=request.email)
            session.add(customer)

        return LogInResponse(
            id=customer.id, name=customer.name, email=customer.email, new_user=new_user
        )

    async def start_conversation(
        self, request: StartConversationRequest, session: AsyncSession
    ) -> StartConversationResponse:
        conversation = Conversation(customer_id=request.customer_id)
        session.add(conversation)

        rag_config = get_rag_config()
        # Create initial system turn (hidden from user) to ground ML model and its objective
        system_turn = Turn(
            role=Role.SYSTEM,
            text=SYSTEM_MESSAGE_WITH_RAG if rag_config.enabled else SYSTEM_MESSAGE,
            conversation_id=conversation.id,
        )

        # Create initial user turn (visible to user) to start the conversation
        initial_greeting = (
            f"Welcome to {self.agent_name}! I'm a Support Agent explicitly designed "
            "to triage any issues you may have in order to get you the help you need as quickly "
            "as possible. How can I assist you today?"
        )
        initial_turn = Turn(
            role=Role.ASSISTANT, text=initial_greeting, conversation_id=conversation.id
        )
        session.add_all([system_turn, initial_turn])

        return StartConversationResponse(conversation_id=conversation.id, message=initial_turn.text)


@singleton
def get_agent_service() -> AgentService:
    return AgentService()
