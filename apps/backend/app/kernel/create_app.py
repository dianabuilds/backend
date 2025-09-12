from __future__ import annotations

import logging
from pathlib import Path

import fastapi
import punq
import sqlalchemy
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from packaging import version
from starlette.middleware.gzip import GZipMiddleware

# Prefer ultra-fast orjson if available; gracefully fall back to std JSONResponse
try:  # pragma: no cover - optional dependency
    from fastapi.responses import ORJSONResponse as DefaultJSONResponse
except Exception:  # orjson not installed
    from fastapi.responses import JSONResponse as DefaultJSONResponse

logger = logging.getLogger(__name__)


def bootstrap_env_and_logging() -> None:
    """Load environment and configure logging once at process start."""
    from app.kernel.env import load_dotenv
    from app.kernel.logging import configure_logging

    load_dotenv()
    configure_logging()


def _instrument_observability(app: FastAPI) -> None:
    """Best‑effort OpenTelemetry instrumentation if available."""
    try:  # pragma: no cover - optional OTEL dependencies
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        try:
            # support both possible config locations
            from config.opentelemetry import setup_otel  # type: ignore
        except Exception:  # pragma: no cover
            setup_otel = None  # type: ignore

        if setup_otel is not None:
            setup_otel()
        FastAPIInstrumentor.instrument_app(app)
        from app.providers.db.session import get_engine

        SQLAlchemyInstrumentor().instrument(engine=get_engine().sync_engine)
        RequestsInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
    except Exception as e:  # pragma: no cover - optional
        logging.getLogger(__name__).warning("Observability instrumentation failed: %s", e)


def _mount_admin_assets(app: FastAPI) -> None:
    from app.kernel.web.immutable_static import ImmutableStaticFiles

    dist_dir = Path(__file__).resolve().parent.parent.parent / "admin" / "dist"
    dist_assets_dir = dist_dir / "assets"
    if dist_assets_dir.exists():
        app.mount("/admin/assets", ImmutableStaticFiles(directory=dist_assets_dir), name="admin-assets")


def _mount_uploads(app: FastAPI, settings) -> None:
    from app.kernel.web.immutable_static import ImmutableStaticFiles
    from app.kernel.web.header_injector import HeaderInjector

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    uploads_static = ImmutableStaticFiles(directory=uploads_dir)
    _uploads_cors = {
        **settings.effective_origins(),
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": settings.cors_allow_methods,
        "allow_headers": settings.cors_allow_headers,
        "expose_headers": settings.cors_expose_headers,
        "max_age": settings.cors_max_age,
    }
    uploads_static = CORSMiddleware(uploads_static, **_uploads_cors)
    uploads_static = HeaderInjector(uploads_static, {"Cross-Origin-Resource-Policy": "cross-origin"})
    app.mount("/static/uploads", uploads_static, name="uploads")


def _register_admin_spa(app: FastAPI) -> None:
    # Fallback middleware for HTML navigations under /admin
    @app.middleware("http")
    async def admin_spa_fallback(request: Request, call_next):  # type: ignore[override]
        if request.method == "GET":
            path = request.url.path
            if path.startswith("/admin") and not path.startswith("/admin/assets"):
                accept = request.headers.get("accept", "")
                if "text/html" in accept.lower():
                    from app.domains.admin.web.admin_spa import serve_admin_app

                    return await serve_admin_app(request)
        return await call_next(request)

    try:
        from app.domains.admin.web.admin_spa import router as admin_spa_router

        app.include_router(admin_spa_router)
    except Exception as e:  # pragma: no cover
        logger.warning("Admin SPA router registration failed: %s", e)


def _register_common_routers(app: FastAPI, settings) -> None:
    # System domain operational routers
    from app.kernel.api.health import router as health_router
    from app.kernel.api.ops import audit_router
    from app.kernel.api.ops import router as ops_router

    if settings.observability.health_enabled:
        app.include_router(health_router)
    app.include_router(ops_router)
    app.include_router(audit_router)


def _register_domain_routers(app: FastAPI, settings, container=None) -> None:
    from app.domains.registry import register_domains
    from app.kernel.events.bus import get_event_bus

    if settings.env_mode.name == "test":
        from app.domains.auth.api.routers import router as auth_router

        app.include_router(auth_router)
        return
    try:
        # Optional telemetry routers
        from app.domains.telemetry.api.metrics_router import router as metrics_router
        from app.domains.telemetry.api.rum_metrics_router import (
            admin_router as rum_admin_router,
        )
        from app.domains.telemetry.api.rum_metrics_router import router as rum_metrics_router

        app.include_router(metrics_router)
        app.include_router(rum_metrics_router)
        app.include_router(rum_admin_router)
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).warning(
            "Telemetry routers failed to load completely: %s", e
        )

    try:
        bus = get_event_bus()
        register_domains(app, container=container, settings=settings, bus=bus)
    except Exception as exc:  # pragma: no cover - optional domains
        logging.getLogger(__name__).warning("Domain router registration failed: %s", exc)

    # Admin overrides last
    try:
        from app.domains.admin.api.override import register_admin_override

        register_admin_override(app)
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).warning("Admin override failed: %s", exc)


