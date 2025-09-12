from __future__ import annotations

from uuid import UUID


def can_read_profile(subject_id: UUID | None, resource_user_id: UUID) -> bool:
    return True  # публичный профиль доступен всем


def can_update_profile(subject_id: UUID | None, resource_user_id: UUID) -> bool:
    return subject_id is not None and subject_id == resource_user_id

__all__ = ["can_read_profile", "can_update_profile"]

