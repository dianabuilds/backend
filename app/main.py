from app.core.env_loader import load_dotenv
from app.core.logging_configuration import configure_logging

load_dotenv()
configure_logging()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware

TESTING = os.environ.get("TESTING") == "True"

if not TESTING:
    from app.web.immutable_static import ImmutableStaticFiles
from app.core.config import settings
from app.core.config import settings
from app.core.metrics_middleware import MetricsMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.csrf import CSRFMiddleware
from app.core.exception_handlers import register_exception_handlers
from app.core.real_ip import RealIPMiddleware
from app.domains.ai.embedding_config import configure_from_settings
from app.domains.system.events import register_handlers
from app.core.db.session import (
    check_database_connection,
    close_db_connection,
    init_db,
)
from app.domains.system.bootstrap import ensure_default_admin
from app.core.rate_limit import init_rate_limiter, close_rate_limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.cookies_security_middleware import CookiesSecurityMiddleware
from app.core.body_limit import BodySizeLimitMiddleware
from app.domains.registry import register_domain_routers

# Используем базовое логирование из uvicorn/стандартного logging
logger = logging.getLogger(__name__)

app = FastAPI()
# Сжатие ответов
app.add_middleware(GZipMiddleware, minimum_size=1024)
# Лимит размера тела запросов
app.add_middleware(BodySizeLimitMiddleware)
# Базовые middlewares
# Корреляция по запросам
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)
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

# CORS: разрешаем фронту ходить на API в dev
# В dev разрешаем фронт с 5173 (localhost и 127.0.0.1), если явно не настроено
_allowed_origins = (
    settings.cors.allowed_origins
    if settings.cors.allowed_origins
    else (
        [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
            "http://localhost:5176",
            "http://127.0.0.1:5176",
        ]
        if not settings.is_production
        else []
    )
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allowed_methods,
    allow_headers=settings.cors.allowed_headers,
)


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


DIST_DIR = Path(__file__).resolve().parent.parent / "admin-frontend" / "dist"
DIST_ASSETS_DIR = DIST_DIR / "assets"
if not TESTING and DIST_ASSETS_DIR.exists():
    # serve built frontend assets (js, css, etc.) with correct MIME types
    from app.web.immutable_static import ImmutableStaticFiles as _ImmutableStaticFiles

    app.mount(
        "/admin/assets",
        _ImmutableStaticFiles(directory=DIST_ASSETS_DIR),
        name="admin-assets",
    )

# Serve uploaded media files with CORS so that editors on other origins can access them
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Static file app for uploads
uploads_static = StaticFiles(directory=UPLOADS_DIR)
# Wrap with CORS middleware because mounted apps bypass the main app middlewares
uploads_static = CORSMiddleware(
    uploads_static,
    allow_origins=_allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=["GET"],
    allow_headers=["*"],
)
# Дополнительно инжектируем CORP, чтобы изображения можно было использовать кросс-оригинально в админке
from app.web.header_injector import HeaderInjector

uploads_static = HeaderInjector(
    uploads_static, {"Cross-Origin-Resource-Policy": "cross-origin"}
)
app.mount("/static/uploads", uploads_static, name="uploads")

from app.api.health import router as health_router

app.include_router(health_router)

if TESTING:
    # Minimal routers needed for tests
    from app.domains.auth.api.routers import router as auth_router

    app.include_router(auth_router)
else:
    # Legacy routers (best-effort): import and include inside try-blocks to avoid startup failures
    try:
        # from app.api.tags import router as tags_router  # removed: served by domain router
        # from app.api.quests import router as quests_router  # removed: served by domain router
        from app.api.metrics_exporter import router as metrics_router
        from app.api.rum_metrics import (
            router as rum_metrics_router,
            admin_router as rum_admin_router,
        )

        # app.include_router(tags_router)  # removed: served by domain router
        # app.include_router(quests_router)  # removed: served by domain router
        app.include_router(metrics_router)
        app.include_router(rum_metrics_router)
        app.include_router(rum_admin_router)
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Legacy routers failed to load completely: {e}"
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
        return HTMLResponse("<script>window.location.href='/admin';</script>")
    return {"message": "Hello, World!"}


@app.on_event("startup")
async def startup_event():
    """Выполняется при запуске приложения"""
    logger.info(f"Starting application in {settings.environment} environment")

    # Конфигурируем провайдер эмбеддингов из настроек
    configure_from_settings()
    register_handlers()

    await init_rate_limiter()

    # Проверяем подключение к базе данных
    if await check_database_connection():
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
    await close_rate_limiter()
