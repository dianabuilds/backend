from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from app.core.db.base import Base
from app.core.db.adapters import UUID, JSONB


class MediaAsset(Base):
    """Stored media file metadata."""

    __tablename__ = "media_assets"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = sa.Column(UUID(), sa.ForeignKey("workspaces.id"), nullable=False)
    url = sa.Column(sa.String, nullable=False)
    type = sa.Column(sa.String, nullable=False)
    metadata_json = sa.Column(JSONB, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

