from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Header
from sqlalchemy import String, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from uuid import UUID

from app.api.deps import (
    assert_owner_or_role,
    assert_seniority_over,
    get_current_user,
)
from app.db.session import get_db
from app.models.user import User
from app.models.node import Node
from app.models.tag import Tag, NodeTag
from app.models.transition import NodeTransition, NodeTransitionType
from app.models.moderation import UserRestriction
from app.models.quest import Quest
from app.schemas.user import AdminUserOut, UserPremiumUpdate, UserRoleUpdate
from app.schemas.node import NodeOut, NodeBulkOperation
from app.schemas.tag import (
    AdminTagOut,
    TagCreate,
    TagUpdate,
    TagMerge,
    TagDetachRequest,
)
from app.schemas.transition import (
    AdminTransitionOut,
    NodeTransitionUpdate,
    TransitionDisableRequest,
)
from app.services.query import (
    NodeFilterSpec,
    NodeQueryService,
    TransitionFilterSpec,
    TransitionQueryService,
    PageRequest,
    QueryContext,
)
from app.engine.embedding import update_node_embedding
from app.services.navcache import navcache
from app.core.log_events import cache_invalidate
from app.core.config import settings
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()
admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)

logger = logging.getLogger(__name__)


@router.get("/dashboard", summary="Admin dashboard data")
async def admin_dashboard(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Return basic statistics for the admin dashboard."""
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    result = await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= day_ago)
    )
    new_registrations = result.scalar() or 0

    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.is_premium == True)  # noqa: E712
    )
    active_premium = result.scalar() or 0

    result = await db.execute(
        select(func.count()).select_from(Node).where(Node.created_at >= day_ago)
    )
    nodes_created = result.scalar() or 0

    result = await db.execute(
        select(func.count()).select_from(Quest).where(Quest.created_at >= day_ago)
    )
    quests_created = result.scalar() or 0

    result = await db.execute(
        select(Node.id, Node.title).order_by(Node.created_at.desc()).limit(5)
    )
    latest_nodes = [
        {"id": str(row.id), "title": row.title or ""} for row in result.all()
    ]

    result = await db.execute(
        select(
            UserRestriction.id,
            UserRestriction.user_id,
            UserRestriction.reason,
        )
        .order_by(UserRestriction.created_at.desc())
        .limit(5)
    )
    latest_restrictions = [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "reason": r.reason or "",
        }
        for r in result.all()
    ]

    db_ok = True
    try:
        await db.execute(select(1))
    except Exception:
        db_ok = False

    redis_ok = True
    try:
        await navcache._cache.get("__healthcheck__")
    except Exception:
        redis_ok = False

    try:
        nav_keys = len(await navcache._cache.scan(f"{settings.cache.key_version}:nav*"))
        comp_keys = len(
            await navcache._cache.scan(f"{settings.cache.key_version}:comp*")
        )
    except Exception:
        nav_keys = 0
        comp_keys = 0

    return {
        "kpi": {
            "active_users_24h": 0,
            "new_registrations_24h": new_registrations,
            "active_premium": active_premium,
            "nodes_24h": nodes_created,
            "quests_24h": quests_created,
        },
        "latest_nodes": latest_nodes,
        "latest_restrictions": latest_restrictions,
        "system": {
            "db_ok": db_ok,
            "redis_ok": redis_ok,
            "nav_keys": nav_keys,
            "comp_keys": comp_keys,
        },
    }


@router.get("/users", response_model=list[AdminUserOut], summary="List users")
async def list_users(
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    premium: str | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of users with optional filters."""
    stmt = select(User).offset(offset).limit(limit)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(pattern),
                User.username.ilike(pattern),
                func.cast(User.id, String).ilike(pattern),
            )
        )
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if premium == "active":
        stmt = stmt.where(User.is_premium == True)  # noqa: E712
    elif premium == "expired":
        stmt = stmt.where(User.is_premium == False)  # noqa: E712

    result = await db.execute(stmt)
    users = result.scalars().all()

    user_ids = [u.id for u in users]
    restrictions_map: dict[UUID, list[UserRestriction]] = {}
    if user_ids:
        res = await db.execute(
            select(UserRestriction).where(UserRestriction.user_id.in_(user_ids))
        )
        for r in res.scalars().all():
            restrictions_map.setdefault(r.user_id, []).append(r)

    return [
        AdminUserOut(
            id=u.id,
            created_at=u.created_at,
            email=u.email,
            wallet_address=u.wallet_address,
            is_active=u.is_active,
            username=u.username,
            bio=u.bio,
            avatar_url=u.avatar_url,
            role=u.role,
            is_premium=u.is_premium,
            premium_until=u.premium_until,
            restrictions=restrictions_map.get(u.id, []),
        )
        for u in users
    ]


