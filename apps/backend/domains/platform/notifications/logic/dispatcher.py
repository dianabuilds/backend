from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from .retry import with_retry

log = logging.getLogger("notifications")

Payload = Mapping[str, Any]
_channels: dict[str, Callable[[Payload], None]] = {}


def register_channel(name: str, sender: Callable[[Payload], None]) -> None:
    _channels[name] = sender


@with_retry()
def dispatch(channel: str, payload: Payload) -> None:  # pragma: no cover - thin wrapper
    sender = _channels.get(channel)
    if sender is None:
        # Fallback to log channel
        log.info("notify[%s]: %s", channel, payload)
        return
    sender(payload)
