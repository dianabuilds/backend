from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa

from app.kernel.db import JSONB, UUID, Base


class MediaAsset(Base):
    """Stored media file metadata."""

    __tablename__ = "media_assets"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)
    profile_id = sa.Column(UUID(), nullable=True, index=True)
    url = sa.Column(sa.String, nullable=False)
    type = sa.Column(sa.String, nullable=False)
    metadata_json = sa.Column(JSONB, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

