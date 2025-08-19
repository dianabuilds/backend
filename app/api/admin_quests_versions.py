from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.quest import Quest
from app.models.quest_version import QuestVersion, QuestGraphNode, QuestGraphEdge
from app.models.quest import Quest
from app.models.user import User
from app.schemas.quest_editor import (
    QuestCreateIn,
    QuestSummary,
    VersionSummary,
    VersionGraph,
    GraphNode,
    GraphEdge,
    ValidateResult,
    SimulateIn,
    SimulateResult,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.quests_editor import validate_graph, simulate_graph
from app.services.audit import audit_log

admin_required = require_admin_role({"admin", "moderator", "editor"})

router = APIRouter(
    prefix="/admin/quests",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("/create", summary="Create a quest (skeleton)")
async def create_quest(
    body: QuestCreateIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    q = Quest(title=body.title, subtitle=None, description=None, author_id=current_user.id, is_draft=True)
    db.add(q)
    await db.flush()
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="quest_create",
        resource_type="quest",
        resource_id=str(q.id),
        after={"title": q.title},
        request=request,
    )
    return {"id": str(q.id)}


@router.get("/{quest_id}", response_model=QuestSummary, summary="Quest with versions")
async def get_quest(
    quest_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    res = await db.execute(select(QuestVersion).where(QuestVersion.quest_id == quest_id).order_by(QuestVersion.number.desc()))
    versions = list(res.scalars().all())
    return QuestSummary(
        id=quest.id,
        slug=quest.slug,
        title=quest.title,
        current_version_id=None,
        versions=[VersionSummary.model_validate(v) for v in versions],
    )


@router.post("/{quest_id}/draft", summary="Create a draft version")
async def create_draft(
    quest_id: UUID,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    # номер версии = max(number)+1
    max_num = (await db.execute(select(func.max(QuestVersion.number)).where(QuestVersion.quest_id == quest_id))).scalar() or 0
    v = QuestVersion(quest_id=quest_id, number=int(max_num) + 1, status="draft", created_by=current_user.id, created_at=datetime.utcnow())
    db.add(v)
    await db.flush()
    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="quest_draft_create",
        resource_type="quest_version",
        resource_id=str(v.id),
        after={"quest_id": str(quest_id), "number": v.number},
        request=request,
    )
    await db.commit()
    return {"versionId": str(v.id)}


@router.get("/versions/{version_id}", response_model=VersionGraph, summary="Get version graph")
async def get_version(
    version_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    nodes = list((await db.execute(select(QuestGraphNode).where(QuestGraphNode.version_id == version_id))).scalars().all())
    edges = list((await db.execute(select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id))).scalars().all())
    return VersionGraph(
        version=VersionSummary(
            id=v.id,
            quest_id=v.quest_id,
            number=v.number,
            status=v.status,
            created_at=v.created_at,
            released_at=v.released_at,
        ),
        nodes=[GraphNode(key=n.key, title=n.title, type=n.type, content=n.content, rewards=n.rewards) for n in nodes],
        edges=[GraphEdge(from_node_key=e.from_node_key, to_node_key=e.to_node_key, label=e.label, condition=e.condition) for e in edges],
    )


@router.put("/versions/{version_id}/graph", summary="Replace graph of the version")
async def put_graph(
    version_id: UUID,
    payload: VersionGraph,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")

    # replace nodes/edges
    # Полностью очищаем текущий граф версии, затем вставляем новый
    from sqlalchemy import delete

    # Сначала рёбра, затем узлы — чтобы не оставлять «висячих» ссылок
    await db.execute(delete(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id))
    await db.execute(delete(QuestGraphNode).where(QuestGraphNode.version_id == version_id))
    # Зафиксируем удаление в текущей транзакции, чтобы уникальные индексы не конфликтовали при вставке
    await db.flush()

    for n in payload.nodes:
        db.add(
            QuestGraphNode(
                version_id=version_id,
                key=n.key,
                title=n.title,
                type=n.type,
                content=n.content,
                rewards=n.rewards,
            )
        )
    for e in payload.edges:
        db.add(
            QuestGraphEdge(
                version_id=version_id,
                from_node_key=e.from_node_key,
                to_node_key=e.to_node_key,
                label=e.label,
                condition=e.condition,
            )
        )

    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="quest_graph_put",
        resource_type="quest_version",
        resource_id=str(version_id),
        after={"nodes": len(payload.nodes), "edges": len(payload.edges)},
        request=request,
    )
    await db.commit()
    return {"ok": True}


@router.post("/versions/{version_id}/validate", response_model=ValidateResult, summary="Validate graph")
async def validate_version(
    version_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    nodes = list((await db.execute(select(QuestGraphNode).where(QuestGraphNode.version_id == version_id))).scalars().all())
    edges = list((await db.execute(select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id))).scalars().all())
    res = validate_graph(
        [GraphNode(key=n.key, title=n.title, type=n.type, content=n.content, rewards=n.rewards) for n in nodes],
        [GraphEdge(from_node_key=e.from_node_key, to_node_key=e.to_node_key, label=e.label, condition=e.condition) for e in edges],
    )
    return res


@router.post("/versions/{version_id}/publish", summary="Publish version")
async def publish_version(
    version_id: UUID,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    if v.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft can be published")

    # validate before publish
    nodes = list((await db.execute(select(QuestGraphNode).where(QuestGraphNode.version_id == version_id))).scalars().all())
    edges = list((await db.execute(select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id))).scalars().all())
    res = validate_graph(
        [GraphNode(key=n.key, title=n.title, type=n.type, content=n.content, rewards=n.rewards) for n in nodes],
        [GraphEdge(from_node_key=e.from_node_key, to_node_key=e.to_node_key, label=e.label, condition=e.condition) for e in edges],
    )
    if not res.ok:
        raise HTTPException(status_code=400, detail="Validation failed")

    v.status = "released"
    v.released_at = datetime.utcnow()
    v.released_by = current_user.id

    # Обновим сам квест: отметим как опубликованный
    q = await db.get(Quest, v.quest_id)
    if q:
        q.is_draft = False
        q.published_at = datetime.utcnow()

    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="quest_version_publish",
        resource_type="quest_version",
        resource_id=str(version_id),
        after={"released_at": v.released_at.isoformat()},
        request=request,
    )
    await db.commit()
    return {"ok": True}


@router.post("/versions/{version_id}/rollback", summary="Rollback to version")
async def rollback_version(
    version_id: UUID,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")

    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="quest_version_rollback",
        resource_type="quest_version",
        resource_id=str(version_id),
        after={"to_version": str(version_id)},
        request=request,
    )
    return {"ok": True}


@router.post("/versions/{version_id}/simulate", response_model=SimulateResult, summary="Simulate run")
async def simulate_version(
    version_id: UUID,
    payload: SimulateIn,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    nodes = list((await db.execute(select(QuestGraphNode).where(QuestGraphNode.version_id == version_id))).scalars().all())
    edges = list((await db.execute(select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id))).scalars().all())
    return simulate_graph(
        [GraphNode(key=n.key, title=n.title, type=n.type, content=n.content, rewards=n.rewards) for n in nodes],
        [GraphEdge(from_node_key=e.from_node_key, to_node_key=e.to_node_key, label=e.label, condition=e.condition) for e in edges],
        payload,
    )


@router.delete("/versions/{version_id}", summary="Delete draft version")
async def delete_draft(
    version_id: UUID,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    if v.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft can be deleted")

    await audit_log(
        db,
        actor_id=str(current_user.id),
        action="quest_version_delete",
        resource_type="quest_version",
        resource_id=str(version_id),
        request=request,
    )
    await db.delete(v)
    return {"ok": True}
