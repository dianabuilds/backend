from __future__ import annotations

import logging
from collections.abc import Callable

from .retry import with_retry

log = logging.getLogger("notifications")

_channels: dict[str, Callable[[dict], None]] = {}


def register_channel(name: str, sender: Callable[[dict], None]) -> None:
    _channels[name] = sender


@with_retry()
def dispatch(channel: str, payload: dict) -> None:  # pragma: no cover - thin wrapper
    sender = _channels.get(channel)
    if sender is None:
        # Fallback to log channel
        log.info("notify[%s]: %s", channel, payload)
        return
    sender(payload)
