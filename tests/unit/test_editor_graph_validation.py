from __future__ import annotations

import importlib
import sys

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.domains.quests.application.editor_service import EditorService  # noqa: E402
from apps.backend.app.domains.quests.schemas.graph import QuestStep, QuestTransition  # noqa: E402


def step(key: str, type_: str = "normal") -> QuestStep:
    return QuestStep(key=key, title=key, type=type_)


def test_end_not_reachable():
    steps = [step("start", "start"), step("mid"), step("end", "end")]
    edges = [QuestTransition(from_node_key="start", to_node_key="mid")]
    res = EditorService().validate_graph(steps, edges)
    assert not res.ok
    assert "End node not reachable: end" in res.errors


def test_no_end_node():
    steps = [step("start", "start"), step("a")]
    edges = [QuestTransition(from_node_key="start", to_node_key="a")]
    res = EditorService().validate_graph(steps, edges)
    assert not res.ok
    assert "There must be at least one end node" in res.errors


def test_isolated_node():
    steps = [step("start", "start"), step("end", "end"), step("iso")]
    edges = [QuestTransition(from_node_key="start", to_node_key="end")]
    res = EditorService().validate_graph(steps, edges)
    assert not res.ok
    assert "Isolated node: iso" in res.errors


def test_unconditional_loop():
    steps = [step("start", "start"), step("a"), step("end", "end")]
    edges = [
        QuestTransition(from_node_key="start", to_node_key="a"),
        QuestTransition(from_node_key="a", to_node_key="a"),
        QuestTransition(from_node_key="a", to_node_key="end"),
    ]
    res = EditorService().validate_graph(steps, edges)
    assert not res.ok
    assert "Unconditional loop at node: a" in res.errors


def test_multiple_unconditional_edges():
    steps = [step("start", "start"), step("a"), step("b"), step("end", "end")]
    edges = [
        QuestTransition(from_node_key="start", to_node_key="a"),
        QuestTransition(from_node_key="start", to_node_key="b"),
        QuestTransition(from_node_key="a", to_node_key="end"),
    ]
    res = EditorService().validate_graph(steps, edges)
    assert not res.ok
    assert "Multiple unconditional transitions from node: start" in res.errors


def test_valid_graph():
    steps = [step("start", "start"), step("a"), step("end", "end")]
    edges = [
        QuestTransition(from_node_key="start", to_node_key="a"),
        QuestTransition(from_node_key="a", to_node_key="end"),
    ]
    res = EditorService().validate_graph(steps, edges)
    assert res.ok
    assert res.errors == []
