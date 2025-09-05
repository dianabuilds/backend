from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import db_session

logger = logging.getLogger(__name__)


async def ensure_default_admin() -> None:
    """Create a default admin user if none exists."""
    if not settings.admin.bootstrap_enabled:
        return

    async with db_session() as session:
        res = await session.execute(select(User).where(User.role == "admin"))
        if res.scalars().first():
            return
        user = User(
            email=settings.admin.email,
            username=settings.admin.username,
            password_hash=get_password_hash(settings.admin.password),
            is_active=True,
            role="admin",
        )
        session.add(user)
        logger.info("Default admin user created")
