"""OpenTelemetry instrumentation helpers.

The project treats OpenTelemetry as an optional dependency.  In production
environments the required packages are usually installed, but during local
development or in minimal test setups they might be missing.  Importing the
modules unconditionally would then raise ``ModuleNotFoundError`` and prevent the
application from starting.  To make the instrumentation optional we attempt to
import the modules and fall back to ``None`` if they are unavailable.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence

try:  # pragma: no cover - the happy path is exercised in environments with OTEL
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except ModuleNotFoundError:  # pragma: no cover - executed when OTEL isn't installed
    metrics = trace = OTLPSpanExporter = PrometheusMetricReader = None  # type: ignore[assignment]
    MeterProvider = Resource = TracerProvider = BatchSpanProcessor = None  # type: ignore[assignment]


def _all_present(modules: Iterable[object]) -> bool:
    return all(mod is not None for mod in modules)


def _parse_headers(header_str: str) -> Sequence[tuple[str, str]]:
    return tuple(part.split("=", 1) for part in header_str.split(",") if "=" in part)


def setup_otel(service_name: str = "backend") -> PrometheusMetricReader | None:
    """Configure OpenTelemetry tracing and metrics if the packages are available."""
    required = (
        metrics,
        trace,
        OTLPSpanExporter,
        PrometheusMetricReader,
        MeterProvider,
        Resource,
        TracerProvider,
        BatchSpanProcessor,
    )
    if not _all_present(required):
        return None

    resource = Resource(attributes={"service.name": service_name})

    exporter_kwargs: dict[str, object] = {}
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    if endpoint:
        exporter_kwargs["endpoint"] = endpoint
    headers_env = os.getenv("OTEL_EXPORTER_OTLP_TRACES_HEADERS") or os.getenv(
        "OTEL_EXPORTER_OTLP_HEADERS"
    )
    if headers_env:
        exporter_kwargs["headers"] = _parse_headers(headers_env)

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(**exporter_kwargs))
    )
    trace.set_tracer_provider(tracer_provider)

    reader = PrometheusMetricReader()
    meter_provider = MeterProvider(metric_readers=[reader], resource=resource)
    metrics.set_meter_provider(meter_provider)
    return reader
