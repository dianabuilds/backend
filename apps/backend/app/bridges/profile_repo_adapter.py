from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_engine
from apps.backendDDD.domains.product.profile.domain.entities import Profile


class SAUserProfileRepo:
    """Profile Repo backed by the monolith users table (sync session).

    Implements the product/profile Repo protocol for transitional wiring.
    """

    def __init__(self) -> None:
        # Use the sync engine for simple blocking operations inside FastAPI thread.
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def _to_uuid(self, id_str: str) -> uuid.UUID:
        return id_str if isinstance(id_str, uuid.UUID) else uuid.UUID(str(id_str))

    def get(self, id: str) -> Optional[Profile]:  # noqa: A003 - protocol name
        uid = self._to_uuid(id)
        with self._Session() as s:  # type: Session
            u = s.get(User, uid)
            if not u:
                return None
            # Normalise username to empty string if missing to satisfy domain type
            username = u.username or ""
            return Profile(id=str(u.id), username=username, bio=u.bio)

    def upsert(self, p: Profile) -> Profile:
        uid = self._to_uuid(p.id)
        with self._Session() as s:  # type: Session
            u = s.get(User, uid)
            if u is None:
                # Create a minimal user row; other fields keep DB defaults
                u = User(id=uid)
                s.add(u)
            # Apply changes
            u.username = p.username
            if p.bio is not None:
                u.bio = p.bio
            try:
                s.commit()
            except IntegrityError as e:
                # Likely username uniqueness violation
                s.rollback()
                raise ValueError("username already taken") from e
            return Profile(id=str(u.id), username=u.username or "", bio=u.bio)

