from src.modules.evals import EvalRunner


def test_eval_runner_smoke() -> None:
    EvalRunner().run_smoke()
