import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from conversational_agent.api.agent import agent_router
from conversational_agent.config.dependencies.database import init_db

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def health():
    logger.info("Example info log")
    return {"status": "ok"}


def app():
    fastapi_app = FastAPI(version="0.1.0")

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize DB on startup (create tables, etc.)
    fastapi_app.add_event_handler("startup", init_db)
    # Simple health check endpoint
    fastapi_app.add_api_route("/health", health, tags=["health"])

    # Add routers for different API areas in the application
    fastapi_app.include_router(agent_router())

    return fastapi_app
