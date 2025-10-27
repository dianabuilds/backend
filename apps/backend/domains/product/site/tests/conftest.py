import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.site.application import SiteService
from domains.product.site.infrastructure import SiteRepository, metadata


@pytest_asyncio.fixture()
async def engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.execute(sa.text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture()
async def repository(engine: AsyncEngine) -> SiteRepository:
    async def factory() -> AsyncEngine | None:
        return engine

    return SiteRepository(factory)


class NotifyStub:
    def __init__(self) -> None:
        self.commands: list = []

    async def create_notification(self, command) -> dict[str, str]:
        self.commands.append(command)
        return {"id": str(len(self.commands)), "user_id": command.user_id}


@pytest_asyncio.fixture()
def notify_stub() -> NotifyStub:
    return NotifyStub()


@pytest_asyncio.fixture()
async def service(repository: SiteRepository, notify_stub: NotifyStub) -> SiteService:
    return SiteService(repository, notify_service=notify_stub)
