from __future__ import annotations

from typing import List, Sequence
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app.providers.db.session import get_engine
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.models import Tag
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from apps.backendDDD.domains.product.nodes.application.ports import NodeDTO
from app.schemas.nodes_common import Visibility


class SANodesRepo:
    def __init__(self) -> None:
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def _to_dto(self, s: Session, node: Node) -> NodeDTO:
        # Collect tag slugs via NodeTag -> Tag
        rows = s.execute(
            sa.select(Tag.slug)
            .select_from(NodeTag)
            .join(Tag, Tag.id == NodeTag.tag_id)
            .where(NodeTag.node_id == node.id)
        ).all()
        tags = [r[0] for r in rows]
        is_public = node.visibility == Visibility.public
        return NodeDTO(id=int(node.id), author_id=str(node.author_id), title=node.title, tags=tags, is_public=is_public)

    def get(self, node_id: int) -> NodeDTO | None:
        with self._Session() as s:  # type: Session
            n = s.get(Node, int(node_id))
            if not n:
                return None
            return self._to_dto(s, n)

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0) -> List[NodeDTO]:
        with self._Session() as s:
            try:
                au = uuid.UUID(str(author_id))
            except Exception:
                return []
            q = s.execute(
                sa.select(Node)
                .where(Node.author_id == au)
                .order_by(Node.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return [self._to_dto(s, row[0]) for row in q.all()]

    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        with self._Session() as s:
            n = s.get(Node, int(node_id))
            if not n:
                raise ValueError("node not found")
            # Resolve tag IDs
            if tags:
                res = s.execute(sa.select(Tag.id, Tag.slug).where(Tag.slug.in_(list(tags))))
                by_slug = {slug: tid for (tid, slug) in ((r[0], r[1]) for r in res.all())}
                missing = [t for t in tags if t not in by_slug]
                if missing:
                    # Create missing tags with name=slug
                    for m in missing:
                        t = Tag(slug=m, name=m)
                        s.add(t)
                    s.commit()
                    res = s.execute(sa.select(Tag.id, Tag.slug).where(Tag.slug.in_(list(tags))))
                    by_slug = {slug: tid for (tid, slug) in ((r[0], r[1]) for r in res.all())}
                tag_ids = [by_slug[t] for t in tags]
            else:
                tag_ids = []
            # Delete existing links
            s.execute(sa.delete(NodeTag).where(NodeTag.node_id == n.id))
            # Insert new links
            for tid in tag_ids:
                s.add(NodeTag(node_id=n.id, tag_id=tid))
            s.commit()
            return self._to_dto(s, n)
