from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_db, require_role
from app.models.moderation import ContentModeration, UserRestriction
from app.models.node import Node
from app.models.user import User
from app.schemas.moderation import (
    ContentHide,
    HiddenNodeOut,
    RestrictionCreate,
    RestrictionOut,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: UUID,
    payload: RestrictionCreate,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    if not await db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
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
    return {"id": restriction.id}


@router.post("/users/{user_id}/restrict-posting")
async def restrict_posting(
    user_id: UUID,
    payload: RestrictionCreate,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    if not await db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
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
    return {"id": restriction.id}


@router.delete("/restrictions/{restriction_id}")
async def remove_restriction(
    restriction_id: UUID,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    restriction = await db.get(UserRestriction, restriction_id)
    if not restriction:
        raise HTTPException(status_code=404, detail="Restriction not found")
    await db.delete(restriction)
    await db.commit()
    return {"message": "Restriction removed"}


@router.post("/nodes/{slug}/hide")
async def hide_node(
    slug: str,
    payload: ContentHide,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    node.is_visible = False
    moderation = ContentModeration(
        node_id=node.id,
        reason=payload.reason,
        hidden_by=current_user.id,
    )
    db.add(moderation)
    await db.commit()
    return {"message": "Node hidden"}


@router.get("/hidden-nodes", response_model=list[HiddenNodeOut])
async def list_hidden_nodes(
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
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


@router.post("/nodes/{slug}/restore")
async def restore_node(
    slug: str,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    node.is_visible = True
    mod_result = await db.execute(
        select(ContentModeration).where(ContentModeration.node_id == node.id)
    )
    moderations = mod_result.scalars().all()
    for mod in moderations:
        await db.delete(mod)
    await db.commit()
    return {"message": "Node restored"}


@router.get("/restrictions", response_model=list[RestrictionOut])
async def list_restrictions(
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    stmt = select(UserRestriction).where(
        (UserRestriction.expires_at == None) | (UserRestriction.expires_at > now)
    )
    result = await db.execute(stmt)
    restrictions = result.scalars().all()
    return restrictions
