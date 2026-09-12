from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.health import router as health_router
from src.api.sessions import router as sessions_router
from src.core.logging import configure_logging
from src.core.settings import get_settings
from src.modules.auth import CookieAuthAdapter
from src.modules.llm.dialogue_stub import LocalDialogueStub
from src.modules.monitor import NoOpObs


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    application = FastAPI(title="agentic-trip")
    origins = [
        origin.strip()
        for origin in settings.cors_allowed_origins.split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.state.auth_port = CookieAuthAdapter()
    # P1: local dialogue stub (no live LiteLLM). Fail-soft tests inject StubLlmGateway.
    application.state.llm_gateway = LocalDialogueStub()
    application.state.obs_port = NoOpObs()
    application.include_router(health_router)
    application.include_router(sessions_router)
    return application


app = create_app()
