from __future__ import annotations

"""Common exceptions for platform event publishing."""


class OutboxError(RuntimeError):
    """Raised when an outbox publisher fails to emit an event."""

    def __init__(
        self, message: str = "outbox_publish_failed", *, topic: str | None = None
    ) -> None:
        super().__init__(message)
        self.topic = topic


__all__ = ["OutboxError"]
