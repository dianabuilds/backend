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

# Prefer ultra-fast orjson if available; gracefully fall back to std JSONResponse
try:  # pragma: no cover - optional dependency
    from fastapi.responses import ORJSONResponse as DefaultJSONResponse
except Exception:  # orjson not installed
    from fastapi.responses import JSONResponse as DefaultJSONResponse
from packaging import version
from starlette.middleware.gzip import GZipMiddleware

from app.core.env_loader import load_dotenv
from app.core.logging_configuration import configure_logging
from app.core.rng import init_rng

try:  # pragma: no cover - optional OTEL dependencies
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    from config.opentelemetry import setup_otel
except ModuleNotFoundError:  # pragma: no cover
    setup_otel = None  # type: ignore[assignment, misc]
    FastAPIInstrumentor = HTTPXClientInstrumentor = None  # type: ignore[assignment, misc]
    RequestsInstrumentor = SQLAlchemyInstrumentor = None  # type: ignore[assignment, misc]

from app.api.admin_override import register_admin_override
from app.api.health import router as health_router
from app.api.ops import audit_router
from app.api.ops import router as ops_router
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
from app.domains.system.bootstrap import ensure_default_admin
from app.domains.system.events import register_handlers
from app.providers import register_providers
from app.providers.db.session import (
    check_database_connection,
    close_db_connection,
    get_engine,
    init_db,
)
from app.security import auth_user
from app.web.header_injector import HeaderInjector
from app.web.immutable_static import ImmutableStaticFiles

load_dotenv()
configure_logging()

settings: Settings = get_settings()

# Initialize RNG based on configuration
_rng_seed = init_rng(settings.rng_seed_strategy)

# Используем базовое логирование из uvicorn/стандартного logging
logger = logging.getLogger(__name__)
logger.info("RNG seed initialised to %s", _rng_seed)

# Log framework versions and enforce minimum requirements
logger.info("Using FastAPI %s, SQLAlchemy %s", fastapi.__version__, sqlalchemy.__version__)
fastapi_version = version.parse(fastapi.__version__)
sqlalchemy_version = version.parse(sqlalchemy.__version__)
if fastapi_version < version.parse("0.116"):
    raise RuntimeError("FastAPI >= 0.116 required")
if sqlalchemy_version.major != 2:
    raise RuntimeError("SQLAlchemy 2.x required")

container = punq.Container()
register_providers(container, settings)

app = FastAPI(default_response_class=DefaultJSONResponse)
app.state.container = container
enable_tracing = settings.env_mode in {
    EnvMode.staging,
    EnvMode.production,
}
enable_metrics = enable_tracing and settings.observability.metrics_enabled
if enable_tracing:
    if 'setup_otel' in globals() and setup_otel is not None:
        setup_otel()
    if 'FastAPIInstrumentor' in globals() and FastAPIInstrumentor is not None:
        FastAPIInstrumentor.instrument_app(app)
    if 'SQLAlchemyInstrumentor' in globals() and SQLAlchemyInstrumentor is not None:
        SQLAlchemyInstrumentor().instrument(engine=get_engine().sync_engine)
    if 'RequestsInstrumentor' in globals() and RequestsInstrumentor is not None:
        RequestsInstrumentor().instrument()
    if 'HTTPXClientInstrumentor' in globals() and HTTPXClientInstrumentor is not None:
        HTTPXClientInstrumentor().instrument()
# Сжатие ответов
app.add_middleware(GZipMiddleware, minimum_size=1024)
# Лимит размера тела запросов
app.add_middleware(BodySizeLimitMiddleware)
# Базовые middlewares
# Корреляция по запросам
app.add_middleware(RequestIDMiddleware)
if settings.logging.requests:
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
from app.core.settings import EnvMode as _EnvMode  # local import to avoid cycles

if settings.env_mode in {_EnvMode.development, _EnvMode.test}:
    _cors_kwargs["allow_headers"] = ["*"]
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

_allowed_hosts = settings.security.allowed_hosts
if not _allowed_hosts and settings.env_mode is EnvMode.production:
    _allowed_hosts = ["localhost"]
if _allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)
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
if DIST_ASSETS_DIR.exists():
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
uploads_static = HeaderInjector(uploads_static, {"Cross-Origin-Resource-Policy": "cross-origin"})
app.mount("/static/uploads", uploads_static, name="uploads")

if settings.observability.health_enabled:
    app.include_router(health_router)
app.include_router(ops_router)
app.include_router(audit_router)

if settings.env_mode == EnvMode.test:
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
        logging.getLogger(__name__).warning(f"Telemetry routers failed to load completely: {e}")

    # Domain routers (auth, etc.)
    try:
        register_domain_routers(app)
    except Exception as exc:  # pragma: no cover - optional domains
        logging.getLogger(__name__).warning("Domain router registration failed: %s", exc)

    # Removed fallback /users/me: domain routers must provide it or app should fail earlier.
    register_admin_override(app)

    # SPA fallback should be last
    from app.web.admin_spa import router as admin_spa_router

    app.include_router(admin_spa_router)


@app.get("/")
async def read_root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        return HTMLResponse("<meta http-equiv='refresh' content='0; url=/admin'>")

@app.get("/users/me")
async def users_me(current=fastapi.Depends(auth_user)):
    try:
        return {
            "id": str(getattr(current, "id", "")),
            "username": getattr(current, "username", None),
            "role": getattr(current, "role", None),
            "email": getattr(current, "email", None),
        }
    except Exception:
        return {"id": None}


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
    else:
        logger.error("Failed to connect to database during startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Выполняется при остановке приложения"""
    logger.info("Shutting down application")
    await close_db_connection()


