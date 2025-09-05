from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.config import settings
from app.domains.accounts.infrastructure.models import Account, AccountMember
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import db_session
from app.schemas.accounts import AccountKind, AccountRole

logger = logging.getLogger(__name__)


async def ensure_global_account() -> None:
    """Ensure a single global system account exists.

    The account is created with kind ``team`` and marked as system. All users
    whose role is in ``settings.security.admin_roles`` are granted access.
    """

    async with db_session() as session:
        result = await session.execute(
            select(Account).where(
                Account.kind == AccountKind.team,
                Account.is_system.is_(True),
            )
        )
        account = result.scalars().first()
        if account:
            return

        owner_res = await session.execute(
            select(User)
            .where(User.role.in_(settings.security.admin_roles))
            .order_by(User.created_at)
            .limit(1)
        )
        owner = owner_res.scalars().first()
        if not owner:
            logger.warning("Cannot create global account: no admin user found")
            return

        account = Account(
            name="Global",
            slug="global",
            owner_user_id=owner.id,
            kind=AccountKind.team,
            is_system=True,
            settings_json={},
        )
        session.add(account)
        await session.flush()

        trusted_res = await session.execute(
            select(User).where(User.role.in_(settings.security.admin_roles))
        )
        for user in trusted_res.scalars().all():
            session.add(
                AccountMember(
                    account_id=account.id,
                    user_id=user.id,
                    role=AccountRole.owner,
                )
            )

        await session.commit()
        logger.info("Created global account %s", account.id)
