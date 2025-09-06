from __future__ import annotations

import asyncio
import importlib
import sys
import types
import uuid
from dataclasses import dataclass

fastapi_stub = types.ModuleType("fastapi")


class _Req:  # noqa: D401 - minimal stub
    """Stub FastAPI Request"""


fastapi_stub.Request = _Req
sys.modules.setdefault("fastapi", fastapi_stub)

# Ensure apps package is importable
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.domains.navigation.application.providers import (  # noqa: E402
    EchoProvider,
)

from app.core.preview import PreviewContext  # noqa: E402


@dataclass
class DummyNode:
    slug: str
    workspace_id: uuid.UUID


class DummyService:
    async def get_echo_transitions(
        self,
        db,
        node,
        limit,
        *,
        user=None,
        preview: PreviewContext | None = None,
        account_id=None,
    ):
        other_ws = uuid.uuid4()
        candidates = [
            DummyNode("a", workspace_id=node.workspace_id),
            DummyNode("b", workspace_id=other_ws),
        ]
        return [n for n in candidates if n.workspace_id == account_id]


def test_echo_provider_filters_workspace():
    ws_id = uuid.uuid4()
    provider = EchoProvider(DummyService())
    node = DummyNode("start", workspace_id=ws_id)
    result = asyncio.run(provider.get_transitions(None, node, None, ws_id))
    assert [n.slug for n in result] == ["a"]
