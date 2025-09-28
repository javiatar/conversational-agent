"""Stubbed module to set up and configure an Opensearch client"""

# src/conversational_agent/config/dependencies/rag.py

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from conversational_agent.utils import STORAGE_PATH, singleton


class RAGConfig(BaseSettings):
    """RAG configuration settings."""

    index_path: Path = Field(
        default=STORAGE_PATH / "indexes/sparse", description="Path to sparse index"
    )
    kb_path: Path = Field(
        default=STORAGE_PATH / "knowledge_base.jsonl", description="Path to knowledge base"
    )
    enabled: bool = Field(
        default=False, description="Whether to enable RAG for the chat service endpoint"
    )
    model_config = SettingsConfigDict(
        env_prefix="RAG__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )


@singleton
def get_rag_config() -> RAGConfig:
    return RAGConfig()
