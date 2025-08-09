from fastapi import FastAPI
import logging

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.nodes import router as nodes_router
from app.api.tags import router as tags_router
from app.api.admin import router as admin_router
from app.web.admin import router as admin_ui_router
from app.api.moderation import router as moderation_router
from app.api.transitions import router as transitions_router
from app.api.navigation import router as navigation_router
from app.api.notifications import router as notifications_router, ws_router as notifications_ws_router
from app.api.quests import router as quests_router
from app.api.traces import router as traces_router
from app.api.achievements import router as achievements_router
from app.api.payments import router as payments_router
from app.core.config import settings
from app.engine import configure_from_settings
from app.db.session import (
    check_database_connection,
    close_db_connection,
    init_db,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(nodes_router)
app.include_router(tags_router)
app.include_router(admin_router)
app.include_router(admin_ui_router)
app.include_router(moderation_router)
app.include_router(transitions_router)
app.include_router(navigation_router)
app.include_router(notifications_router)
app.include_router(notifications_ws_router)
app.include_router(quests_router)
app.include_router(traces_router)
app.include_router(achievements_router)
app.include_router(payments_router)


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности приложения"""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Выполняется при запуске приложения"""
    logger.info(f"Starting application in {settings.ENVIRONMENT} environment")

    # Конфигурируем провайдер эмбеддингов из настроек
    configure_from_settings()

    # Проверяем подключение к базе данных
    if await check_database_connection():
        logger.info("Database connection successful")
        await init_db()
    else:
        logger.error("Failed to connect to database during startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Выполняется при остановке приложения"""
    logger.info("Shutting down application")
    await close_db_connection()

