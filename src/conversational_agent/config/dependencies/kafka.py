"""Stubbed module to set up and configure a Kafka client"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BrokerConnectionConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KAFKA__", env_nested_delimiter="__", env_file=".env"
    )
