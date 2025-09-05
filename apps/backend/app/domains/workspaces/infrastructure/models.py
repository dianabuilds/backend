from __future__ import annotations

from sqlalchemy.orm import relationship

from app.domains.accounts.infrastructure.models import Account, AccountMember


class Workspace(Account):
    __tablename__ = Account.__tablename__
    __table__ = Account.__table__

    members = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan",
        overlaps="account",
    )


class WorkspaceMember(AccountMember):
    __tablename__ = AccountMember.__tablename__
    __table__ = AccountMember.__table__

    workspace = relationship(
        "Workspace",
        back_populates="members",
        overlaps="account,members",
    )

    @property
    def workspace_id(self):
        return self.account_id

    @workspace_id.setter
    def workspace_id(self, value):  # type: ignore[no-untyped-def]
        self.account_id = value

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        if "workspace_id" in kwargs and "account_id" not in kwargs:
            kwargs["account_id"] = kwargs.pop("workspace_id")
        if "workspace" in kwargs and "account" not in kwargs:
            kwargs["account"] = kwargs.pop("workspace")
        super().__init__(*args, **kwargs)
