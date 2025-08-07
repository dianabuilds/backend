from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import (
    ensure_can_post,
    get_current_user,
    require_premium,
)
from app.db.session import get_db
from app.models.node import Node
from app.models.user import User
from app.schemas.node import NodeCreate, NodeOut, NodeUpdate, ReactionUpdate

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("", response_model=dict)
async def create_node(
    payload: NodeCreate,
    current_user: User = Depends(ensure_can_post),
    db: AsyncSession = Depends(get_db),
):
    node = Node(
        title=payload.title,
        content_format=payload.content_format,
        content=payload.content,
        media=payload.media or [],
        tags=payload.tags or [],
        is_public=payload.is_public,
        meta=payload.meta or {},
        premium_only=payload.premium_only if payload.premium_only is not None else False,
        nft_required=payload.nft_required,
        ai_generated=payload.ai_generated if payload.ai_generated is not None else False,
        author_id=current_user.id,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return {"slug": node.slug}


@router.get("/{slug}", response_model=NodeOut)
async def read_node(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug, Node.is_visible == True))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if not node.is_public and node.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this node")
    if node.premium_only:
        await require_premium(current_user)
    node.views += 1
    await db.commit()
    await db.refresh(node)
    return node


@router.get("/{slug}/echo", dependencies=[Depends(require_premium)])
async def view_echo(slug: str):
    return {"slug": slug}


@router.patch("/{slug}", response_model=NodeOut)
async def update_node(
    slug: str,
    payload: NodeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this node")
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(node, field, value)
    node.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(node)
    return node


@router.delete("/{slug}")
async def delete_node(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this node")
    await db.delete(node)
    await db.commit()
    return {"message": "Node deleted"}


@router.post("/{slug}/reactions", response_model=dict)
async def update_reactions(
    slug: str,
    payload: ReactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    reactions = node.reactions or {}
    current = reactions.get(payload.reaction, 0)
    if payload.action == "add":
        reactions[payload.reaction] = current + 1
    elif payload.action == "remove" and current > 0:
        reactions[payload.reaction] = current - 1
        if reactions[payload.reaction] <= 0:
            reactions.pop(payload.reaction)
    node.reactions = reactions
    await db.commit()
    await db.refresh(node)
    return {"reactions": node.reactions}
