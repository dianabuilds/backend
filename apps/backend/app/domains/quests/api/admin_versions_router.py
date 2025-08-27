# ruff: noqa: B008
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_preview_context
from app.core.db.session import get_db
from app.core.preview import PreviewContext
from app.domains.audit.application.audit_service import audit_log
from app.domains.nodes import service as node_service
from app.domains.nodes.service import validate_transition
from app.domains.quests.application.editor_service import EditorService
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.quests.infrastructure.models.quest_version_models import (
    QuestGraphEdge,
    QuestGraphNode,
    QuestVersion,
)
from app.domains.users.infrastructure.models.user import User
from app.schemas.nodes_common import Status
from app.domains.quests.schemas import (
    QuestGraphIn,
    QuestGraphOut,
    QuestStep,
    QuestTransition,
    QuestVersionOut,
)
from app.schemas.quest_editor import (
    QuestCreateIn,
    QuestSummary,
    SimulateIn,
    SimulateResult,
    ValidateResult,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

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
    workspace_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    q = Quest(
        workspace_id=workspace_id,
        title=body.title,
        subtitle=None,
        description=None,
        author_id=current_user.id,
        is_draft=True,
        created_by_user_id=current_user.id,
    )
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
    await db.commit()
    return {"id": str(q.id)}


@router.get("/{quest_id}", response_model=QuestSummary, summary="Quest with versions")
async def get_quest(
    quest_id: UUID,
    workspace_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Quest not found")
    res = await db.execute(
        select(QuestVersion)
        .where(QuestVersion.quest_id == quest_id)
        .order_by(QuestVersion.number.desc())
    )
    versions = list(res.scalars().all())
    return QuestSummary(
        id=quest.id,
        slug=quest.slug,
        title=quest.title,
        current_version_id=None,
        versions=[QuestVersionOut.model_validate(v) for v in versions],
    )


@router.post("/{quest_id}/draft", summary="Create a draft version")
async def create_draft(
    quest_id: UUID,
    request: Request,
    workspace_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Quest not found")
    max_num = (
        await db.execute(
            select(func.max(QuestVersion.number)).where(
                QuestVersion.quest_id == quest_id
            )
        )
    ).scalar() or 0
    v = QuestVersion(
        quest_id=quest_id,
        number=int(max_num) + 1,
        status="draft",
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
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


@router.get(
    "/versions/{version_id}", response_model=QuestGraphOut, summary="Get version graph"
)
async def get_version(
    version_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    nodes = list(
        (
            await db.execute(
                select(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    edges = list(
        (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    return QuestGraphOut(
        version=QuestVersionOut(
            id=v.id,
            quest_id=v.quest_id,
            number=v.number,
            status=v.status,
            created_at=v.created_at,
            released_at=v.released_at,
        ),
        steps=[
            QuestStep(
                key=n.key,
                title=n.title,
                type=n.type,
                content=n.content,
                rewards=n.rewards,
            )
            for n in nodes
        ],
        transitions=[
            QuestTransition(
                from_node_key=e.from_node_key,
                to_node_key=e.to_node_key,
                label=e.label,
                condition=e.condition,
            )
            for e in edges
        ],
    )


@router.put("/versions/{version_id}/graph", summary="Replace graph of the version")
async def put_graph(
    version_id: UUID,
    payload: QuestGraphIn,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")

    from sqlalchemy import delete

    await db.execute(
        delete(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
    )
    await db.execute(
        delete(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
    )
    await db.flush()

    for n in payload.steps:
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
    for e in payload.transitions:
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
        after={"steps": len(payload.steps), "transitions": len(payload.transitions)},
        request=request,
    )
    await db.commit()
    return {"ok": True}


@router.post(
    "/versions/{version_id}/validate",
    response_model=ValidateResult,
    summary="Validate graph",
)
async def validate_version(
    version_id: UUID,
    workspace_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    ver = await db.get(QuestVersion, version_id)
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    q = await db.get(Quest, ver.quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Version not found")
    nodes = list(
        (
            await db.execute(
                select(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    edges = list(
        (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    res = EditorService().validate_graph(
        [
            QuestStep(
                key=n.key,
                title=n.title,
                type=n.type,
                content=n.content,
                rewards=n.rewards,
            )
            for n in nodes
        ],
        [
            QuestTransition(
                from_node_key=e.from_node_key,
                to_node_key=e.to_node_key,
                label=e.label,
                condition=e.condition,
            )
            for e in edges
        ],
    )
    return res


@router.post("/versions/{version_id}/autofix", summary="Autofix graph (basic)")
async def autofix_version(
    version_id: UUID,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")

    nodes = list(
        (
            await db.execute(
                select(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    node_keys = {n.key for n in nodes}
    edges = list(
        (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )

    applied = []

    from sqlalchemy import delete

    invalid_edges = [
        e.id
        for e in edges
        if (e.from_node_key not in node_keys or e.to_node_key not in node_keys)
    ]
    if invalid_edges:
        await db.execute(
            delete(QuestGraphEdge).where(QuestGraphEdge.id.in_(invalid_edges))
        )
        applied.append({"type": "remove_broken_edges", "affected": len(invalid_edges)})

    edges = list(
        (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    seen = set()
    dup_ids = []
    for e in edges:
        k = (e.from_node_key, e.to_node_key)
        if k in seen:
            dup_ids.append(e.id)
        else:
            seen.add(k)
    if dup_ids:
        await db.execute(delete(QuestGraphEdge).where(QuestGraphEdge.id.in_(dup_ids)))
        applied.append({"type": "deduplicate_edges", "affected": len(dup_ids)})

    start_key = next((n.key for n in nodes if n.type == "start"), None)
    if start_key:
        edges = list(
            (
                await db.execute(
                    select(QuestGraphEdge).where(
                        QuestGraphEdge.version_id == version_id
                    )
                )
            )
            .scalars()
            .all()
        )
        incoming_to_start = [e.id for e in edges if e.to_node_key == start_key]
        if incoming_to_start:
            await db.execute(
                delete(QuestGraphEdge).where(QuestGraphEdge.id.in_(incoming_to_start))
            )
            applied.append(
                {"type": "remove_incoming_to_start", "affected": len(incoming_to_start)}
            )

    edges = list(
        (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    outgoing = {}
    for e in edges:
        outgoing.setdefault(e.from_node_key, 0)
        outgoing[e.from_node_key] += 1
    changed = 0
    for n in nodes:
        if n.type != "end" and outgoing.get(n.key, 0) == 0:
            n.type = "end"
            changed += 1
    if changed:
        applied.append({"type": "mark_dead_ends", "affected": changed})

    if applied:
        await audit_log(
            db,
            actor_id=str(current_user.id),
            action="quest_version_autofix",
            resource_type="quest_version",
            resource_id=str(version_id),
            after={"applied": applied},
            request=request,
        )
        await db.commit()

    return {"applied": applied}


@router.post("/versions/{version_id}/publish", summary="Publish version")
async def publish_version(
    version_id: UUID,
    request: Request,
    workspace_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    q = await db.get(Quest, v.quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Version not found")
    if v.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft can be published")

    nodes = list(
        (
            await db.execute(
                select(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    edges = list(
        (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    res = EditorService().validate_graph(
        [
            QuestStep(
                key=n.key,
                title=n.title,
                type=n.type,
                content=n.content,
                rewards=n.rewards,
            )
            for n in nodes
        ],
        [
            QuestTransition(
                from_node_key=e.from_node_key,
                to_node_key=e.to_node_key,
                label=e.label,
                condition=e.condition,
            )
            for e in edges
        ],
    )
    if not res.ok:
        raise HTTPException(status_code=400, detail="Validation failed")

    v.status = "released"
    v.released_at = datetime.utcnow()
    v.released_by = current_user.id

    q = await db.get(Quest, v.quest_id)
    if q:
        if q.status != Status.in_review:
            raise HTTPException(status_code=400, detail="Quest must be in review")
        validate_transition(q.status, Status.published)
        q.status = Status.published
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
    if q:
        await node_service.publish_content(q.id, q.slug, current_user.id)
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


@router.post(
    "/versions/{version_id}/simulate",
    response_model=SimulateResult,
    summary="Simulate run",
)
async def simulate_version(
    version_id: UUID,
    payload: SimulateIn,
    workspace_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
    preview: PreviewContext = Depends(get_preview_context),
):
    ver = await db.get(QuestVersion, version_id)
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    q = await db.get(Quest, ver.quest_id)
    if not q or q.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Version not found")
    nodes = list(
        (
            await db.execute(
                select(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    edges = list(
        (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        )
        .scalars()
        .all()
    )
    return EditorService().simulate_graph(
        [
            QuestStep(
                key=n.key,
                title=n.title,
                type=n.type,
                content=n.content,
                rewards=n.rewards,
            )
            for n in nodes
        ],
        [
            QuestTransition(
                from_node_key=e.from_node_key,
                to_node_key=e.to_node_key,
                label=e.label,
                condition=e.condition,
            )
            for e in edges
        ],
        payload,
        preview,
    )


@router.delete("/versions/{version_id}", summary="Delete draft version")
async def delete_draft(
    version_id: UUID,
    request: Request,
    workspace_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    v = await db.get(QuestVersion, version_id)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")
    q = await db.get(Quest, v.quest_id)
    if not q or q.workspace_id != workspace_id:
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
    await db.commit()
    return {"ok": True}
