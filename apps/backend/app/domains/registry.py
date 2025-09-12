from __future__ import annotations

import logging

from fastapi import FastAPI

from app.domains.domain_config import DOMAIN_CONFIGS, DomainConfig

logger = logging.getLogger(__name__)


def _resolve_load_order(configs: list[DomainConfig]) -> list[DomainConfig]:
    """Topologically sort domains based on depends_on.

    If a cycle or missing dependency is detected, fall back to declared order
    and log a warning, but do not crash.
    """
    # Build adjacency lists
    graph: dict[str, set[str]] = {c.name: set(c.depends_on or []) for c in configs}
    by_name: dict[str, DomainConfig] = {c.name: c for c in configs}

    # Ignore unknown dependencies
    for n, deps in graph.items():
        graph[n] = {d for d in deps if d in by_name and d != n}

    indeg: dict[str, int] = {n: 0 for n in graph}
    for deps in graph.values():
        for d in deps:
            indeg[d] += 1

    queue = [n for n, deg in indeg.items() if deg == 0]
    order: list[str] = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m, deps in graph.items():
            if n in deps:
                deps.remove(n)
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)

    if len(order) != len(graph):
        logger.warning("Domain dependency cycle or missing deps detected; using declared order")
        return configs
    return [by_name[n] for n in order]


def register_domains(app: FastAPI, container=None, settings=None, bus=None) -> None:
    """Initialize domains: inits, providers, routers (and optionally events).

    - Respects feature flags and declared dependencies
    - Registers DI providers if `container` and `settings` are provided
    - Registers event handlers if `bus` is provided
    """
    # Load feature flags (support both execution contexts)
    try:  # pragma: no cover - environment dependent import path
        from config.feature_flags import feature_flags  # type: ignore
    except Exception:  # pragma: no cover
        from apps.backend.config.feature_flags import feature_flags  # type: ignore

    for dc in _resolve_load_order(DOMAIN_CONFIGS):
        if not dc.is_enabled(feature_flags):
            logger.info("Domain '%s' disabled by feature flag '%s'", dc.name, dc.feature_flag)
            continue
        try:
            dc.run_inits()
        except Exception as exc:  # pragma: no cover - init failures are rare
            logger.exception("Domain '%s' init failed", dc.name)
            raise RuntimeError(f"Failed to init domain {dc.name}") from exc

        # Register DI providers per domain when available
        if container is not None and settings is not None:
            try:
                dc.register_providers(container, settings)
            except Exception as exc:  # pragma: no cover - optional per-domain
                logger.exception("Domain '%s' provider registration failed", dc.name)
                raise RuntimeError(
                    f"Failed to register providers for domain {dc.name}"
                ) from exc

        # Register domain events when a bus is provided
        if bus is not None and getattr(dc, "events", None):
            try:
                dc.register_event_handlers(bus)
            except Exception as exc:  # pragma: no cover - optional
                logger.exception("Domain '%s' event registration failed", dc.name)
                raise RuntimeError(
                    f"Failed to register events for domain {dc.name}"
                ) from exc

        for router in dc.load_routers():
            try:
                app.include_router(router)
            except Exception as exc:
                logger.exception(
                    "Failed to load router for domain '%s' (%s)",
                    dc.name,
                    getattr(router, "__module__", "<unknown>"),
                )
                raise RuntimeError(f"Failed to load router for domain {dc.name}") from exc


def register_domain_routers(app: FastAPI) -> None:
    """Backward-compatible wrapper to include routers only.

    New code should call `register_domains` from the kernel to also wire
    providers/events with proper load order.
    """
    register_domains(app)
