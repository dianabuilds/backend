from __future__ import annotations

from app.core.metrics import metrics_storage


def setup_function() -> None:
    metrics_storage.reset()


def test_summary_filters_by_workspace_id() -> None:
    metrics_storage.record(100, 200, "GET", "/foo", "ws1")
    metrics_storage.record(100, 500, "GET", "/foo", "ws2")
    summary = metrics_storage.summary(3600, workspace_id="ws1")
    assert summary["count"] == 1
    assert summary["error_count"] == 0


def test_timeseries_filters_by_workspace_id() -> None:
    metrics_storage.record(100, 200, "GET", "/a", "ws1")
    metrics_storage.record(100, 200, "GET", "/a", "ws2")
    data = metrics_storage.timeseries(3600, 60, workspace_id="ws1")
    series_2xx = next(s for s in data["series"] if s["name"] == "2xx")
    assert series_2xx["points"][0]["value"] == 1


def test_top_endpoints_filters_by_workspace_id() -> None:
    metrics_storage.record(100, 200, "GET", "/ws1", "ws1")
    metrics_storage.record(100, 200, "GET", "/ws2", "ws2")
    top = metrics_storage.top_endpoints(3600, 10, "rps", workspace_id="ws1")
    assert len(top) == 1
    assert top[0]["route"] == "/ws1"


def test_recent_errors_filters_by_workspace_id() -> None:
    metrics_storage.record(100, 404, "GET", "/err1", "ws1")
    metrics_storage.record(100, 404, "GET", "/err2", "ws2")
    errors = metrics_storage.recent_errors(10, workspace_id="ws1")
    assert len(errors) == 1
    assert errors[0]["route"] == "/err1"
