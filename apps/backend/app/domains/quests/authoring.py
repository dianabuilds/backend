from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.quests.infrastructure.models.quest_version_models import (
    QuestVersion,
    QuestGraphNode,
    QuestGraphEdge,
)
from app.schemas.quest import QuestCreate, QuestUpdate
from app.domains.users.infrastructure.models.user import User
from app.domains.quests.versions import release_latest, ValidationFailed
from uuid import UUID


async def create_quest(
    db: AsyncSession,
    *,
    payload: QuestCreate,
    author: User,
    workspace_id: UUID,
) -> Quest:
    quest = Quest(
        workspace_id=workspace_id,
        title=payload.title,
        subtitle=payload.subtitle,
        description=payload.description,
        cover_image=payload.cover_image,
        tags=payload.tags,
        price=payload.price,
        is_premium_only=payload.is_premium_only,
        entry_node_id=payload.entry_node_id,
        nodes=payload.nodes,
        custom_transitions=payload.custom_transitions,
        allow_comments=payload.allow_comments,
        author_id=author.id,
        created_by_user_id=author.id,
    )
    db.add(quest)
    await db.commit()
    await db.refresh(quest)
    return quest


async def update_quest(
    db: AsyncSession,
    *,
    quest_id: UUID,
    workspace_id: UUID,
    payload: QuestUpdate,
    actor: User,
) -> Quest:
    result = await db.execute(
        select(Quest).where(
            Quest.id == quest_id,
            Quest.workspace_id == workspace_id,
            Quest.is_deleted == False,
        )
    )
    quest = result.scalars().first()
    if not quest:
        raise ValueError("Quest not found")
    if quest.author_id != actor.id:
        raise PermissionError("Not authorized")
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(quest, field, value)
    quest.updated_by_user_id = actor.id
    await db.commit()
    await db.refresh(quest)
    return quest


async def _latest_version(db: AsyncSession, quest_id: UUID) -> QuestVersion | None:
    res = await db.execute(
        select(QuestVersion).where(QuestVersion.quest_id == quest_id).order_by(QuestVersion.number.desc())
    )
    return res.scalars().first()


async def publish_quest(
    db: AsyncSession, *, quest_id: UUID, workspace_id: UUID, actor: User
) -> Quest:
    """Публикация квеста — делегирует в versions.release_latest с жёсткой валидацией."""
    return await release_latest(
        db, quest_id=quest_id, workspace_id=workspace_id, actor=actor
    )


_KEY_RE = re.compile(r"^[A-Za-z0-9_.:\-]+$")


