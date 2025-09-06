from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest
from fastapi import HTTPException


def _load_node_policy():
    path = (
        Path(__file__).resolve().parents[2]
        / "apps/backend/app/domains/nodes/policies/node_policy.py"
    )
    spec = util.spec_from_file_location("node_policy", path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.NodePolicy


class StubNode:
    def __init__(self, author_id: str, is_visible: bool = False) -> None:
        self.author_id = author_id
        self.is_visible = is_visible


class StubUser:
    def __init__(self, user_id: str, role: str) -> None:
        self.id = user_id
        self.role = role


def test_override_allows_editor_access() -> None:
    NodePolicy = _load_node_policy()

    node = StubNode(author_id="author", is_visible=False)
    user = StubUser(user_id="other", role="editor")
    NodePolicy.ensure_can_view(node, user, override=True)
    NodePolicy.ensure_can_edit(node, user, override=True)


def test_override_disallowed_for_regular_user() -> None:
    NodePolicy = _load_node_policy()

    node = StubNode(author_id="author", is_visible=False)
    user = StubUser(user_id="other", role="user")
    with pytest.raises(HTTPException):
        NodePolicy.ensure_can_view(node, user, override=True)
    with pytest.raises(HTTPException):
        NodePolicy.ensure_can_edit(node, user, override=True)
