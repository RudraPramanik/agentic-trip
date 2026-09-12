from src.modules.monitor import NoOpObs


def test_noop_obs_does_not_raise() -> None:
    obs = NoOpObs()
    with obs.start_trace("boot"):
        with obs.span("work"):
            with obs.generation("unused"):
                pass
