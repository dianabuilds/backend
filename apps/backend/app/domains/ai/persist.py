from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any
from uuid import UUID as _UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.generation_models import GenerationJob
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.quests.infrastructure.models.quest_version_models import (
    QuestGraphEdge,
    QuestGraphNode,
    QuestVersion,
)


def _pick_author_id(job: GenerationJob) -> _UUID:
    if getattr(job, "created_by", None):
        return job.created_by  # type: ignore[return-value]
    env_id = os.getenv("AI_DEFAULT_AUTHOR_ID")
    if env_id:
        try:
            return _UUID(env_id)
        except Exception:
            pass
    raise RuntimeError("author_id_missing: set job.created_by or AI_DEFAULT_AUTHOR_ID")


def _normalize_graph(graph: Any) -> tuple[list[dict], list[dict]]:
    """Принимает граф в произвольной форме и приводит к спискам nodes/edges."""
    if isinstance(graph, str):
        graph = json.loads(graph)
    if not isinstance(graph, dict):
        raise ValueError("graph_json_invalid")
    payload = (
        graph.get("graph")
        if "graph" in graph and isinstance(graph["graph"], dict)
        else graph
    )
    nodes = payload.get("nodes") or []
    edges = payload.get("edges") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("graph_missing_nodes_edges")
    return nodes, edges


async def persist_generated_quest(
    db: AsyncSession, job: GenerationJob, graph_json: Any
) -> tuple[Any, Any]:
    """Создаёт квест и первую версию на основе JSON графа (узлы/ребра).
    Возвращает (quest_id, version_id).
    """
    nodes, edges = _normalize_graph(graph_json)
    params = job.params or {}
    author_id = _pick_author_id(job)

    # Название квеста
    extras = params.get("extras") if isinstance(params.get("extras"), dict) else {}
    title = (
        extras.get("title")
        or params.get("title")
        or f"AI Quest {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )

    quest = Quest(
        title=title,
        subtitle=None,
        description=None,
        author_id=author_id,
        structure=params.get("structure"),
        length=params.get("length"),
        tone=params.get("tone"),
        genre=params.get("genre"),
        locale=params.get("locale"),
        is_draft=True,
        allow_comments=True,
    )
    db.add(quest)
    await db.flush()  # получить quest.id

    version = QuestVersion(
        quest_id=quest.id,
        number=1,
        status="draft",
        created_by=getattr(job, "created_by", None),
        parent_version_id=None,
        meta={"generated_by": "ai", "job_id": str(job.id)},
    )
    db.add(version)
    await db.flush()  # получить version.id

    # Узлы
    used_keys: set[str] = set()
    for idx, n in enumerate(nodes):
        key = n.get("key") or n.get("id") or f"n{idx+1}"
        if key in used_keys:
            # обезопасим дубликаты
            key = f"{key}_{idx+1}"
        used_keys.add(key)
        title = n.get("title") or n.get("name") or key
        ntype = n.get("type") or "normal"
        # Контент: берём nodes или собираем из text/choices
        content = n.get("nodes")
        if not isinstance(content, dict):
            content = {}
        if "text" in n and "text" not in content:
            content["text"] = n.get("text")
        if "choices" in n and "choices" not in content:
            content["choices"] = n.get("choices") or []
        rewards = n.get("rewards") if isinstance(n.get("rewards"), dict) else None

        qn = QuestGraphNode(
            version_id=version.id,
            key=str(key),
            title=str(title),
            type=str(ntype),
            content=content or None,
            rewards=rewards,
        )
        db.add(qn)

    # Рёбра
    for e in edges:
        from_key = e.get("from_node_key") or e.get("from") or e.get("source")
        to_key = e.get("to_node_key") or e.get("to") or e.get("target")
        if not from_key or not to_key:
            continue
        label = e.get("label") or e.get("choice")
        condition = e.get("condition") if isinstance(e.get("condition"), dict) else None
        qe = QuestGraphEdge(
            version_id=version.id,
            from_node_key=str(from_key),
            to_node_key=str(to_key),
            label=str(label) if label is not None else None,
            condition=condition,
        )
        db.add(qe)

    await db.flush()
    return quest.id, version.id
