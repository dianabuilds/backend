from __future__ import annotations

# ruff: noqa: E402
from app.core.env_loader import load_dotenv

# Ensure environment variables from .env are loaded before importing modules
# that access them (e.g. logging configuration or settings).
load_dotenv()

from app.core.logging_configuration import configure_logging

configure_logging()

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.gzip import GZipMiddleware

from app.core.policy import policy
from app.core.rng import init_rng

if policy.allow_write:
    try:  # pragma: no cover - optional OTEL dependencies
        from config.opentelemetry import setup_otel
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    except ModuleNotFoundError:  # pragma: no cover
        setup_otel = None  # type: ignore[assignment]
        FastAPIInstrumentor = HTTPXClientInstrumentor = None  # type: ignore[assignment]
        RequestsInstrumentor = SQLAlchemyInstrumentor = None  # type: ignore[assignment]
import punq

from app.core.body_limit import BodySizeLimitMiddleware
from app.core.config import Settings, get_settings
from app.core.cookies_security_middleware import CookiesSecurityMiddleware
from app.core.csrf import CSRFMiddleware
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.metrics_middleware import MetricsMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.core.real_ip import RealIPMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.settings import EnvMode
from app.domains.ai.embedding_config import configure_from_settings
from app.domains.registry import register_domain_routers
from app.domains.system.bootstrap import ensure_default_admin, ensure_global_workspace
from app.domains.system.events import register_handlers
from app.providers import register_providers
from app.providers.db.session import (
    check_database_connection,
    close_db_connection,
    get_engine,
    init_db,
)
from app.web.immutable_static import ImmutableStaticFiles

settings: Settings = get_settings()

# Initialize RNG based on configuration
_rng_seed = init_rng(settings.rng_seed_strategy)

# Используем базовое логирование из uvicorn/стандартного logging
logger = logging.getLogger(__name__)
logger.info("RNG seed initialised to %s", _rng_seed)

container = punq.Container()
register_providers(container, settings)

app = FastAPI()
app.state.container = container
enable_tracing = settings.env_mode in {
    EnvMode.staging,
    EnvMode.production,
}
enable_metrics = enable_tracing and settings.observability.metrics_enabled
if policy.allow_write and setup_otel and enable_tracing:
    setup_otel()
    if FastAPIInstrumentor:
        FastAPIInstrumentor.instrument_app(app)
    if SQLAlchemyInstrumentor:
        SQLAlchemyInstrumentor().instrument(engine=get_engine().sync_engine)
    if RequestsInstrumentor:
        RequestsInstrumentor().instrument()
    if HTTPXClientInstrumentor:
        HTTPXClientInstrumentor().instrument()
# Сжатие ответов
app.add_middleware(GZipMiddleware, minimum_size=1024)
# Лимит размера тела запросов
app.add_middleware(BodySizeLimitMiddleware)
# Базовые middlewares
# Корреляция по запросам
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
if enable_metrics:
    app.add_middleware(MetricsMiddleware)
# CORS configuration
# В dev, если явные origin'ы не заданы, используем безопасный фолбэк (regex) из настроек
_cors_kwargs = {
    "allow_credentials": settings.cors_allow_credentials,
    "allow_methods": settings.cors_allow_methods,
    "allow_headers": settings.cors_allow_headers,
    "expose_headers": settings.cors_expose_headers,
    "max_age": settings.cors_max_age,
}
_effective = settings.effective_origins()
_cors_kwargs.update(_effective)
app.add_middleware(CORSMiddleware, **_cors_kwargs)
if settings.rate_limit.enabled:
    app.add_middleware(
        RateLimitMiddleware,
        capacity=10,
        fill_rate=1,
        burst=5,
    )
# CSRF для мутаций
app.add_middleware(CSRFMiddleware)
# Заголовки безопасности и CSP
app.add_middleware(SecurityHeadersMiddleware)
# Усиление Set-Cookie флагов
app.add_middleware(CookiesSecurityMiddleware)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=settings.security.allowed_hosts or ["*"]
)
app.add_middleware(RealIPMiddleware)
register_exception_handlers(app)


