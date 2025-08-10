from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.api.deps import (
    assert_owner_or_role,
    assert_seniority_over,
    get_current_user,
    require_role,
)
from app.db.session import get_db
from app.models.user import User
from app.models.node import Node
from app.models.tag import Tag
from app.schemas.user import UserPremiumUpdate, UserRoleUpdate
from app.schemas.node import NodeOut, NodeBulkOperation
from app.engine.embedding import update_node_embedding

router = APIRouter(prefix="/admin", tags=["admin"])

logger = logging.getLogger(__name__)


@router.post("/users/{user_id}/premium", summary="Set user premium status")
async def set_user_premium(
    user_id: UUID,
    payload: UserPremiumUpdate,
    current_user: User = Depends(require_role("admin")),
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
    current_user: User = Depends(require_role("admin")),
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
    stmt = select(Node).options(selectinload(Node.tags))
    if current_user.role not in {"moderator", "admin"}:
        stmt = stmt.where(Node.author_id == current_user.id)
    if author:
        stmt = stmt.where(Node.author_id == author)
    if is_public is not None:
        stmt = stmt.where(Node.is_public == is_public)
    if premium_only is not None:
        stmt = stmt.where(Node.premium_only == premium_only)
    if recommendable is not None:
        stmt = stmt.where(Node.is_recommendable == recommendable)
    if date_from:
        stmt = stmt.where(Node.updated_at >= date_from)
    if date_to:
        stmt = stmt.where(Node.updated_at <= date_to)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Node.title).like(like),
                func.lower(Node.slug).like(like),
            )
        )
    if tags:
        slugs = [t.strip() for t in tags.split(",") if t.strip()]
        if slugs:
            stmt = stmt.join(Node.tags).where(Tag.slug.in_(slugs))
            if match == "all":
                stmt = stmt.group_by(Node.id).having(func.count(Tag.id) == len(slugs))
            else:
                stmt = stmt.distinct()
    stmt = stmt.order_by(Node.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


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
    current_user: User = Depends(require_role("moderator")),
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
