from fastapi import FastAPI

from src.api.health import router as health_router
from src.core.logging import configure_logging
from src.core.settings import get_settings
from src.modules.auth import StubAuthAdapter
from src.modules.llm import StubLlmGateway
from src.modules.monitor import NoOpObs


def create_app() -> FastAPI:
    get_settings()
    configure_logging()
    application = FastAPI(title="agentic-trip")
    application.state.auth_port = StubAuthAdapter()
    application.state.llm_gateway = StubLlmGateway()
    application.state.obs_port = NoOpObs()
    application.include_router(health_router)
    return application


app = create_app()
