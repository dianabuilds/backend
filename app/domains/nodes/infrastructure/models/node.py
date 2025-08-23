from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.core.db.adapters import ARRAY, JSONB, UUID, VECTOR
from app.core.db.base import Base
from app.schemas.nodes_common import Status, Visibility


def generate_slug() -> str:
    seed = f"{datetime.utcnow().isoformat()}-{uuid4()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


class Node(Base):
    __tablename__ = "nodes"

    id = Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = Column(
        UUID(), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    slug = Column(
        String, unique=True, index=True, nullable=False, default=generate_slug
    )
    title = Column(String, nullable=True)
    content = Column(JSONB, nullable=False)
    cover_url = Column(String, nullable=True)
    media = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    embedding_vector = Column(
        MutableList.as_mutable(VECTOR(settings.embedding.dim)), nullable=True
    )
    author_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    views = Column(Integer, default=0)
    # ``reactions`` used to rely on ``MutableDict`` for change tracking which
    # enforces that the underlying value is always a mapping.  In production some
    # records ended up storing reactions as plain JSON strings which caused
    # SQLAlchemy to raise "Attribute 'reactions' does not accept objects of type
    # <class 'str'>" when loading rows.  Using the plain ``JSONB`` type allows us
    # to gracefully handle such legacy values; the application level schema
    # already normalises strings to dictionaries.
    reactions = Column(JSONB, default=dict)
    is_public = Column(Boolean, default=False, index=True)
    is_visible = Column(Boolean, default=True, index=True)
    allow_feedback = Column(Boolean, default=True, index=True)
    is_recommendable = Column(Boolean, default=True, index=True)
    popularity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ``meta`` previously used ``MutableDict`` which rejected rows where the
    # column contained a JSON string.  Such legacy records caused SQLAlchemy to
    # raise "Attribute 'meta' does not accept objects of type <class 'str'>" on
    # load.  Using the plain ``JSONB`` type allows those rows to be loaded and
    # normalised at the schema level.
    meta = Column(JSONB, default=dict)

    premium_only = Column(Boolean, default=False)
    nft_required = Column(String, nullable=True)
    ai_generated = Column(Boolean, default=False)

    status = Column(
        SAEnum(Status, name="content_status"),
        nullable=False,
        server_default=Status.draft.value,
    )
    version = Column(Integer, nullable=False, server_default="1")
    visibility = Column(
        SAEnum(Visibility, name="content_visibility"),
        nullable=False,
        server_default=Visibility.private.value,
    )
    created_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)

    tags = relationship(
        "Tag", secondary="node_tags", back_populates="nodes", lazy="selectin"
    )

    @property
    def tag_slugs(self) -> list[str]:
        return [t.slug for t in self.tags]
