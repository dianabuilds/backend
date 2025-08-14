from app.core.env_loader import load_dotenv


load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.nodes import router as nodes_router
from app.api.tags import router as tags_router
from app.api.admin import router as admin_router
from app.api.admin_navigation import router as admin_navigation_router
from app.api.admin_restrictions import router as admin_restrictions_router
from app.api.admin_echo import router as admin_echo_router
from app.api.admin_audit import router as admin_audit_router
from app.api.admin_cache import router as admin_cache_router
from app.api.admin_menu import router as admin_menu_router
from app.api.admin_ratelimit import router as admin_ratelimit_router
from app.api.admin_notifications import router as admin_notifications_router
from app.api.admin_notifications_broadcast import router as admin_notifications_broadcast_router
from app.api.admin_quests import router as admin_quests_router
from app.api.admin_achievements import router as admin_achievements_router
from app.web.admin_spa import router as admin_spa_router
from app.api.moderation import router as moderation_router
from app.api.transitions import router as transitions_router
from app.api.navigation import router as navigation_router
from app.api.notifications import router as notifications_router, ws_router as notifications_ws_router
from app.api.quests import router as quests_router
from app.api.traces import router as traces_router
from app.api.achievements import router as achievements_router
from app.api.payments import router as payments_router
from app.api.search import router as search_router
from app.api.admin_metrics import router as admin_metrics_router
from app.api.admin_embedding import router as admin_embedding_router
from app.api.health import router as health_router
from app.api.metrics_exporter import router as metrics_router
from app.core.config import settings
from app.core.metrics_middleware import MetricsMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.csrf import CSRFMiddleware
from app.core.exception_handlers import register_exception_handlers
from app.engine import configure_from_settings
from app.services.events import register_handlers
from app.db.session import (
    check_database_connection,
    close_db_connection,
    init_db,
)
from app.services.bootstrap import ensure_default_admin
from app.core.rate_limit import init_rate_limiter, close_rate_limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.cookies_security_middleware import CookiesSecurityMiddleware
from app.core.body_limit import BodySizeLimitMiddleware

# Используем базовое логирование из uvicorn/стандартного logging
logger = logging.getLogger(__name__)

app = FastAPI()
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
register_exception_handlers(app)

# CORS: разрешаем фронту ходить на API в dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allowed_methods,
    allow_headers=settings.cors.allowed_headers,
)


DIST_DIR = Path(__file__).resolve().parent.parent / "admin-frontend" / "dist"
DIST_ASSETS_DIR = DIST_DIR / "assets"
if DIST_ASSETS_DIR.exists():
    # serve built frontend assets (js, css, etc.) with correct MIME types
    app.mount(
        "/admin/assets",
        StaticFiles(directory=DIST_ASSETS_DIR),
        name="admin-assets",
    )

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(nodes_router)
app.include_router(tags_router)
app.include_router(admin_router)
app.include_router(admin_navigation_router)
app.include_router(admin_restrictions_router)
app.include_router(admin_echo_router)
app.include_router(admin_audit_router)
app.include_router(admin_cache_router)
app.include_router(admin_menu_router)
app.include_router(admin_ratelimit_router)
app.include_router(admin_notifications_router)
app.include_router(admin_notifications_broadcast_router)
app.include_router(admin_quests_router)
app.include_router(admin_achievements_router)
app.include_router(admin_metrics_router)
app.include_router(admin_embedding_router)
app.include_router(admin_spa_router)
app.include_router(moderation_router)
app.include_router(transitions_router)
app.include_router(navigation_router)
app.include_router(notifications_router)
app.include_router(notifications_ws_router)
app.include_router(quests_router)
app.include_router(traces_router)
app.include_router(achievements_router)
app.include_router(payments_router)
app.include_router(search_router)
app.include_router(health_router)
app.include_router(metrics_router)


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

