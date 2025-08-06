from fastapi import FastAPI
import logging

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_engine, check_database_connection, close_db_connection

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(auth_router)
app.include_router(users_router)


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

    # Проверяем подключение к базе данных
    if await check_database_connection():
        logger.info("Database connection successful")

        # Создание таблиц в режиме разработки
        if settings.ENVIRONMENT.lower() == "development":
            logger.info("Creating database tables in development mode")
            engine = get_engine()
            async with engine.begin() as conn:
                # await conn.run_sync(Base.metadata.drop_all)  # Раскомментируйте для сброса базы
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    else:
        logger.error("Failed to connect to database during startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Выполняется при остановке приложения"""
    logger.info("Shutting down application")
    await close_db_connection()

