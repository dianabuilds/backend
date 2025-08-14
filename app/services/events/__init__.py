"""Domain events infrastructure."""
from .base import Event
from .bus import get_event_bus, InMemoryEventBus
from .events import NodeCreated, NodeUpdated
from .handlers import register_handlers
import os

__all__ = [
    "Event",
    "get_event_bus",
    "InMemoryEventBus",
    "NodeCreated",
    "NodeUpdated",
    "register_handlers",
]

if os.environ.get("TESTING") == "True":
    register_handlers()
