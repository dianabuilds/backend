import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.domains.ai.pipeline_impl import _build_fallback_chain
from apps.backend.app.domains.ai.providers import OpenAICompatibleProvider


def test_build_chain_with_openai_compatible():
    providers = _build_fallback_chain("openai_compatible")
    assert providers[0].__class__.__name__ == OpenAICompatibleProvider.__name__
    names = {p.name for p in providers}
    assert {
        "openai_compatible",
        "openai",
        "anthropic",
    } <= names
