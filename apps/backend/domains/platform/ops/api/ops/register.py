"""Router registration for the ops contour of domain platform.ops."""

from fastapi import FastAPI

from .http import router


def register_ops(app: FastAPI) -> None:
    """Attach the ops contour routes for domain platform.ops."""
    # TODO: wire handlers when the contour gains real endpoints.
    app.include_router(router)


__all__ = ["register_ops"]
