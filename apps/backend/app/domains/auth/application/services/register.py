from __future__ import annotations

from app.domains.auth.application.ports.hasher import IPasswordHasher
from app.domains.auth.application.ports.user_repo import IUserRepository
from app.domains.users.infrastructure.models.user import User


class RegisterService:
    def __init__(self, repo: IUserRepository, hasher: IPasswordHasher) -> None:
        self._repo = repo
        self._hasher = hasher

    async def register(self, *, email: str, password: str, is_active: bool = False) -> User:
        existing: User | None = await self._repo.get_by_email(email)
        if existing is not None:
            raise ValueError("user with this email already exists")
        ph = self._hasher.hash(password)
        user = await self._repo.create(email=email, password_hash=ph, is_active=is_active)
        return user
