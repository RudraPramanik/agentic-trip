import importlib

import pytest

FEATURE_MODULES = [
    "src.modules.chat",
    "src.modules.geo",
    "src.modules.catalog",
    "src.modules.planner",
    "src.modules.trips",
    "src.modules.explore",
    "src.modules.media",
    "src.modules.booking",
    "src.modules.llm",
    "src.modules.agents",
    "src.modules.auth",
    "src.modules.monitor",
    "src.modules.evals",
]


@pytest.mark.parametrize("module_name", FEATURE_MODULES)
def test_feature_module_imports_without_network(module_name: str) -> None:
    importlib.import_module(module_name)
