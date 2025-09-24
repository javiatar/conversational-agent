import logging

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def include_models(app: FastAPI, /, *models: type[BaseModel]):
    """
    Include the passed models in the FastAPI app's generated OpenAPI specifiction. These models
    don't need to be present in any actual endpoints; instead, we created dummy endpoints which have
    no associated methods. Using dummy endpoints forces FastAPI to include their associated models
    in the spec, but specifying that there are no HTTP methods causes it not to include the
    endpoints themselves.
    """
    for idx, model in enumerate(models):
        app.add_api_route(
            f"/dummy{idx}",
            lambda: None,
            methods=[],
            response_model=model,
            operation_id=f"dummy{idx}",
        )
