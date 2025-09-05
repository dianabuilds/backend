from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class EchoTrace(Base):
    __tablename__ = "echo_trace"
    __table_args__ = (Index("idx_echo_from_node", "from_node_id"),)

    id = Column(UUID(), primary_key=True, default=uuid4)
    from_node_id = Column(BigInteger, ForeignKey("nodes.id"))
    to_node_id = Column(BigInteger, ForeignKey("nodes.id"))
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    source = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    from_node = relationship("Node", foreign_keys=[from_node_id])
    to_node = relationship("Node", foreign_keys=[to_node_id])
