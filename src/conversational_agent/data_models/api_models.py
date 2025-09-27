from uuid import UUID

from pydantic import BaseModel


# --- Log in ---
class LogInRequest(BaseModel):
    name: str
    email: str


class LogInResponse(BaseModel):
    id: UUID
    name: str
    email: str
    new_user: bool


# --- Start Conversation ---
class StartConversationRequest(BaseModel):
    customer_id: UUID


class StartConversationResponse(BaseModel):
    conversation_id: UUID
    message: str
