from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request

try:
    from prometheus_client import Counter, Histogram  # type: ignore
except Exception:  # pragma: no cover
    Counter = Histogram = None  # type: ignore


HTTP_REQUESTS: Any | None = None
HTTP_REQUEST_DURATION: Any | None = None


def _ensure_metrics():
    global HTTP_REQUESTS, HTTP_REQUEST_DURATION
    if HTTP_REQUESTS is not None and HTTP_REQUEST_DURATION is not None:
        return
    if Counter is None or Histogram is None:
        return
    # Cardinality guard: use route path templates as labels
    HTTP_REQUESTS = Counter(
        "http_requests_total",
        "Total HTTP requests",
        labelnames=("method", "path", "status"),
    )
    # Milliseconds histogram with sensible web buckets
    HTTP_REQUEST_DURATION = Histogram(
        "http_request_duration_ms",
        "HTTP request duration in milliseconds",
        labelnames=("method", "path"),
        buckets=(1, 2, 5, 10, 20, 50, 100, 200, 300, 500, 750, 1000, 2000, 5000),
    )


def _route_template(request: Request) -> str:
    try:
        r = request.scope.get("route")
        # FastAPI has .path; Starlette has .path_format in recent versions
        return getattr(r, "path", None) or getattr(r, "path_format", None) or request.url.path
    except Exception:
        return request.url.path


def setup_http_metrics(app: FastAPI) -> None:
    _ensure_metrics()
    if Counter is None or Histogram is None:
        return

    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next: Callable):  # type: ignore[override]
        method = request.method
        path = _route_template(request)
        t0 = time.perf_counter()
        status = "500"
        try:
            response = await call_next(request)
            status = str(getattr(response, "status_code", 200))
            return response
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            counter = HTTP_REQUESTS
            duration = HTTP_REQUEST_DURATION
            if counter is not None and duration is not None:
                try:
                    counter.labels(method=method, path=path, status=status).inc()
                    duration.labels(method=method, path=path).observe(dt_ms)
                except Exception:
                    pass


__all__ = ["setup_http_metrics"]
