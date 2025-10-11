from __future__ import annotations

from datetime import datetime

import pytest

from domains.product.navigation.api import support


def test_isoformat_normalizes_naive_datetime():
    dt = datetime(2025, 10, 11, 12, 30, 45)

    result = support.isoformat(dt)

    assert result == "2025-10-11T12:30:45Z"


def test_isoformat_passthrough_and_invalid():
    assert support.isoformat("2025-10-10T00:00:00Z") == "2025-10-10T00:00:00Z"
    assert support.isoformat(None) is None
    assert support.isoformat("not-a-date") == "not-a-date"
    assert support.isoformat(123) is None


@pytest.mark.parametrize(
    "input_key,expected",
    [
        ("Fts", "embedding"),
        ("  mix  ", "explore"),
        ("", "tags"),
        ("custom", "custom"),
    ],
)
def test_normalize_algo_key_handles_aliases(input_key, expected):
    assert support.normalize_algo_key(input_key) == expected


@pytest.mark.parametrize(
    "key,expected",
    [
        ("tags", ["tags"]),
        ("embedding", ["embedding", "fts", "semantic", "vector"]),
        ("unknown", ["unknown"]),
    ],
)
def test_algo_sources_returns_configured_aliases(key, expected):
    assert support.algo_sources(key) == expected


@pytest.mark.parametrize(
    "value,default,expected",
    [
        ("10", None, 10),
        (None, 5, 5),
        ("oops", 3, 3),
    ],
)
def test_coerce_int_handles_invalid_inputs(value, default, expected):
    assert support.coerce_int(value, default=default) == expected