@app.middleware("http")
async def admin_spa_fallback(request: Request, call_next):
    """Serve Admin SPA for direct browser navigations to /admin paths.

    This middleware intercepts HTML navigation requests (including browser
    refreshes) that target /admin routes which may otherwise be handled by API
    routers. By short‑circuiting such requests and returning the SPA index, we
    avoid slow API handlers and blank pages when reloading deep links.
    """

    if request.method == "GET":
        path = request.url.path
        if path.startswith("/admin") and not path.startswith("/admin/assets"):
            accept = request.headers.get("accept", "")
            if "text/html" in accept.lower():
                from app.web.admin_spa import serve_admin_app

                return await serve_admin_app(request)
    return await call_next(request)


DIST_DIR = Path(__file__).resolve().parent.parent.parent / "admin" / "dist"
DIST_ASSETS_DIR = DIST_DIR / "assets"
if policy.allow_write and DIST_ASSETS_DIR.exists():
    # serve built frontend assets (js, css, etc.) with correct MIME types
    app.mount(
        "/admin/assets",
        ImmutableStaticFiles(directory=DIST_ASSETS_DIR),
        name="admin-assets",
    )

# Serve uploaded media files with CORS so that editors on other origins can access them
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Static file app for uploads with long-lived caching
uploads_static = ImmutableStaticFiles(directory=UPLOADS_DIR)
# Wrap with CORS middleware because mounted apps bypass the main app middlewares
_uploads_cors = {
    **settings.effective_origins(),
    "allow_credentials": settings.cors_allow_credentials,
    "allow_methods": settings.cors_allow_methods,
    "allow_headers": settings.cors_allow_headers,
    "expose_headers": settings.cors_expose_headers,
    "max_age": settings.cors_max_age,
}
uploads_static = CORSMiddleware(uploads_static, **_uploads_cors)
# Inject CORP so admin can load images cross-origin
from app.web.header_injector import HeaderInjector

uploads_static = HeaderInjector(
    uploads_static, {"Cross-Origin-Resource-Policy": "cross-origin"}
)
app.mount("/static/uploads", uploads_static, name="uploads")

from app.api.health import router as health_router  # noqa: E402
from app.api.ops import router as ops_router  # noqa: E402

if settings.observability.health_enabled:
    app.include_router(health_router)
app.include_router(ops_router)

if not policy.allow_write:
    # Minimal routers needed for tests
    from app.domains.auth.api.routers import router as auth_router

    app.include_router(auth_router)
else:
    # Telemetry routers: import inside try to avoid startup failures
    try:
        from app.domains.telemetry.api.metrics_router import (
            router as metrics_router,
        )
        from app.domains.telemetry.api.rum_metrics_router import (
            admin_router as rum_admin_router,
        )
        from app.domains.telemetry.api.rum_metrics_router import (
            router as rum_metrics_router,
        )

        # app.include_router(tags_router)  # removed: served by domain router
        # app.include_router(quests_router)  # removed: served by domain router
        app.include_router(metrics_router)
        app.include_router(rum_metrics_router)
        app.include_router(rum_admin_router)
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Telemetry routers failed to load completely: {e}"
        )

    # Domain routers (auth, etc.)
    register_domain_routers(app)

    # SPA fallback should be last
    from app.web.admin_spa import router as admin_spa_router

    app.include_router(admin_spa_router)


@app.get("/")
async def read_root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        return HTMLResponse("<meta http-equiv='refresh' content='0; url=/admin'>")
    return {"message": "Hello, World!"}


@app.on_event("startup")
async def startup_event():
    """Выполняется при запуске приложения"""
    logger.info(f"Starting application in {settings.env_mode} environment")

    # Конфигурируем провайдер эмбеддингов из настроек
    configure_from_settings()
    register_handlers()

    # Проверяем подключение к базе данных
    if settings.env_mode == EnvMode.test:
        logger.info("Test environment detected, skipping database initialization")
    elif await check_database_connection():
        logger.info("Database connection successful")
        await init_db()
        # Создаём/чиним дефолтного администратора (для dev)
        try:
            await ensure_default_admin()
        except Exception as e:
            logger.warning(f"Admin bootstrap failed: {e}")
        # Глобальное рабочее пространство для доверенной группы
        try:
            await ensure_global_workspace()
        except Exception as e:
            logger.warning(f"Global workspace bootstrap failed: {e}")
    else:
        logger.error("Failed to connect to database during startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Выполняется при остановке приложения"""
    logger.info("Shutting down application")
    await close_db_connection()
