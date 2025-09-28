import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException

from conversational_agent.config.dependencies.database import SessionDep
from conversational_agent.data_models.api_models import (
    ChatRequest,
    ChatResponse,
    LogInRequest,
    LogInResponse,
    StartConversationRequest,
    StartConversationResponse,
)
from conversational_agent.data_models.db_models import Customer
from conversational_agent.services.agent_service import get_agent_service
from conversational_agent.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


def agent_router():
    router = APIRouter(prefix="/agent", tags=["agent"])

    @router.post("/log_in")
    async def log_in_user(request: LogInRequest, session: SessionDep) -> LogInResponse:
        service = get_agent_service()
        return await service.log_in_user(request, session)

    @router.post("/start_conversation")
    async def start_conversation(
        request: StartConversationRequest, session: SessionDep
    ) -> StartConversationResponse:
        service = get_agent_service()
        customer = await session.get(Customer, request.customer_id)
        if not customer:
            raise HTTPException(401, detail="Customer not recognized - please log in first.")

        return await service.start_conversation(request, session)

    @router.post("/chat/{conversation_id}")
    async def chat(
        conversation_id: UUID, request: ChatRequest, session: SessionDep
    ) -> ChatResponse:
        service = get_llm_service()
        return await service.chat(conversation_id, request, session)

    @router.get("/{conversation_id}/summary")
    async def conversation_summary(conversation_id: UUID, session: SessionDep) -> str:
        service = get_llm_service()
        return await service.summarize_conversation(conversation_id, session)

    return router