def validate_graph_input(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    *,
    allow_self_loops: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Нормализация и валидация входных данных графа:
    - key обязателен, строка, формат по _KEY_RE
    - уникальность ключей узлов
    - рёбра ссылаются на существующие узлы
    - самоссылки запрещены (если allow_self_loops=False)
    Возвращает нормализованные nodes/edges.
    """
    norm_nodes: List[Dict[str, Any]] = []
    keys: set[str] = set()
    for idx, n in enumerate(nodes or []):
        key = str(n.get("key") or n.get("id") or f"n{idx+1}").strip()
        if not key or not _KEY_RE.match(key):
            raise ValueError(f"Invalid node key: {key!r}")
        if key in keys:
            raise ValueError(f"Duplicate node key: {key}")
        keys.add(key)
        norm_nodes.append(
            {
                "key": key,
                "title": n.get("title") or n.get("name") or key,
                "type": n.get("type") or "normal",
                "nodes": (n.get("nodes") if isinstance(n.get("nodes"), dict) else None),
                "rewards": (n.get("rewards") if isinstance(n.get("rewards"), dict) else None),
            }
        )
    norm_edges: List[Dict[str, Any]] = []
    for e in edges or []:
        fk = str(e.get("from_node_key") or e.get("from") or e.get("source") or "").strip()
        tk = str(e.get("to_node_key") or e.get("to") or e.get("target") or "").strip()
        if not fk or not tk:
            raise ValueError("Edge must have from/to")
        if fk not in keys or tk not in keys:
            raise ValueError(f"Edge refers to missing node: {fk}->{tk}")
        if not allow_self_loops and fk == tk:
            raise ValueError(f"Self-loop is not allowed: {fk}")
        norm_edges.append(
            {
                "from_node_key": fk,
                "to_node_key": tk,
                "label": e.get("label") or e.get("choice"),
                "condition": (e.get("condition") if isinstance(e.get("condition"), dict) else None),
            }
        )
    return norm_nodes, norm_edges


async def batch_upsert_graph(
    db: AsyncSession,
    *,
    version_id: UUID,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    remove_missing: bool = True,
) -> Dict[str, int]:
    """
    Массовый upsert графа: узлы по key и полное пересоздание рёбер.
    Если remove_missing=True — удаляет узлы, не попавшие в список, и их рёбра.
    Возвращает счётчики {"inserted": x, "updated": y, "deleted": z, "edges": n}.
    """
    # Валидируем и нормализуем входные данные
    nodes, edges = validate_graph_input(nodes, edges)

    res = await db.execute(select(QuestGraphNode).where(QuestGraphNode.version_id == version_id))
    existing_nodes = {n.key: n for n in res.scalars().all()}
    in_keys = set()
    inserted = updated = deleted = 0

    # Upsert nodes
    for n in nodes:
        key = n["key"]
        in_keys.add(key)
        if key in existing_nodes:
            node = existing_nodes[key]
            node.title = n["title"]
            node.type = n["type"]
            node.content = n["nodes"]
            node.rewards = n["rewards"]
            updated += 1
        else:
            db.add(
                QuestGraphNode(
                    version_id=version_id,
                    key=key,
                    title=n["title"],
                    type=n["type"],
                    content=n["nodes"],
                    rewards=n["rewards"],
                )
            )
            inserted += 1

    # Delete missing nodes (and their edges)
    if remove_missing:
        to_delete = [k for k in existing_nodes.keys() if k not in in_keys]
        if to_delete:
            await db.execute(delete(QuestGraphEdge).where(
                QuestGraphEdge.version_id == version_id,
                (QuestGraphEdge.from_node_key.in_(to_delete)) | (QuestGraphEdge.to_node_key.in_(to_delete)),
            ))
            await db.execute(delete(QuestGraphNode).where(
                QuestGraphNode.version_id == version_id,
                QuestGraphNode.key.in_(to_delete),
            ))
            deleted += len(to_delete)

    # Recreate edges (нормализованные, гарантированно валидные)
    await db.execute(delete(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id))
    edge_count = 0
    for e in edges:
        db.add(
            QuestGraphEdge(
                version_id=version_id,
                from_node_key=e["from_node_key"],
                to_node_key=e["to_node_key"],
                label=str(e["label"]) if e.get("label") is not None else None,
                condition=e.get("condition"),
            )
        )
        edge_count += 1

    await db.commit()
    return {"inserted": inserted, "updated": updated, "deleted": deleted, "edges": edge_count}


async def rename_node_key(db: AsyncSession, *, version_id: UUID, old_key: str, new_key: str) -> None:
    """Переименовать ключ узла и обновить ссылки в рёбрах."""
    if old_key == new_key:
        return
    res = await db.execute(select(QuestGraphNode).where(QuestGraphNode.version_id == version_id, QuestGraphNode.key == old_key))
    node = res.scalars().first()
    if not node:
        raise ValueError("Node not found")
    # проверяем конфликт
    res2 = await db.execute(select(QuestGraphNode).where(QuestGraphNode.version_id == version_id, QuestGraphNode.key == new_key))
    if res2.scalars().first():
        raise ValueError("New key already exists")
    node.key = new_key
    # обновляем рёбра
    await db.execute(
        update(QuestGraphEdge)
        .where(QuestGraphEdge.version_id == version_id, QuestGraphEdge.from_node_key == old_key)
        .values(from_node_key=new_key)
    )
    await db.execute(
        update(QuestGraphEdge)
        .where(QuestGraphEdge.version_id == version_id, QuestGraphEdge.to_node_key == old_key)
        .values(to_node_key=new_key)
    )
    await db.commit()


async def delete_node(db: AsyncSession, *, version_id: UUID, key: str, cascade_edges: bool = True) -> None:
    """Удалить узел и, опционально, связанные рёбра."""
    if cascade_edges:
        await db.execute(
            delete(QuestGraphEdge).where(
                QuestGraphEdge.version_id == version_id,
                (QuestGraphEdge.from_node_key == key) | (QuestGraphEdge.to_node_key == key),
            )
        )
    await db.execute(
        delete(QuestGraphNode).where(QuestGraphNode.version_id == version_id, QuestGraphNode.key == key)
    )
    await db.commit()


async def delete_quest_soft(
    db: AsyncSession, *, quest_id: UUID, workspace_id: UUID, actor: User
) -> None:
    """Мягкое удаление квеста (пометка is_deleted=True) с проверкой владельца."""
    res = await db.execute(
        select(Quest).where(
            Quest.id == quest_id,
            Quest.workspace_id == workspace_id,
            Quest.is_deleted == False,
        )
    )  # noqa: E712
    quest = res.scalars().first()
    if not quest:
        raise ValueError("Quest not found")
    if quest.author_id != actor.id:
        raise PermissionError("Not authorized")
    quest.is_deleted = True
    await db.commit()
