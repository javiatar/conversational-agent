from sqlmodel import select

from conversational_agent.config.dependencies.postgres import get_session
from conversational_agent.data_models.api_models import (
    AgentServiceLogInRequest,
    AgentServiceLogInResponse,
)
from conversational_agent.data_models.db_models import Customer
from conversational_agent.utils import singleton


@singleton
class AgentService:
    async def log_in_user(self, request: AgentServiceLogInRequest) -> AgentServiceLogInResponse:
        async with get_session() as session:
            # Check if user exists
            result = await session.execute(select(Customer).where(Customer.email == request.email))
            customer = result.scalar_one_or_none()
            new_user = False

            if customer is None:
                # Customer is new (didn't previously exist), create them
                new_user = True
                customer = Customer(name=request.name, email=request.email)
                session.add(customer)
                await session.commit()
                await session.refresh(customer)

            return AgentServiceLogInResponse(
                id=customer.id, name=customer.name, email=customer.email, new_user=new_user
            )
