from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Callable

import pytest
import requests

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))
from app.domains.ai.application.embedding_service import reduce_vector_dim  # noqa: E402
from app.domains.ai.embedding_config import (  # noqa: E402
    _make_cohere_provider,
    _make_hf_provider,
    _make_openai_provider,
    _simple_embedding,
)


class _FailResponse(requests.Response):
    def __init__(self, status: int) -> None:
        super().__init__()
        self.status_code = status


@pytest.mark.parametrize(
    "factory,kwargs",
    [
        (
            _make_openai_provider,
            {"api_base": "", "api_key": "k", "model": "m", "target_dim": 10},
        ),
        (
            _make_cohere_provider,
            {"api_base": "", "api_key": "k", "model": "m", "target_dim": 10},
        ),
        (
            _make_hf_provider,
            {"api_base": "", "api_key": "k", "model": "m", "target_dim": 10},
        ),
    ],
)  # type: ignore[misc]
@pytest.mark.parametrize("status", [405, 422, 500])  # type: ignore[misc]
def test_http_error_falls_back_to_simple(
    factory: Callable[..., Callable[[str], list[float]]],
    kwargs: dict[str, object],
    status: int,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fake_post(*_args: object, **_kw: object) -> _FailResponse:
        return _FailResponse(status)

    monkeypatch.setattr(requests, "post", fake_post)

    provider = factory(**kwargs)
    target_dim = kwargs["target_dim"]
    text = "hello world"
    expected = _simple_embedding(text)
    if len(expected) != target_dim:
        expected = reduce_vector_dim(expected, target_dim)

    with caplog.at_level(logging.ERROR):
        result = provider(text)
    assert result == expected  # nosec B101
    assert str(status) in caplog.text  # nosec B101
