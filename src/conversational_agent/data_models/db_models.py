"""Data models for the conversational agent service.

- A Customer can have 0 or more Issues and 0 or more Conversations associated with them.
- Each Conversation consists of multiple Turns, each with a role (user, assistant, system)
  and text content.
    - Note: these turns are timestamped and used by the ML Agent to generate responses.
- Each Issue can have 1 or more Conversations associated with it.
    - Note: not all conversations need to be linked to an issue, e.g. general inquiries.
"""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class IssueType(StrEnum):
    DELIVERY = "delivery"
    PRODUCT = "product"
    BILLING = "billing"
    OTHER = "other"


class IssueStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


class UrgencyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Customer(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field()
    email: str = Field()

    conversations: list["Conversation"] = Relationship(
        back_populates="customer", cascade_delete=True
    )
    issues: list["Issue"] = Relationship(back_populates="customer", cascade_delete=True)


class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # A conversation consists of multiple turns
    turns: list["Turn"] = Relationship(back_populates="conversation", cascade_delete=True)

    # A conversation is always linked to a customer
    customer_id: UUID = Field(foreign_key="customer.id")
    customer: Customer = Relationship(back_populates="conversations")

    # A conversation can optionally be linked to a single issue
    issue_id: UUID | None = Field(default=None, foreign_key="issue.id")
    # NO CASCADE: Deleting a conversations should not delete the issue
    issue: Optional["Issue"] = Relationship(back_populates="conversations")


class Turn(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role: Role
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Each turn is linked to a single conversation
    conversation_id: UUID = Field(foreign_key="conversation.id")
    conversation: "Conversation" = Relationship(back_populates="turns")


class Issue(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    description: str = Field(
        max_length=1000, description="Freeform text describing the issue, max 1000 chars"
    )
    issue_type: IssueType = Field(default=IssueType.OTHER)
    urgency: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM)
    status: IssueStatus = Field(default=IssueStatus.IN_PROGRESS)
    order_number: str | None = Field(default=None, description="Optional order number")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Each issue is linked to a customer (who can have 0+ issues)
    customer_id: UUID = Field(foreign_key="customer.id")
    customer: Customer = Relationship(back_populates="issues")

    # Each issue can have 0+ conversations, expecting at least 1
    # NO CASCADE: Keep conversations when issue is deleted
    conversations: list["Conversation"] = Relationship(back_populates="issue")
