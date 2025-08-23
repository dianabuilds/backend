from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String
from . import Base
from .adapters import JSONB, UUID


class ConfigVersion(Base):
    __tablename__ = "config_versions"

    id = Column(UUID(), primary_key=True, default=uuid4)
    type = Column(String, nullable=False)  # e.g. "relevance"
    version = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="active")  # draft|active|archived
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    parent_id = Column(UUID(), nullable=True)
    comment = Column(String, nullable=True)
    checksum = Column(String, nullable=True)


class SearchRelevanceActive(Base):
    __tablename__ = "search_relevance_active"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False, default=1)
    payload = Column(JSONB, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_by = Column(UUID(), nullable=True)
