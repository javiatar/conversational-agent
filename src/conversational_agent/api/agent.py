import logging

from fastapi import APIRouter

from conversational_agent.data_models.api_models import (
    AgentServiceLogInRequest,
    AgentServiceLogInResponse,
)
from conversational_agent.services.agent_service import AgentService

logger = logging.getLogger(__name__)


def agent_router():
    router = APIRouter(prefix="/agent", tags=["agent"])

    @router.post("/log_in")
    async def log_in_user(request: AgentServiceLogInRequest) -> AgentServiceLogInResponse:
        service = AgentService()
        return await service.log_in_user(request)

    return router
