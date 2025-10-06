"""Compatibility shim that forwards to the new admin http module."""

from .admin.http import make_router

__all__ = ["make_router"]
