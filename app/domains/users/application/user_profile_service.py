from __future__ import annotations

from typing import Any

from app.domains.users.application.ports.user_repo_port import IUserRepository
from app.domains.users.infrastructure.models.user import User


class UserProfileService:
    def __init__(self, repo: IUserRepository) -> None:
        self._repo = repo

    async def read_me(self, user: User) -> User:
        return user

    async def update_me(self, user: User, data: dict[str, Any]) -> User:
        return await self._repo.update_fields(user, data)

    async def delete_me(self, user: User) -> dict:
        await self._repo.soft_delete(user)
        return {"message": "Account deleted"}
