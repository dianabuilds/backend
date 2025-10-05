"""Delivery subpackage exposing service and event abstractions."""

from .event import NotificationEvent
from .service import DeliveryService

__all__ = ["NotificationEvent", "DeliveryService"]
