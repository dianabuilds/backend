import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import db_session
from app.models.user import User

logger = logging.getLogger(__name__)


async def ensure_default_admin() -> None:
    """
    Создаёт администратора (или чинит пароль/роль), если включён bootstrap.
    Параметры берутся из .env: admin_username, admin_email, admin_password.
    """
    if not settings.admin_bootstrap_enabled:
        return

    username = settings.admin_username.strip()
    email = settings.admin_email.strip()
    password = settings.admin_password

    if not username or not email or not password:
        logger.warning("Admin bootstrap skipped: incomplete credentials in settings.")
        return

    async with db_session() as session:  # type: AsyncSession
        # Ищем по username или email
        result = await session.execute(
            select(User).where((User.username == username) | (User.email == email))
        )
        user: User | None = result.scalars().first()

        if not user:
            # Создаём нового администратора
            user = User(
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                is_active=True,
                role="admin",
                is_premium=True,
            )
            session.add(user)
            await session.flush()
            logger.info("Default admin user created: %s (%s)", username, email)
        else:
            changed = False
            # Повышаем роль при необходимости
            if getattr(user, "role", "user") != "admin":
                user.role = "admin"
                changed = True
            # Устанавливаем пароль, если отсутствует, либо чиним тестовый
            if not user.password_hash:
                user.password_hash = get_password_hash(password)
                changed = True
            if changed:
                logger.info("Default admin user updated: %s", username)
        # commit произойдёт в db_session
