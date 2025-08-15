from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.node import Node
from app.schemas.node import NodeCreate, NodeUpdate
from .tag_repository import TagRepository


class NodeRepository:
    """Data access layer for :class:`Node` entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tags = TagRepository(session)

    async def get_by_slug(self, slug: str) -> Node | None:
        result = await self.session.execute(
            select(Node).where(Node.slug == slug, Node.is_visible == True)
        )
        return result.scalars().first()

    async def get_by_id(self, node_id: UUID) -> Node | None:
        return await self.session.get(Node, node_id)

    async def create(self, payload: NodeCreate, author_id: UUID) -> Node:
        tag_objs = (
            await self.tags.get_or_create_many(payload.tags) if payload.tags else []
        )
        node = Node(
            title=payload.title,
            content=payload.content,
            cover_url=payload.cover_url or (payload.media[0] if payload.media else None),
            media=payload.media or [],
            is_public=payload.is_public,
            is_visible=payload.is_visible,
            allow_feedback=payload.allow_feedback,
            is_recommendable=payload.is_recommendable,
            meta=payload.meta or {},
            premium_only=payload.premium_only or False,
            nft_required=payload.nft_required,
            ai_generated=payload.ai_generated or False,
            author_id=author_id,
        )
        if tag_objs:
            node.tags = tag_objs
        self.session.add(node)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(node, attribute_names=["id", "slug"])
        return node

    async def set_tags(self, node: Node, tags: Sequence[str]) -> Node:
        tag_objs = await self.tags.get_or_create_many(tags)
        node.tags = tag_objs
        node.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def increment_views(self, node: Node) -> Node:
        node.views += 1
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def update(self, node: Node, payload: NodeUpdate) -> Node:
        data = payload.model_dump(exclude_unset=True)
        tags = data.pop("tags", None)
        for field, value in data.items():
            setattr(node, field, value)
        if tags is not None:
            node.tags = await self.tags.get_or_create_many(tags)
        node.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def delete(self, node: Node) -> None:
        await self.session.delete(node)
        await self.session.commit()

    async def update_reactions(self, node: Node, reaction: str, action: str) -> Node:
        reactions = node.reactions or {}
        current = reactions.get(reaction, 0)
        if action == "add":
            reactions[reaction] = current + 1
        elif action == "remove" and current > 0:
            new_val = current - 1
            if new_val > 0:
                reactions[reaction] = new_val
            else:
                reactions.pop(reaction, None)
        node.reactions = reactions
        await self.session.commit()
        await self.session.refresh(node)
        return node
