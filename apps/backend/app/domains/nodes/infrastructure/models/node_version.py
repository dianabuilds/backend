from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String

from app.kernel.db import JSONB, UUID, Base


class NodeVersion(Base):
    __tablename__ = "node_versions"

    node_id = Column(BigInteger, ForeignKey("nodes.id"), primary_key=True)
    version = Column(Integer, primary_key=True)
    title = Column(String, nullable=True)
    meta = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)

