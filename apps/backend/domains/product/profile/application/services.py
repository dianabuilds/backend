from __future__ import annotations

from domains.product.profile.application.mappers import to_view
from domains.product.profile.application.ports import IamClient, Outbox, Repo
from domains.product.profile.domain.entities import Profile
from packages.core import Flags


class Service:
    def __init__(self, repo: Repo, outbox: Outbox, iam: IamClient, flags: Flags):
        self.repo, self.outbox, self.iam, self.flags = repo, outbox, iam, flags

    def update_username(self, user_id: str, username: str, subject: dict) -> dict:
        if not self.iam.allow(subject, "profile.update", {"user_id": user_id}):
            raise PermissionError("denied")
        entity = self.repo.get(user_id) or Profile(id=user_id, username=username)
        entity.rename(username)
        saved = self.repo.upsert(entity)
        self.outbox.publish(
            "profile.updated.v1",
            {"id": saved.id, "username": saved.username},
            key=saved.id,
        )
        return to_view(saved).__dict__
