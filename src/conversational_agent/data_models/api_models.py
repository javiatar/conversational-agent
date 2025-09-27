from uuid import UUID

from pydantic import BaseModel

from conversational_agent.data_models.db_models import IssueStatus


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


# --- Chat with Agent ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    status: IssueStatus
