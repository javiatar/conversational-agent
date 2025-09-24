import logging

from fastapi import APIRouter

from conversational_agent.data_models.agent import (
    AgentServiceDoThingRequest,
    AgentServiceDoThingResponse,
)
from conversational_agent.services.agent_service import AgentService

logger = logging.getLogger(__name__)


async def do_thing(request: AgentServiceDoThingRequest) -> AgentServiceDoThingResponse:
    service = AgentService()
    return await service.do_thing(request)


def router():
    fastapi_router = APIRouter(prefix="/agent", tags=["agent"])
    fastapi_router.add_api_route("do_thing", do_thing, methods=["POST"])
    return fastapi_router