@router.post("/users/{user_id}/premium", summary="Set user premium status")
async def set_user_premium(
    user_id: UUID,
    payload: UserPremiumUpdate,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Grant or revoke premium access for a specific user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id == user.id:
        raise HTTPException(status_code=403, detail="Cannot modify self")
    assert_seniority_over(user, current_user)
    user.is_premium = payload.is_premium
    user.premium_until = payload.premium_until
    await db.commit()
    await db.refresh(user)
    logger.info(
        "admin_action",
        extra={
            "action": "set_premium",
            "actor_id": str(current_user.id),
            "target_user_id": str(user.id),
            "payload": payload.model_dump(),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"is_premium": user.is_premium, "premium_until": user.premium_until}


@router.post("/users/{user_id}/role", summary="Change user role")
async def set_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Assign a new role to a user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id == user.id:
        raise HTTPException(status_code=403, detail="Cannot modify self")
    assert_seniority_over(user, current_user)
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    logger.info(
        "admin_action",
        extra={
            "action": "set_role",
            "actor_id": str(current_user.id),
            "target_user_id": str(user.id),
            "payload": payload.model_dump(),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"role": user.role}


@router.get("/nodes", response_model=list[NodeOut], summary="List nodes")
async def list_nodes_admin(
    response: Response,
    if_none_match: str | None = Header(None, alias="If-None-Match"),
    author: UUID | None = None,
    tags: str | None = Query(None),
    match: str = Query("any", pattern="^(any|all)$"),
    is_public: bool | None = None,
    premium_only: bool | None = None,
    recommendable: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List nodes for admin interface with various filters."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    # regular users can only see their own nodes
    is_moderator = current_user.role in {"moderator", "admin"}
    effective_author = author if is_moderator else current_user.id
    spec = NodeFilterSpec(
        author=effective_author,
        tags=tag_list,
        match=match,
        is_public=is_public,
        premium_only=premium_only,
        recommendable=recommendable,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )
    ctx = QueryContext(user=current_user, is_admin=True)
    service = NodeQueryService(db)
    page = PageRequest()
    etag = await service.compute_nodes_etag(spec, ctx, page)
    if if_none_match and if_none_match == etag:
        # Не отдаем 304, чтобы избежать CORS-проблем с fetch; всегда возвращаем данные.
        pass
    nodes = await service.list_nodes(spec, page, ctx)
    try:
        response.headers["ETag"] = etag  # type: ignore[name-defined]
    except NameError:
        pass
    return nodes


@router.post("/nodes/{node_id}/embedding/recompute", summary="Recompute node embedding")
async def recompute_node_embedding(
    node_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    node = await db.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    assert_owner_or_role(node.author_id, "moderator", current_user)
    await update_node_embedding(db, node)
    return {"embedding_dim": len(node.embedding_vector or [])}


@router.post("/nodes/bulk", summary="Bulk node operations")
async def bulk_node_operation(
    payload: NodeBulkOperation,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.id.in_(payload.ids)))
    nodes = result.scalars().all()
    for node in nodes:
        if payload.op == "hide":
            node.is_visible = False
        elif payload.op == "show":
            node.is_visible = True
        elif payload.op == "public":
            node.is_public = True
        elif payload.op == "private":
            node.is_public = False
        elif payload.op == "toggle_premium":
            node.premium_only = not node.premium_only
        elif payload.op == "toggle_recommendable":
            node.is_recommendable = not node.is_recommendable
        node.updated_at = datetime.utcnow()
    await db.commit()
    return {"updated": [str(n.id) for n in nodes]}


# --- Transitions -------------------------------------------------------------


@router.get(
    "/transitions",
    response_model=list[AdminTransitionOut],
    summary="List transitions",
)
async def list_transitions_admin(
    from_slug: str | None = Query(None, alias="from"),
    to_slug: str | None = Query(None, alias="to"),
    type: NodeTransitionType | None = None,
    author: UUID | None = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of manual transitions."""
    spec = TransitionFilterSpec(
        from_slug=from_slug,
        to_slug=to_slug,
        type=type,
        author=author,
    )
    ctx = QueryContext(user=current_user, is_admin=True)
    service = TransitionQueryService(db)
    rows = await service.list_transitions(
        spec,
        PageRequest(limit=page_size, offset=(page - 1) * page_size),
        ctx,
    )
    return [
        AdminTransitionOut(
            id=t.id,
            from_slug=fs,
            to_slug=ts,
            type=t.type,
            weight=t.weight,
            label=t.label,
            created_by=t.created_by,
            created_at=t.created_at,
        )
        for t, fs, ts in rows
    ]


@router.patch(
    "/transitions/{transition_id}",
    response_model=AdminTransitionOut,
    summary="Update transition",
)
async def update_transition_admin(
    transition_id: UUID,
    payload: NodeTransitionUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Update fields of a manual transition."""
    transition = await db.get(NodeTransition, transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")

    old_from = await db.get(Node, transition.from_node_id)
    old_from_slug = old_from.slug if old_from else None

    if payload.from_slug:
        res = await db.execute(select(Node).where(Node.slug == payload.from_slug))
        new_from = res.scalars().first()
        if not new_from:
            raise HTTPException(status_code=404, detail="Source node not found")
        transition.from_node_id = new_from.id
    if payload.to_slug:
        res = await db.execute(select(Node).where(Node.slug == payload.to_slug))
        new_to = res.scalars().first()
        if not new_to:
            raise HTTPException(status_code=404, detail="Target node not found")
        transition.to_node_id = new_to.id
    if payload.type:
        transition.type = payload.type
    if payload.condition is not None:
        transition.condition = payload.condition.model_dump(exclude_none=True)
    if payload.weight is not None:
        transition.weight = payload.weight
    if payload.label is not None:
        transition.label = payload.label

    await db.commit()
    await db.refresh(transition)

    from_node = await db.get(Node, transition.from_node_id)
    from_slug = from_node.slug if from_node else old_from_slug

    await navcache.invalidate_navigation_by_node(from_slug)
    await navcache.invalidate_compass_by_node(from_slug)
    cache_invalidate("nav", reason="transition_update", key=from_slug)
    cache_invalidate("comp", reason="transition_update", key=from_slug)
    logger.info(
        "admin_action",
        extra={
            "action": "update_transition",
            "actor_id": str(current_user.id),
            "transition_id": str(transition.id),
            "payload": payload.model_dump(exclude_none=True),
            "ts": datetime.utcnow().isoformat(),
        },
    )

    to_node = await db.get(Node, transition.to_node_id)
    return AdminTransitionOut(
        id=transition.id,
        from_slug=from_node.slug if from_node else "",
        to_slug=to_node.slug if to_node else "",
        type=transition.type,
        weight=transition.weight,
        label=transition.label,
        created_by=transition.created_by,
        created_at=transition.created_at,
    )


@router.delete("/transitions/{transition_id}", summary="Delete transition")
async def delete_transition_admin(
    transition_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Remove a manual transition."""
    transition = await db.get(NodeTransition, transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")
    from_node = await db.get(Node, transition.from_node_id)
    from_slug = from_node.slug if from_node else None
    await db.delete(transition)
    await db.commit()
    if from_slug:
        await navcache.invalidate_navigation_by_node(from_slug)
        await navcache.invalidate_compass_by_node(from_slug)
        cache_invalidate("nav", reason="transition_delete", key=from_slug)
        cache_invalidate("comp", reason="transition_delete", key=from_slug)
    logger.info(
        "admin_action",
        extra={
            "action": "delete_transition",
            "actor_id": str(current_user.id),
            "transition_id": str(transition_id),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"message": "Transition deleted"}


@router.post(
    "/transitions/disable_by_node",
    summary="Disable transitions by node",
)
async def disable_transitions_by_node(
    payload: TransitionDisableRequest,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Lock all transitions related to the given node."""
    result = await db.execute(select(Node).where(Node.slug == payload.slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    stmt = select(NodeTransition).where(
        or_(
            NodeTransition.from_node_id == node.id,
            NodeTransition.to_node_id == node.id,
        )
    )
    res = await db.execute(stmt)
    transitions = res.scalars().all()
    for t in transitions:
        t.type = NodeTransitionType.locked
    await db.commit()
    await navcache.invalidate_navigation_by_node(node.slug)
    await navcache.invalidate_compass_by_node(node.slug)
    cache_invalidate("nav", reason="transition_disable", key=node.slug)
    cache_invalidate("comp", reason="transition_disable", key=node.slug)
    logger.info(
        "admin_action",
        extra={
            "action": "disable_transitions_by_node",
            "actor_id": str(current_user.id),
            "node_slug": node.slug,
            "count": len(transitions),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"disabled": len(transitions)}


@router.get("/tags", response_model=list[AdminTagOut], summary="List tags")
async def list_tags_admin(
    search: str | None = None,
    hidden: bool | None = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Return tags with optional search and pagination."""
    stmt = select(Tag, func.count(NodeTag.node_id).label("count")).join(
        NodeTag, Tag.id == NodeTag.tag_id, isouter=True
    )
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Tag.slug.ilike(pattern), Tag.name.ilike(pattern)))
    if hidden is not None:
        stmt = stmt.where(Tag.is_hidden == hidden)
    stmt = stmt.group_by(Tag.id).order_by(Tag.slug)
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        AdminTagOut(
            slug=t.slug,
            name=t.name,
            is_hidden=t.is_hidden,
            uses_count=c,
        )
        for t, c in rows
    ]


@router.post("/tags", response_model=AdminTagOut, summary="Create tag")
async def create_tag_admin(
    payload: TagCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag. Example: `{ "slug": "demo", "name": "Demo" }`."""
    existing = await db.execute(select(Tag).where(Tag.slug == payload.slug))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Tag with this slug already exists")
    tag = Tag(slug=payload.slug, name=payload.name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    logger.info(
        "admin_action",
        extra={
            "action": "create_tag",
            "actor_id": str(current_user.id),
            "slug": tag.slug,
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return AdminTagOut(
        slug=tag.slug,
        name=tag.name,
        is_hidden=tag.is_hidden,
        uses_count=0,
    )


@router.patch("/tags/{slug}", response_model=AdminTagOut, summary="Update tag")
async def update_tag_admin(
    slug: str,
    payload: TagUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Rename or hide/unhide a tag."""
    result = await db.execute(select(Tag).where(Tag.slug == slug))
    tag = result.scalars().first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if payload.name is not None:
        tag.name = payload.name
    if payload.hidden is not None:
        tag.is_hidden = payload.hidden
    await db.commit()
    await db.refresh(tag)
    res = await db.execute(
        select(func.count(NodeTag.node_id)).where(NodeTag.tag_id == tag.id)
    )
    count = res.scalar() or 0
    logger.info(
        "admin_action",
        extra={
            "action": "update_tag",
            "actor_id": str(current_user.id),
            "slug": slug,
            "payload": payload.model_dump(exclude_none=True),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return AdminTagOut(
        slug=tag.slug,
        name=tag.name,
        is_hidden=tag.is_hidden,
        uses_count=count,
    )


@router.post("/tags/merge", summary="Merge tags")
async def merge_tags_admin(
    payload: TagMerge,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Merge one tag into another, reassigning all node links."""
    if payload.from_slug == payload.to_slug:
        raise HTTPException(status_code=400, detail="Cannot merge the same tag")
    res = await db.execute(
        select(Tag).where(Tag.slug.in_([payload.from_slug, payload.to_slug]))
    )
    tags = {t.slug: t for t in res.scalars().all()}
    from_tag = tags.get(payload.from_slug)
    to_tag = tags.get(payload.to_slug)
    if not from_tag or not to_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    res = await db.execute(select(NodeTag).where(NodeTag.tag_id == from_tag.id))
    nodetags = res.scalars().all()
    node_ids: set[UUID] = {nt.node_id for nt in nodetags}
    for nt in nodetags:
        exists = await db.execute(
            select(NodeTag).where(
                NodeTag.node_id == nt.node_id, NodeTag.tag_id == to_tag.id
            )
        )
        if exists.scalars().first():
            await db.delete(nt)
        else:
            nt.tag_id = to_tag.id
    await db.delete(from_tag)
    await db.commit()
    if node_ids:
        res = await db.execute(select(Node.slug).where(Node.id.in_(node_ids)))
        slugs = [row[0] for row in res.all()]
        for s in slugs:
            await navcache.invalidate_navigation_by_node(s)
            await navcache.invalidate_compass_by_node(s)
            cache_invalidate("nav", reason="tag_merge", key=s)
            cache_invalidate("comp", reason="tag_merge", key=s)
    logger.info(
        "admin_action",
        extra={
            "action": "merge_tags",
            "actor_id": str(current_user.id),
            "from_slug": payload.from_slug,
            "to_slug": payload.to_slug,
            "moved": len(nodetags),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"moved": len(nodetags)}


@router.post("/tags/{slug}/detach", summary="Detach tag from nodes")
async def detach_tag_admin(
    slug: str,
    payload: TagDetachRequest,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Detach a tag from specified nodes or from all if `node_ids` omitted."""
    result = await db.execute(select(Tag).where(Tag.slug == slug))
    tag = result.scalars().first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    stmt = select(NodeTag).where(NodeTag.tag_id == tag.id)
    if payload.node_ids:
        stmt = stmt.where(NodeTag.node_id.in_(payload.node_ids))
    res = await db.execute(stmt)
    nodetags = res.scalars().all()
    node_ids: set[UUID] = {nt.node_id for nt in nodetags}
    for nt in nodetags:
        await db.delete(nt)
    await db.commit()
    if node_ids:
        res = await db.execute(select(Node.slug).where(Node.id.in_(node_ids)))
        slugs = [row[0] for row in res.all()]
        for s in slugs:
            await navcache.invalidate_navigation_by_node(s)
            await navcache.invalidate_compass_by_node(s)
            cache_invalidate("nav", reason="tag_detach", key=s)
            cache_invalidate("comp", reason="tag_detach", key=s)
    logger.info(
        "admin_action",
        extra={
            "action": "detach_tag",
            "actor_id": str(current_user.id),
            "slug": slug,
            "detached": len(nodetags),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"detached": len(nodetags)}
