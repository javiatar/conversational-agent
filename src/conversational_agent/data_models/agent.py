from pydantic import BaseModel


class AgentServiceDoThingRequest(BaseModel):
    input: str


class AgentServiceDoThingResponse(BaseModel):
    output: str
