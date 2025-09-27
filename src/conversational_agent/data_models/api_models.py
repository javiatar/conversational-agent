from uuid import UUID

from pydantic import BaseModel


class AgentServiceLogInRequest(BaseModel):
    name: str
    email: str


class AgentServiceLogInResponse(BaseModel):
    id: UUID
    name: str
    email: str
    new_user: bool = False
