from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.providers.db.session import get_engine
from app.models.outbox import OutboxEvent, OutboxStatus
from app.bridges.tag_usage_projection_adapter import SATagUsageProjection


logger = logging.getLogger(__name__)


def _process_payload(proj: SATagUsageProjection, payload: dict[str, Any]) -> None:
    author_id = str(payload.get("author_id") or "")
    added = list(payload.get("added") or [])
    removed = list(payload.get("removed") or [])
    content_type = str(payload.get("content_type") or "node")
    if not author_id:
        return
    # Ensure strings
    added = [str(x) for x in added]
    removed = [str(x) for x in removed]
    if not added and not removed:
        return
    proj.apply_diff(author_id, added, removed, content_type=content_type)


def consume_once(max_events: int = 500) -> int:
    """Pull a batch of NEW outbox events for node.tags.updated.v1 and apply projection.

    Returns number of processed events.
    """
    SessionLocal = sessionmaker(bind=get_engine().sync_engine, expire_on_commit=False)
    processed = 0
    proj = SATagUsageProjection()
    with SessionLocal() as s:  # type: Session
        # Lock a batch for processing (best-effort; DB-specific tuning may apply)
        rows = (
            s.query(OutboxEvent)
            .filter(OutboxEvent.topic.in_(["node.tags.updated.v1", "quest.tags.updated.v1"]) , OutboxEvent.status == OutboxStatus.NEW)
            .order_by(OutboxEvent.created_at.asc())
            .limit(max_events)
            .with_for_update(skip_locked=True)
            .all()
        )
        for evt in rows:
            try:
                payload = evt.payload_json if isinstance(evt.payload_json, dict) else json.loads(json.dumps(evt.payload_json))
            except Exception:
                payload = {}
            try:
                _process_payload(proj, payload)
                evt.status = OutboxStatus.SENT
                processed += 1
            except Exception as e:  # keep robust, mark failed
                logger.warning("tag_usage consumer failed for event %s: %s", getattr(evt, "id", None), e)
                evt.status = OutboxStatus.FAILED
        if rows:
            s.commit()
    return processed


def main() -> None:  # pragma: no cover - CLI entry
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    n = consume_once(max_events=500)
    logger.info("Processed %s tag usage events", n)


if __name__ == "__main__":  # pragma: no cover
    main()
