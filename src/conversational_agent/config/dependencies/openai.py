from logging import getLogger

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure models are imported so SQLModel metadata is populated
from conversational_agent.utils import singleton  # noqa: F401

logger = getLogger(__name__)


class OpenAIAPIConfig(BaseSettings):
    """OpenAI API configuration settings."""

    # No default, must be set via env var or .env file
    key: str = Field(default=..., description="OpenAI API key")

    # OpenAI API config settings can be passed as env vars (e.g in .env file) and must match "OPENAI_API__<ATTR__SUBATTR>"
    model_config = SettingsConfigDict(
        env_prefix="OPENAI_API__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",  # Ignore unrecognized env vars in .env
    )


@singleton
def get_openai_api_config() -> OpenAIAPIConfig:
    """Get the OpenAI API configuration."""
    return OpenAIAPIConfig()
