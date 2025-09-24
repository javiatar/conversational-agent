"""Stubbed module to set up and configure an Opensearch client"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenSearchSettings(BaseSettings):
    # OpenSearch config settings can be passed as env vars (e.g in .env file) and must match
    # "OPENSEARCH__<ATTR__SUBATTR>"
    model_config = SettingsConfigDict(
        env_prefix="OPENSEARCH__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",  # Ignore unrecognized env vars in .env
    )
