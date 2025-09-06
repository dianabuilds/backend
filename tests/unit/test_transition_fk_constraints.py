from __future__ import annotations

import importlib
import sys
import types
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import JSON, Column, ForeignKey, Integer, String, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import TypeDecorator

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

providers_stub = types.ModuleType("app.providers")
db_stub = types.ModuleType("app.providers.db")


class UUIDType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return uuid.UUID(value)


class JSONBType(TypeDecorator):
    impl = JSON


class ARRAYType(TypeDecorator):
    impl = JSON

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type


def ARRAY(item_type):
    return ARRAYType(item_type)


adapters_stub = types.ModuleType("app.providers.db.adapters")
adapters_stub.UUID = UUIDType
adapters_stub.JSONB = JSONBType
adapters_stub.ARRAY = ARRAY

db_stub.adapters = adapters_stub
base_module = types.ModuleType("app.providers.db.base")
Base = declarative_base()
base_module.Base = Base
db_stub.base = base_module
providers_stub.db = db_stub
sys.modules.setdefault("app.providers", providers_stub)
sys.modules.setdefault("app.providers.db", db_stub)
sys.modules.setdefault("app.providers.db.adapters", adapters_stub)
sys.modules.setdefault("app.providers.db.base", base_module)

from app.domains.navigation.infrastructure.models.transition_models import (  # noqa: E402
    NodeTransition,
)


class User(Base):
    __tablename__ = "users"
    id = Column(UUIDType, primary_key=True)


class Workspace(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    owner_user_id = Column(UUIDType, nullable=False)


class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    slug = Column(String, nullable=False)
    author_id = Column(UUIDType, nullable=False)


@pytest_asyncio.fixture()
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


async def _setup_entities(session: AsyncSession) -> tuple[User, Workspace, Node, Node]:
    user = User(id=uuid.uuid4())
    session.add(user)
    await session.flush()

    ws = Workspace(name="w", slug="w", owner_user_id=user.id)
    session.add(ws)
    await session.flush()

    from_node = Node(account_id=ws.id, slug="from", author_id=user.id)
    to_node = Node(account_id=ws.id, slug="to", author_id=user.id)
    session.add_all([from_node, to_node])
    await session.flush()

    return user, ws, from_node, to_node


@pytest.mark.asyncio
async def test_delete_from_node_cascades(session: AsyncSession) -> None:
    user, ws, from_node, to_node = await _setup_entities(session)
    transition = NodeTransition(
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        account_id=ws.id,
        created_by=user.id,
    )
    session.add(transition)
    await session.commit()
    tid = transition.id

    await session.delete(from_node)
    await session.commit()
    res = await session.scalar(select(NodeTransition).where(NodeTransition.id == tid))
    assert res is None


@pytest.mark.asyncio
async def test_delete_to_node_restricts(session: AsyncSession) -> None:
    user, ws, from_node, to_node = await _setup_entities(session)
    transition = NodeTransition(
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        account_id=ws.id,
        created_by=user.id,
    )
    session.add(transition)
    await session.commit()
    tid = transition.id

    with pytest.raises(IntegrityError):
        await session.delete(to_node)
        await session.commit()

    await session.rollback()
    res = await session.scalar(select(NodeTransition).where(NodeTransition.id == tid))
    assert res is not None
