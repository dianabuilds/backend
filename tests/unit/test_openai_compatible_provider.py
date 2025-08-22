from app.domains.ai.pipeline_impl import _build_fallback_chain
from app.domains.ai.providers import OpenAICompatibleProvider


def test_build_chain_with_openai_compatible():
    providers = _build_fallback_chain("openai_compatible")
    assert isinstance(providers[0], OpenAICompatibleProvider)
    names = {p.name for p in providers}
    assert {
        "openai_compatible",
        "openai",
        "anthropic",
    } <= names
