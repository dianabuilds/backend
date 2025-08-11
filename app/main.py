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
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.exception_handlers import register_exception_handlers
from app.core.sentry import init_sentry
from app.engine import configure_from_settings
from app.db.session import (
    check_database_connection,
    close_db_connection,
    init_db,
)
from app.services.bootstrap import ensure_default_admin
from app.core.rate_limit import init_rate_limiter, close_rate_limiter

# Настройка логирования
configure_logging()
init_sentry(settings)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
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


@app.get("/")
async def read_root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        return HTMLResponse("<script>window.location.href='/admin';</script>")
    return {"message": "Hello, World!"}


@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности приложения"""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Выполняется при запуске приложения"""
    logger.info(f"Starting application in {settings.environment} environment")

    # Конфигурируем провайдер эмбеддингов из настроек
    configure_from_settings()

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

