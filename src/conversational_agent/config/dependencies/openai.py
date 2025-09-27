from logging import getLogger

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure models are imported so SQLModel metadata is populated
import conversational_agent.data_models  # noqa: F401

logger = getLogger(__name__)


class OpenAIAPIConfig(BaseSettings):
    """OpenAI API configuration settings."""

    key: str = Field(...)

    # OpenAI API config settings can be passed as env vars (e.g in .env file) and must match "OPENAI_API__<ATTR__SUBATTR>"
    model_config = SettingsConfigDict(
        env_prefix="OPENAI_API__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",  # Ignore unrecognized env vars in .env
    )
