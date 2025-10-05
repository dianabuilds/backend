import importlib
from types import SimpleNamespace
from unittest.mock import patch

import pytest

with patch("prometheus_client.Counter"), patch("prometheus_client.Histogram"):
    _admin_queries = importlib.import_module(
        "apps.backend.domains.product.nodes.application.admin_queries"
    )
_emit_admin_activity = _admin_queries._emit_admin_activity


class DummySafePublisher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def _safe_publish(
        self,
        event: str,
        payload: dict,
        *,
        key: str | None = None,
        context: dict | None = None
    ) -> None:
        self.calls.append(
            {"event": event, "payload": payload, "key": key, "context": context}
        )


class DummyEvents:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        self.calls.append({"event": topic, "payload": payload, "key": key})


@pytest.mark.asyncio
async def test_emit_admin_activity_prefers_safe_publish() -> None:
    nodes_service = DummySafePublisher()
    events = DummyEvents()
    container = SimpleNamespace(nodes_service=nodes_service, events=events, audit=None)

    await _emit_admin_activity(
        container,
        event="node.updated.v1",
        payload={"id": 42},
        key="node:42",
        event_context={"node_id": 42},
    )

    assert events.calls == []
    assert nodes_service.calls and nodes_service.calls[0]["event"] == "node.updated.v1"
    context = nodes_service.calls[0]["context"]
    assert context is not None
    assert context["source"] == "nodes_admin_api"
    assert context["node_id"] == 42


@pytest.mark.asyncio
async def test_emit_admin_activity_falls_back_to_events() -> None:
    events = DummyEvents()
    container = SimpleNamespace(events=events, audit=None)

    await _emit_admin_activity(
        container,
        event="node.updated.v1",
        payload={"id": 7},
        key="node:7",
    )

    assert events.calls == [
        {"event": "node.updated.v1", "payload": {"id": 7}, "key": "node:7"}
    ]


@pytest.mark.asyncio
async def test_emit_admin_activity_writes_audit_log() -> None:
    calls: list[dict] = []

    async def log(**kwargs) -> None:
        calls.append(kwargs)

    audit = SimpleNamespace(service=SimpleNamespace(log=log))
    container = SimpleNamespace(nodes_service=None, events=DummyEvents(), audit=audit)

    await _emit_admin_activity(
        container,
        audit_action="product.nodes.test",
        audit_actor="actor",
        audit_resource_type="node",
        audit_resource_id="42",
        audit_reason="test",
        audit_extra={"foo": "bar"},
    )

    assert calls == [
        {
            "actor_id": "actor",
            "action": "product.nodes.test",
            "resource_type": "node",
            "resource_id": "42",
            "reason": "test",
            "extra": {"foo": "bar"},
        }
    ]
