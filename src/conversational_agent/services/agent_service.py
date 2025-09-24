from conversational_agent.data_models.agent import (
    AgentServiceDoThingRequest,
    AgentServiceDoThingResponse,
)


class AgentService:
    async def do_thing(self, request: AgentServiceDoThingRequest) -> AgentServiceDoThingResponse:
        return AgentServiceDoThingResponse(output=request.input)
