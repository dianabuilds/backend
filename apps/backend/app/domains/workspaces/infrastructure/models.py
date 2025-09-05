from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.providers.db.adapters import JSONB, UUID
from app.providers.db.base import Base
from app.schemas.workspaces import WorkspaceRole, WorkspaceType


class Workspace(Base):
    __tablename__ = "workspaces"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)
    name = sa.Column(sa.String, nullable=False)
    slug = sa.Column(sa.String, nullable=False, unique=True, index=True)
    owner_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=False, index=True)
    settings_json = sa.Column(JSONB, nullable=False, server_default=sa.text("'{}'"))
    type = sa.Column(
        sa.Enum(
            WorkspaceType,
            name="workspace_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        server_default="team",
        default=WorkspaceType.team,
    )
    is_system = sa.Column(
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
        default=False,
    )
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, index=True)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship(
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (sa.Index("ix_workspace_members_workspace_id_role", "workspace_id", "role"),)

    workspace_id = sa.Column(UUID(), sa.ForeignKey("workspaces.id"), primary_key=True)
    user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), primary_key=True)
    role = sa.Column(sa.Enum(WorkspaceRole, name="workspace_role"), nullable=False)
    permissions_json = sa.Column(JSONB, nullable=False, server_default=sa.text("'{}'"))

    workspace = relationship("Workspace", back_populates="members")
