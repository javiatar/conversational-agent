import logging

from fastapi import APIRouter, HTTPException

from conversational_agent.config.dependencies.postgres import SessionDep
from conversational_agent.data_models.api_models import (
    LogInRequest,
    LogInResponse,
    StartConversationRequest,
    StartConversationResponse,
)
from conversational_agent.data_models.db_models import Customer
from conversational_agent.services.agent_service import get_service

logger = logging.getLogger(__name__)


def agent_router():
    router = APIRouter(prefix="/agent", tags=["agent"])

    @router.post("/log_in")
    async def log_in_user(request: LogInRequest, session: SessionDep) -> LogInResponse:
        service = get_service()
        return await service.log_in_user(request, session)

    @router.post("/start_conversation")
    async def start_conversation(
        request: StartConversationRequest, session: SessionDep
    ) -> StartConversationResponse:
        service = get_service()
        customer = await session.get(Customer, request.customer_id)
        if not customer:
            raise HTTPException(401, detail="Customer not recognized - please log in first.")

        return await service.start_conversation(request, session)

    return router
