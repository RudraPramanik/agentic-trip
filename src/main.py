from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from src.api.catalog import router as catalog_router
from src.api.generate import router as generate_router
from src.api.health import router as health_router
from src.api.revise import router as revise_router
from src.api.sessions import router as sessions_router
from src.api.trips import router as trips_router
from src.modules.media import StubMediaProvider
from src.core.logging import configure_logging
from src.core.settings import get_settings
from src.modules.agents.dialogue import DialogueDeps, DialogueRunner, build_checkpointer
from src.modules.agents.runner import InProcessGenerateRunner
from src.modules.auth import CookieAuthAdapter
from src.modules.catalog import (
    ArqAcquireQueue,
    DefaultPlacesFacade,
    InlineAcquireQueue,
    OtmAdapter,
    OverpassAdapter,
)
from src.modules.geo import GeoService, NominatimAdapter
from src.modules.llm.litellm_adapter import build_llm_gateway
from src.modules.monitor import NoOpObs
from src.modules.planner import GreedyTravelEngine


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
    application.state.llm_gateway = build_llm_gateway(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        api_base=settings.llm_api_base,
        embedding_model=settings.embedding_model,
        dialogue_stub_fallback=False,
    )
    application.state.obs_port = NoOpObs()
    # Media stub registered for later enrich — never wired into generate.
    application.state.media_provider = StubMediaProvider()
    application.state.geo_gateway = NominatimAdapter(
        base_url=settings.nominatim_base_url,
        user_agent=settings.nominatim_user_agent,
        timeout_seconds=settings.nominatim_timeout_seconds,
    )
    application.state.geo_service = GeoService(application.state.geo_gateway)
    application.state.places_facade = DefaultPlacesFacade(
        overpass=OverpassAdapter(
            base_url=settings.overpass_base_url,
            timeout_seconds=settings.overpass_timeout_seconds,
            user_agent=settings.places_user_agent,
        ),
        otm=OtmAdapter(
            base_url=settings.otm_base_url,
            api_key=settings.otm_api_key,
            timeout_seconds=settings.otm_timeout_seconds,
            user_agent=settings.places_user_agent,
        ),
    )
    if settings.catalog_enqueue_inline:
        application.state.acquire_queue = InlineAcquireQueue()
    else:
        application.state.acquire_queue = ArqAcquireQueue(settings.redis_url)

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
    application.state.travel_engine = GreedyTravelEngine()
    application.state.settings = settings
    # deps_factory is bound per-request in the generate/revise routers (DB session scoped).
    application.state.generate_runner = InProcessGenerateRunner(
        deps_factory=lambda _session_id: (_ for _ in ()).throw(
            RuntimeError("generate deps_factory not bound")
        ),
        timeout_seconds=settings.generate_timeout_seconds,
        revise_timeout_seconds=settings.revise_timeout_seconds,
        max_revise_loops=settings.revise_max_loops,
    )
    application.include_router(health_router)
    application.include_router(sessions_router)
    application.include_router(catalog_router)
    application.include_router(generate_router)
    application.include_router(revise_router)
    application.include_router(trips_router)
    return application


app = create_app()
