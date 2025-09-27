from collections.abc import AsyncIterator
from http.client import HTTPException
from logging import getLogger

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel
from typing_extensions import Annotated

# Ensure models are imported so SQLModel metadata is populated
import conversational_agent.data_models  # noqa: F401
from conversational_agent.utils import singleton

logger = getLogger(__name__)


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""

    # Use in-memory SQLite by default (use e.g PostgreSQL for robustness via env vars)
    url: str = Field(default="sqlite+aiosqlite:///:memory:")

    # Database config settings can be passed as env vars (e.g in .env file) and must match "DB_CONFIG__<ATTR__SUBATTR>"
    model_config = SettingsConfigDict(
        env_prefix="DB_CONFIG__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",  # Ignore unrecognized env vars in .env
    )


@singleton
def get_db_config() -> DatabaseConfig:
    """Get the database configuration."""
    return DatabaseConfig()


@singleton
def create_engine() -> AsyncEngine:
    """Create the SQLAlchemy engine."""
    db_config = get_db_config()
    return create_async_engine(db_config.url, future=True)


async def init_db() -> None:
    """Initialize database tables."""
    async with create_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Context manager to get a new database session from the configured engine."""
    session_maker = async_sessionmaker(create_engine(), expire_on_commit=False)
    session = session_maker()
    try:
        yield session
        await session.commit()
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        logger.error(e, exc_info=True)
        await session.rollback()
        raise
    finally:
        await session.close()


# Annotated fastapi dependency for getting DB session
SessionDep = Annotated[AsyncSession, Depends(get_session)]
