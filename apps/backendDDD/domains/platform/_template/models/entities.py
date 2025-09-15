from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Message:
    id: str
    channel: str
    payload: dict
