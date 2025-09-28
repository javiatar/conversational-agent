from logging import getLogger
from uuid import UUID

from fastapi import HTTPException
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from sqlalchemy.ext.asyncio import AsyncSession

from conversational_agent.config.dependencies.openai import get_openai_api_config
from conversational_agent.data_models.api_models import ChatRequest, ChatResponse
from conversational_agent.data_models.db_models import (
    Conversation,
    Issue,
    IssueStatus,
    Role,
    Turn,
    UrgencyLevel,
)
from conversational_agent.data_models.ml_models import OpenAIAPIIssueFormat
from conversational_agent.utils import singleton

logger = getLogger(__name__)


class LLMService:
    _model_name: str = "gpt-5-nano"  # Cheap, fast

    def __init__(self):
        openai_config = get_openai_api_config()
        self._client = AsyncOpenAI(api_key=openai_config.key)

    async def chat(
        self, conversation_id: UUID, request: ChatRequest, session: AsyncSession
    ) -> ChatResponse:
        # Get the conversation requested and associated turns
        conversation = await session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(404, "Conversation not found")

        # Save the user turn and refresh the conversation so it contains it
        user_turn = Turn(role=Role.USER, text=request.message, conversation_id=conversation_id)
        session.add(user_turn)
        await session.flush()
        await session.refresh(conversation, ["turns"])

        turns = conversation.turns
        openai_messages = self._convert_turns_to_openai(turns)

        # Call the OpenAI API
        model = None
        while True:
            response = await self._client.chat.completions.parse(
                model=self._model_name,
                messages=openai_messages,
                response_format=OpenAIAPIIssueFormat,
            )
            reply = response.choices[0].message
            model = reply.parsed
            if model is not None and model.assistant_reply:
                break
            logger.warning(f"Had to re-do the API call... got back response_model: {model}")

        # Handle issue creation or append depending on whether this conversation already has an issue associated
        if model.create_issue and conversation.issue_id is None:
            await self._create_issue(conversation, model, session)
        elif model.create_issue and conversation.issue_id is not None:
            await self._update_issue(conversation, model, session)

        status = model.status or IssueStatus.IN_PROGRESS
        match status:
            case IssueStatus.REQUIRES_MANUAL_REVIEW:
                logger.warning(f"Conversation {conversation_id} requires manual review per model.")
            case IssueStatus.RESOLVED | IssueStatus.CLOSED:
                logger.info(f"Conversation {conversation_id} marked as resolved by model.")
            case _:
                logger.info(
                    f"Conversation {conversation_id} has ongoing/none status: {model.status}"
                )

        # Save assistant turn
        reply = model.assistant_reply
        assistant_turn = Turn(role=Role.ASSISTANT, text=reply, conversation_id=conversation_id)
        session.add(assistant_turn)
        return ChatResponse(
            reply=reply,
            status=status,
        )

    def _convert_turns_to_openai(self, turns: list[Turn]) -> list[ChatCompletionMessageParam]:
        messages: list[ChatCompletionMessageParam] = []
        for turn in turns:
            match turn.role.value.lower():
                case "user":
                    messages.append(ChatCompletionUserMessageParam(role="user", content=turn.text))
                case "assistant":
                    messages.append(
                        ChatCompletionAssistantMessageParam(role="assistant", content=turn.text)
                    )
                case "system":
                    messages.append(
                        ChatCompletionSystemMessageParam(role="system", content=turn.text)
                    )
                case _:
                    raise ValueError(f"Unknown role: {turn.role}")
        return messages

    async def _create_issue(
        self, conversation: Conversation, model: OpenAIAPIIssueFormat, session: AsyncSession
    ) -> Issue:
        """Create a new issue based on the ML model decision and link it to the conversation that prompted it."""
        if not model.description or not model.issue_type:
            raise ValueError("Cannot create issue without description and issue_type")

        new_issue = Issue(
            customer_id=conversation.customer_id,
            description=model.description,
            issue_type=model.issue_type,
            urgency=model.urgency or UrgencyLevel.MEDIUM,
            status=model.status or IssueStatus.IN_PROGRESS,
            order_number=model.order_number,
        )
        session.add(new_issue)

        # Link issue to conversation
        conversation.issue_id = new_issue.id
        session.add(conversation)
        logger.info(
            f"Created new issue {new_issue.id} and linked to conversation {conversation.id}"
        )
        return new_issue

    async def _update_issue(
        self, conversation: Conversation, model: OpenAIAPIIssueFormat, session: AsyncSession
    ) -> None:
        """Update an existing issue linked to the conversation based on the ML model decision."""
        if conversation.issue_id is None:
            raise ValueError("No existing issue linked to conversation to update")

        existing_issue = await session.get(Issue, conversation.issue_id)
        if not existing_issue:
            raise ValueError("Linked issue not found in database")

        if model.description:
            existing_issue.description = model.description
        if model.issue_type:
            existing_issue.issue_type = model.issue_type
        if model.urgency:
            existing_issue.urgency = model.urgency
        if model.status:
            existing_issue.status = model.status
        if model.order_number:
            existing_issue.order_number = model.order_number

        session.add(existing_issue)
        logger.info(f"Updated existing issue {existing_issue.id} with new information")


@singleton
def get_llm_service() -> LLMService:
    return LLMService()
