from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.core.db.adapters import UUID, JSONB
from app.schemas.workspaces import WorkspaceRole


class Workspace(Base):
    __tablename__ = "workspaces"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)
    name = sa.Column(sa.String, nullable=False)
    slug = sa.Column(sa.String, nullable=False, unique=True, index=True)
    owner_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=False)
    settings_json = sa.Column(JSONB, nullable=False, server_default=sa.text("'{}'"))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id = sa.Column(UUID(), sa.ForeignKey("workspaces.id"), primary_key=True)
    user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), primary_key=True)
    role = sa.Column(
        sa.Enum(WorkspaceRole, name="workspace_role"), nullable=False
    )
    permissions_json = sa.Column(JSONB, nullable=False, server_default=sa.text("'{}'"))

    workspace = relationship("Workspace", back_populates="members")
