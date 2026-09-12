class EvalRunner:
    def run_smoke(self) -> None:
        from src.api import health as health_api

        assert callable(health_api.health)
        assert callable(health_api.ready)
