from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.providers.db.adapters import JSONB, UUID, VECTOR
from app.providers.db.base import Base
from app.schemas.nodes_common import Status, Visibility


def generate_slug() -> str:
    seed = f"{datetime.utcnow().isoformat()}-{uuid4()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


class Node(Base):
    __tablename__ = "nodes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Legacy: account-based scoping (now optional during transition to profiles)
    account_id = Column(BigInteger, ForeignKey("accounts.id"), nullable=True, index=True)
    slug = Column(String, index=True, nullable=False, default=generate_slug)
    title = Column(String, nullable=True)
    embedding_vector = Column(MutableList.as_mutable(VECTOR(settings.embedding.dim)), nullable=True)
    author_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    views = Column(Integer, default=0)
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
        "Tag",
        secondary=NodeTag.__table__,
        back_populates="nodes",
        lazy="selectin",
    )

    __table_args__ = (
        # Legacy account-scoped indexes (kept for backward compatibility during transition)
        Index("ix_nodes_account_id_slug", "account_id", "slug", unique=True),
        Index("ix_nodes_account_id_created_at", "account_id", "created_at"),
        # New profile/user-scoped indexes
        Index("uq_nodes_author_id_slug", "author_id", "slug", unique=True),
        Index("ix_nodes_author_id_created_at", "author_id", "created_at"),
    )

    # ``workspace_id`` previously mirrored ``account_id`` for backwards
    # compatibility.  Callers should now pass ``account_id`` directly.

    # ------------------------------------------------------------------
    # Compatibility properties for legacy fields removed from the schema.
    # These fields were historically stored as separate columns but now
    # live inside the ``meta`` JSONB blob.  Exposing them as properties
    # keeps older code and admin tooling functional while allowing new
    # records to persist data in ``meta``.

    def _meta_dict(self) -> dict:
        """Return ``meta`` as a dictionary, tolerating legacy string values.

        Some historical rows stored JSON as a plain string in the ``meta``
        column. Accessors below normalise such values to a dict to avoid
        ``AttributeError: 'str' object has no attribute 'get'``.
        """
        m = self.meta
        if isinstance(m, dict):
            return m
        if isinstance(m, str):
            # Memoize parsed meta to avoid repeated json.loads on every accessor
            cache = getattr(self, "_meta_cache", None)
            if isinstance(cache, dict) and cache.get("raw") is m:
                parsed = cache.get("parsed")
                if isinstance(parsed, dict):
                    return parsed
            try:
                import json

                parsed = json.loads(m)
                if isinstance(parsed, dict):
                    try:
                        self._meta_cache = {"raw": m, "parsed": parsed}
                    except Exception:
                        # instance may be in a state where setattr is blocked; ignore
                        pass
                    return parsed
                return {}
            except Exception:
                return {}
        return {}

    @property
    def content(self) -> dict | list:
        """Return node content stored inside ``meta``."""
        return self._meta_dict().get("content", {})

    @content.setter
    def content(self, value: dict | list) -> None:
        meta = dict(self._meta_dict())
        meta["content"] = value
        self.meta = meta

    @property
    def cover_url(self) -> str | None:
        return self._meta_dict().get("cover_url")

    @cover_url.setter
    def cover_url(self, value: str | None) -> None:
        meta = dict(self._meta_dict())
        meta["cover_url"] = value
        self.meta = meta

    @property
    def coverUrl(self) -> str | None:
        return self.cover_url

    @coverUrl.setter
    def coverUrl(self, value: str | None) -> None:
        self.cover_url = value

    @property
    def media(self) -> list[str]:
        return self._meta_dict().get("media", [])

    @media.setter
    def media(self, value: list[str]) -> None:
        meta = dict(self._meta_dict())
        meta["media"] = value
        self.meta = meta

    @property
    def reactions(self) -> dict:
        return self._meta_dict().get("reactions", {})

    @reactions.setter
    def reactions(self, value: dict) -> None:
        meta = dict(self._meta_dict())
        meta["reactions"] = value
        self.meta = meta

    @property
    def is_public(self) -> bool:
        return self.visibility == Visibility.public

    @is_public.setter
    def is_public(self, value: bool) -> None:
        self.visibility = Visibility.public if value else Visibility.private

    @property
    def tag_slugs(self) -> list[str]:
        return [t.slug for t in self.tags] if self.tags else []
