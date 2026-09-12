from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from src.api.health import router as health_router
from src.api.sessions import router as sessions_router
from src.core.logging import configure_logging
from src.core.settings import get_settings
from src.modules.agents.dialogue import DialogueDeps, DialogueRunner, build_checkpointer
from src.modules.auth import CookieAuthAdapter
from src.modules.geo import GeoService, NominatimAdapter
from src.modules.llm.litellm_adapter import build_llm_gateway
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
    application.state.llm_gateway = build_llm_gateway(api_key=settings.llm_api_key)
    application.state.obs_port = NoOpObs()
    application.state.geo_gateway = NominatimAdapter(
        base_url=settings.nominatim_base_url,
        user_agent=settings.nominatim_user_agent,
        timeout_seconds=settings.nominatim_timeout_seconds,
    )
    application.state.geo_service = GeoService(application.state.geo_gateway)

    # Prefer Postgres checkpointer; fall soft to in-memory (session.hitl remains FE SSOT).
    try:
        checkpointer = build_checkpointer(
            settings.database_url,
            prefer_postgres=settings.dialogue_prefer_postgres_checkpointer,
        )
    except Exception:
        checkpointer = InMemorySaver()

    application.state.dialogue_runner = DialogueRunner(
        DialogueDeps(
            llm=application.state.llm_gateway,
            geo=application.state.geo_service,
        ),
        checkpointer=checkpointer,
    )
    application.include_router(health_router)
    application.include_router(sessions_router)
    return application


app = create_app()
