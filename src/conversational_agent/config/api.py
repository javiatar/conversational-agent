import uvicorn

from conversational_agent.api.endpoints import app


def api_server(host: str = "0.0.0.0", port: int = 5020):
    fastapi_app = app()
    config = uvicorn.Config(fastapi_app, host=host, port=port, log_level="info")
    return uvicorn.Server(config)


async def run_api_server(host: str = "0.0.0.0", port: int = 5020):
    server = api_server(host, port)
    await server.serve()
