import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.content.infrastructure import home_config_metadata
from domains.product.content.infrastructure.home_config_repository import (
    HomeConfigRepository,
)


@pytest_asyncio.fixture()
async def engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.execute(sa.text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(home_config_metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture()
async def repository(engine: AsyncEngine) -> HomeConfigRepository:
    async def factory() -> AsyncEngine | None:
        return engine

    return HomeConfigRepository(factory)
