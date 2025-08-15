from datetime import datetime
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import assert_seniority_over, get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.models.moderation import ContentModeration, UserRestriction
from app.models.node import Node
from app.models.user import User
from app.schemas.moderation import (
    ContentHide,
    HiddenNodeOut,
    RestrictionCreate,
    RestrictionOut,
)

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/moderation",
    tags=["moderation"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)

logger = logging.getLogger(__name__)


@router.post("/users/{user_id}/ban", summary="Ban user")
async def ban_user(
    user_id: UUID,
    payload: RestrictionCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Completely block a user from accessing the platform."""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    assert_seniority_over(target_user, current_user)
    restriction = UserRestriction(
        user_id=user_id,
        type="ban",
        reason=payload.reason,
        expires_at=payload.expires_at,
        issued_by=current_user.id,
    )
    db.add(restriction)
    await db.commit()
    await db.refresh(restriction)
    logger.info(
        "admin_action",
        extra={
            "action": "ban_user",
            "actor_id": str(current_user.id),
            "target_user_id": str(user_id),
            "payload": payload.model_dump(),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"id": restriction.id}


@router.post(
    "/users/{user_id}/restrict-posting",
    summary="Restrict user posting",
)
async def restrict_posting(
    user_id: UUID,
    payload: RestrictionCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Temporarily forbid a user from creating new content."""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    assert_seniority_over(target_user, current_user)
    restriction = UserRestriction(
        user_id=user_id,
        type="post_restrict",
        reason=payload.reason,
        expires_at=payload.expires_at,
        issued_by=current_user.id,
    )
    db.add(restriction)
    await db.commit()
    await db.refresh(restriction)
    logger.info(
        "admin_action",
        extra={
            "action": "restrict_posting",
            "actor_id": str(current_user.id),
            "target_user_id": str(user_id),
            "payload": payload.model_dump(),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"id": restriction.id}


@router.delete("/restrictions/{restriction_id}", summary="Remove restriction")
async def remove_restriction(
    restriction_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Delete an active restriction entry."""
    restriction = await db.get(UserRestriction, restriction_id)
    if not restriction:
        raise HTTPException(status_code=404, detail="Restriction not found")
    await db.delete(restriction)
    await db.commit()
    return {"message": "Restriction removed"}


@router.post("/nodes/{slug}/hide", summary="Hide node")
async def hide_node(
    slug: str,
    payload: ContentHide,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Hide a node from public view for moderation reasons."""
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    author = await db.get(User, node.author_id)
    if author:
        assert_seniority_over(author, current_user)
    node.is_visible = False
    moderation = ContentModeration(
        node_id=node.id,
        reason=payload.reason,
        hidden_by=current_user.id,
    )
    db.add(moderation)
    await db.commit()
    logger.info(
        "admin_action",
        extra={
            "action": "hide_node",
            "actor_id": str(current_user.id),
            "node_id": str(node.id),
            "payload": payload.model_dump(),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"message": "Node hidden"}


@router.get(
    "/hidden-nodes",
    response_model=list[HiddenNodeOut],
    summary="List hidden nodes",
)
async def list_hidden_nodes(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Return nodes currently hidden by moderators."""
    stmt = (
        select(Node, ContentModeration)
        .join(ContentModeration, ContentModeration.node_id == Node.id)
        .where(Node.is_visible == False)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        HiddenNodeOut(
            slug=node.slug,
            title=node.title,
            reason=mod.reason,
            hidden_by=mod.hidden_by,
            hidden_at=mod.created_at,
        )
        for node, mod in rows
    ]


@router.post("/nodes/{slug}/restore", summary="Restore node")
async def restore_node(
    slug: str,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Make a previously hidden node visible again."""
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    author = await db.get(User, node.author_id)
    if author:
        assert_seniority_over(author, current_user)
    node.is_visible = True
    mod_result = await db.execute(
        select(ContentModeration).where(ContentModeration.node_id == node.id)
    )
    moderations = mod_result.scalars().all()
    for mod in moderations:
        await db.delete(mod)
    await db.commit()
    logger.info(
        "admin_action",
        extra={
            "action": "restore_node",
            "actor_id": str(current_user.id),
            "node_id": str(node.id),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"message": "Node restored"}


@router.get(
    "/restrictions",
    response_model=list[RestrictionOut],
    summary="List restrictions",
)
async def list_restrictions(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Get all active user restrictions."""
    now = datetime.utcnow()
    stmt = select(UserRestriction).where(
        (UserRestriction.expires_at == None) | (UserRestriction.expires_at > now)
    )
    result = await db.execute(stmt)
    restrictions = result.scalars().all()
    return restrictions
