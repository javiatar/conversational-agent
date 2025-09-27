import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http.client import HTTPException
from logging import getLogger

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

logger = getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/conversational_agent_db"
)

# Create async engine (using psycopg3)
engine = create_async_engine(DATABASE_URL, echo=True, future=True)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Context manager to get a new database session from the configured engine."""
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
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


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
