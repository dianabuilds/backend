from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.providers.db.session import get_engine
from app.models.outbox import OutboxEvent


class SAOutboxAdapter:
    """Persist events into monolith Outbox table (sync session)."""

    def __init__(self) -> None:
        self._Session = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)

    def publish(self, topic: str, payload: dict[str, Any], key: str | None = None) -> None:
        with self._Session() as s:  # type: Session
            evt = OutboxEvent(topic=topic, payload_json=payload, dedup_key=key)
            s.add(evt)
            s.commit()
