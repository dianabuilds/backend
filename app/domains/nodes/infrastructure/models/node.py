from __future__ import annotations

from datetime import datetime
import hashlib
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Float,
)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.core.db.adapters import ARRAY, JSONB, UUID, VECTOR
from app.core.config import settings


def generate_slug() -> str:
    seed = f"{datetime.utcnow().isoformat()}-{uuid4()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


class Node(Base):
    __tablename__ = "nodes"

    id = Column(UUID(), primary_key=True, default=uuid4)
    slug = Column(String, unique=True, index=True, nullable=False, default=generate_slug)
    title = Column(String, nullable=True)
    content = Column(JSONB, nullable=False)
    cover_url = Column(String, nullable=True)
    media = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    embedding_vector = Column(
        MutableList.as_mutable(VECTOR(settings.embedding.dim)), nullable=True
    )
    author_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    views = Column(Integer, default=0)
    reactions = Column(MutableDict.as_mutable(JSONB), default=dict)
    is_public = Column(Boolean, default=False, index=True)
    is_visible = Column(Boolean, default=True, index=True)
    allow_feedback = Column(Boolean, default=True, index=True)
    is_recommendable = Column(Boolean, default=True, index=True)
    popularity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = Column(MutableDict.as_mutable(JSONB), default=dict)

    premium_only = Column(Boolean, default=False)
    nft_required = Column(String, nullable=True)
    ai_generated = Column(Boolean, default=False)

    tags = relationship("Tag", secondary="node_tags", back_populates="nodes", lazy="selectin")

    @property
    def tag_slugs(self) -> list[str]:
        return [t.slug for t in self.tags]
