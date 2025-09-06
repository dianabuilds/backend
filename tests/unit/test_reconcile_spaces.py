"""Tests for reconcile_spaces script."""

# ruff: noqa: E402

import importlib
import logging
import sys
import tempfile
import types
import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Stub minimal application modules to isolate script dependencies
Base = declarative_base()


class Node(Base):
    __tablename__ = "nodes"
    id = sa.Column(sa.Integer, primary_key=True)
    slug = sa.Column(sa.String, nullable=False)
    workspace_id = sa.Column(sa.String, nullable=False)


class NavigationCache(Base):
    __tablename__ = "navigation_cache"
    id = sa.Column(sa.Integer, primary_key=True)
    node_slug = sa.Column(sa.String, nullable=False)
    space_id = sa.Column(sa.String, nullable=True)
    navigation = sa.Column(sa.JSON, default=dict)
    compass = sa.Column(sa.JSON, default=list)
    echo = sa.Column(sa.JSON, default=list)


node_module = types.ModuleType("apps.backend.app.domains.nodes.infrastructure.models.node")
node_module.Node = Node
sys.modules[node_module.__name__] = node_module

nav_module = types.ModuleType(
    "apps.backend.app.domains.quests.infrastructure.models.navigation_cache_models"
)
nav_module.NavigationCache = NavigationCache
sys.modules[nav_module.__name__] = nav_module

config_module = types.ModuleType("apps.backend.app.core.config")
config_module.settings = types.SimpleNamespace(database_url="")
sys.modules[config_module.__name__] = config_module

logging_module = types.ModuleType("apps.backend.app.core.logging_configuration")
logging_module.configure_logging = lambda *args, **kwargs: None
sys.modules[logging_module.__name__] = logging_module

# Import script after stubbing dependencies
reconcile_spaces = importlib.import_module("scripts.reconcile_spaces")


@pytest.mark.asyncio
async def test_reconcile_spaces_backfills_space_id(monkeypatch, caplog) -> None:
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        url = f"sqlite+aiosqlite:///{tmp.name}"
        config_module.settings.database_url = url
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            ws_id = str(uuid.uuid4())
            node = Node(id=1, workspace_id=ws_id, slug="n")
            cache = NavigationCache(node_slug="n")
            session.add_all([node, cache])
            await session.commit()
        caplog.set_level(logging.INFO)
        anomalies = await reconcile_spaces._reconcile()
        assert anomalies == 0
        async with async_session() as session:
            rec = (
                await session.execute(
                    sa.select(NavigationCache).where(NavigationCache.node_slug == "n")
                )
            ).scalar_one()
            assert rec.space_id == ws_id
        await engine.dispose()


@pytest.mark.asyncio
async def test_reconcile_spaces_logs_mismatch(monkeypatch, caplog) -> None:
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        url = f"sqlite+aiosqlite:///{tmp.name}"
        config_module.settings.database_url = url
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        ws_id = str(uuid.uuid4())
        other_ws = str(uuid.uuid4())
        async with async_session() as session:
            node = Node(id=1, workspace_id=ws_id, slug="n")
            cache = NavigationCache(node_slug="n", space_id=other_ws)
            session.add_all([node, cache])
            await session.commit()
        caplog.set_level(logging.WARNING)
        anomalies = await reconcile_spaces._reconcile()
        assert anomalies == 1
        assert any("workspace_mismatch" in r.message for r in caplog.records)
        await engine.dispose()
