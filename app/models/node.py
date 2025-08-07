from __future__ import annotations

from datetime import datetime
from enum import Enum
import hashlib
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
)
from .adapters import ARRAY, JSONB, UUID
from sqlalchemy.ext.mutable import MutableDict, MutableList

from . import Base


class ContentFormat(str, Enum):
    text = "text"
    markdown = "markdown"
    rich_json = "rich_json"
    html = "html"
    image_set = "image_set"


def generate_slug() -> str:
    seed = f"{datetime.utcnow().isoformat()}-{uuid4()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


class Node(Base):
    __tablename__ = "nodes"

    id = Column(UUID(), primary_key=True, default=uuid4)
    slug = Column(String, unique=True, index=True, nullable=False, default=generate_slug)
    title = Column(String, nullable=True)
    content_format = Column(SAEnum(ContentFormat), nullable=False)
    content = Column(JSONB, nullable=False)
    media = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    tags = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    author_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    views = Column(Integer, default=0)
    reactions = Column(MutableDict.as_mutable(JSONB), default=dict)
    is_public = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = Column(MutableDict.as_mutable(JSONB), default=dict)

    premium_only = Column(Boolean, default=False)
    nft_required = Column(String, nullable=True)
    ai_generated = Column(Boolean, default=False)