def _register_middlewares(app: FastAPI, settings) -> None:
    from app.kernel.middlewares.body_limit import BodySizeLimitMiddleware
    from app.kernel.middlewares.cookies_security_middleware import (
        CookiesSecurityMiddleware,
    )
    from app.kernel.middlewares.csrf import CSRFMiddleware
    from app.kernel.exception_handlers import register_exception_handlers
    from app.kernel.middlewares.logging_middleware import RequestLoggingMiddleware
    from app.domains.telemetry.metrics_middleware import MetricsMiddleware
    from app.kernel.middlewares.rate_limit import RateLimitMiddleware
    from app.kernel.middlewares.real_ip import RealIPMiddleware
    from app.kernel.middlewares.request_id import RequestIDMiddleware
    from app.kernel.middlewares.security_headers import SecurityHeadersMiddleware
    from app.kernel.config import EnvMode

    # Compression and body size limit
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(BodySizeLimitMiddleware)

    # Core middlewares
    app.add_middleware(RequestIDMiddleware)
    if settings.logging.requests:
        app.add_middleware(RequestLoggingMiddleware)

    enable_tracing = settings.env_mode in {EnvMode.staging, EnvMode.production}
    enable_metrics = enable_tracing and settings.observability.metrics_enabled
    if enable_metrics:
        app.add_middleware(MetricsMiddleware)

    # CORS
    _cors_kwargs = {
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": settings.cors_allow_methods,
        "allow_headers": settings.cors_allow_headers,
        "expose_headers": settings.cors_expose_headers,
        "max_age": settings.cors_max_age,
    }
    _effective = settings.effective_origins()
    _cors_kwargs.update(_effective)
    if settings.env_mode.name in {"development", "test"}:
        _cors_kwargs["allow_headers"] = ["*"]
    app.add_middleware(CORSMiddleware, **_cors_kwargs)

    if settings.rate_limit.enabled:
        app.add_middleware(
            RateLimitMiddleware,
            capacity=10,
            fill_rate=1,
            burst=5,
        )

    # Security
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CookiesSecurityMiddleware)

    _allowed_hosts = settings.security.allowed_hosts
    if not _allowed_hosts and settings.env_mode is EnvMode.production:
        _allowed_hosts = ["localhost"]
    if _allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)
    app.add_middleware(RealIPMiddleware)

    register_exception_handlers(app)


def _register_lifecycle(app: FastAPI, settings) -> None:
    from app.kernel.config import EnvMode
    from app.kernel.rng import init_rng
    from app.domains.ai.embedding_config import configure_from_settings
    # ensure_default_admin will be resolved dynamically
    from app.kernel.events.bus import register_handlers
    from app.providers.db.session import (
        check_database_connection,
        close_db_connection,
        init_db,
    )

    seed = init_rng(settings.rng_seed_strategy)
    logger.info("RNG seed initialised to %s", seed)

        @app.on_event("startup")
    async def startup_event():  # pragma: no cover - integration
        logger.info("Starting application in %s environment", settings.env_mode)
        configure_from_settings()
        register_handlers()

        # Resolve ensure_default_admin dynamically from auth domain if available
        async def _ensure_default_admin():
            try:
                from app.domains.auth.application.services.bootstrap import ensure_default_admin as _impl  # type: ignore
                await _impl()
            except Exception as e:
                logger.warning("ensure_default_admin not available: %s", e)

        if settings.env_mode == EnvMode.test:
            logger.info("Test environment detected, skipping database initialization")
        elif await check_database_connection():
            logger.info("Database connection successful")
            await init_db()
            try:
                await _ensure_default_admin()
            except Exception as e:
                logger.warning("Admin bootstrap failed: %s", e)
        else:
            logger.error("Failed to connect to database during startup")

    @app.on_event("shutdown")
    async def shutdown_event():  # pragma: no cover - integration
        logger.info("Shutting down application")
        await close_db_connection()
def create_app(settings) -> FastAPI:
    """Create and configure FastAPI app (kernel loader)."""
    # Log framework versions and enforce minimum requirements
    logger.info("Using FastAPI %s, SQLAlchemy %s", fastapi.__version__, sqlalchemy.__version__)
    fastapi_version = version.parse(fastapi.__version__)
    sqlalchemy_version = version.parse(sqlalchemy.__version__)
    if fastapi_version < version.parse("0.116"):
        raise RuntimeError("FastAPI >= 0.116 required")
    if sqlalchemy_version.major != 2:
        raise RuntimeError("SQLAlchemy 2.x required")

    # DI container
    container = punq.Container()
    from app.providers import register_providers

    register_providers(container, settings)

    # App
    app = FastAPI(default_response_class=DefaultJSONResponse)
    app.state.container = container
    # Attach template renderer service (optional dependency on jinja2)
    try:
        from app.kernel.templates import TemplateService

        app.state.templates = TemplateService()
    except Exception:
        app.state.templates = None  # type: ignore[assignment]

    # Optional OTEL/metrics instrumentation
    from app.kernel.config import EnvMode

    if settings.env_mode in {EnvMode.staging, EnvMode.production} and settings.observability.tracing_enabled:
        _instrument_observability(app)

    # Middlewares and exception handlers
    _register_middlewares(app, settings)

    # Static mounts
    _mount_admin_assets(app)
    _mount_uploads(app, settings)

    # Routers
    _register_common_routers(app, settings)
    _register_domain_routers(app, settings, container)

    # SPA fallback (should be last)
    _register_admin_spa(app)

    # Lifecycle hooks
    _register_lifecycle(app, settings)

    # Convenience root redirect for HTML
    @app.get("/")
    async def _root(request: Request):  # type: ignore[override]
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            return HTMLResponse("<meta http-equiv='refresh' content='0; url=/admin'>")
        return {"ok": True}

    return app


__all__ = ["bootstrap_env_and_logging", "create_app"]






