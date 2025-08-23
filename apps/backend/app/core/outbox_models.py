from __future__ import annotations

import app.models.outbox as _outbox  # legacy source

OutboxEvent = _outbox.OutboxEvent
OutboxStatus = _outbox.OutboxStatus

__all__ = ["OutboxEvent", "OutboxStatus"]
