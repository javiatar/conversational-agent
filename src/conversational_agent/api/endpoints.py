import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from conversational_agent.api.agent import router as pipeline_router

logger = logging.getLogger(__name__)


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

    fastapi_app.include_router(pipeline_router())

    fastapi_app.add_api_route("/health", health, tags=["health"])

    return fastapi_app
