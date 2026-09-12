import pytest
from fastapi.testclient import TestClient

from src.db.session import ping_db
from src.main import create_app


def _client(*, db_ok: bool) -> TestClient:
    application = create_app()

    async def _override_ping() -> bool:
        return db_ok

    application.dependency_overrides[ping_db] = _override_ping
    return TestClient(application)


def test_liveness_ok_when_db_down() -> None:
    response = _client(db_ok=False).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "db" not in response.json()


def test_liveness_ok_without_vendor_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    response = _client(db_ok=False).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_ok_when_db_up() -> None:
    response = _client(db_ok=True).get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}


def test_ready_degraded_when_db_down() -> None:
    response = _client(db_ok=False).get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "db": False}


@pytest.mark.asyncio
async def test_ready_live_database() -> None:
    reachable = await ping_db()
    if not reachable:
        pytest.skip("PostGIS not reachable (optional locally; required in CI)")
    response = TestClient(create_app()).get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": True}


def test_sessions_is_not_a_product_route() -> None:
    response = _client(db_ok=True).post("/api/v1/sessions")
    assert response.status_code in {404, 405}
    body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    assert "session_id" not in body


def test_generate_is_not_a_product_route() -> None:
    response = _client(db_ok=True).post("/api/v1/sessions/demo/generate")
    assert response.status_code in {404, 405}


def test_no_guideagent_paths() -> None:
    paths = [getattr(route, "path", "") for route in create_app().routes]
    assert all("guideagent" not in path.lower() for path in paths)
