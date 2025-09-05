from __future__ import annotations

import builtins
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.schemas.accounts import AccountRole, AccountSettings

from .models import Account, AccountMember

logger = logging.getLogger("app.audit.workspace_member")


class AccountDAO:
    """Data access helpers for :class:`Account` objects."""

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        name: str,
        slug: str,
        owner_user_id: UUID,
        settings: AccountSettings | None = None,
    ) -> Account:
        account = Account(
            name=name,
            slug=slug,
            owner_user_id=owner_user_id,
            settings_json=settings.model_dump() if settings else {},
        )
        db.add(account)
        await db.flush()
        return account

    @staticmethod
    async def get(db: AsyncSession, account_id: int) -> Account | None:
        return await db.get(Account, account_id)

    @staticmethod
    async def list_for_user(db: AsyncSession, user_id: UUID) -> list[Account]:
        stmt = (
            select(Account)
            .join(AccountMember)
            .where(AccountMember.user_id == user_id)
            .order_by(Account.name)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        account: Account,
        *,
        name: str | None = None,
        slug: str | None = None,
        settings: AccountSettings | None = None,
    ) -> Account:
        if name is not None:
            account.name = name
        if slug is not None:
            account.slug = slug
        if settings is not None:
            account.settings_json = settings.model_dump()
        await db.flush()
        return account

    @staticmethod
    async def delete(db: AsyncSession, account: Account) -> None:
        await db.delete(account)
        await db.flush()


class AccountMemberDAO:
    @staticmethod
    async def get(db: AsyncSession, *, account_id: int, user_id: UUID) -> AccountMember | None:
        stmt = select(AccountMember).where(
            AccountMember.account_id == account_id,
            AccountMember.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def add(
        db: AsyncSession, *, account_id: int, user_id: UUID, role: AccountRole
    ) -> AccountMember:
        member = AccountMember(account_id=account_id, user_id=user_id, role=role)
        db.add(member)
        await db.flush()
        logger.info(
            "account_member.add",
            extra={
                "account_id": str(account_id),
                "user_id": str(user_id),
                "role": role.value if hasattr(role, "value") else str(role),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
        return member

    @staticmethod
    async def update_role(
        db: AsyncSession,
        *,
        account_id: int,
        user_id: UUID,
        role: AccountRole,
    ) -> AccountMember | None:
        member = await AccountMemberDAO.get(db, account_id=account_id, user_id=user_id)
        if member:
            old_role = member.role
            member.role = role
            await db.flush()
            logger.info(
                "account_member.update_role",
                extra={
                    "account_id": str(account_id),
                    "user_id": str(user_id),
                    "old_role": (old_role.value if hasattr(old_role, "value") else str(old_role)),
                    "new_role": role.value if hasattr(role, "value") else str(role),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        return member

    @staticmethod
    async def remove(db: AsyncSession, *, account_id: int, user_id: UUID) -> None:
        member = await AccountMemberDAO.get(db, account_id=account_id, user_id=user_id)
        if member:
            role = member.role
            await db.delete(member)
            await db.flush()
            logger.info(
                "account_member.remove",
                extra={
                    "account_id": str(account_id),
                    "user_id": str(user_id),
                    "role": role.value if hasattr(role, "value") else str(role),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

    @staticmethod
    async def list(db: AsyncSession, *, account_id: int) -> builtins.list[AccountMember]:
        stmt = select(AccountMember).where(AccountMember.account_id == account_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())
