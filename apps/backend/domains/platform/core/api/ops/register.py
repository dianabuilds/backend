"""Router registration for the ops contour of domain platform.core."""

from fastapi import FastAPI

from .http import router


def register_ops(app: FastAPI) -> None:
    """Attach the ops contour routes for domain platform.core."""
    # TODO: wire handlers when the contour gains real endpoints.
    app.include_router(router)


__all__ = ["register_ops"]
