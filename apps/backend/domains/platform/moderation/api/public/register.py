"""Router registration for the public contour of domain platform.moderation."""

from fastapi import FastAPI

from .http import router


def register_public(app: FastAPI) -> None:
    """Attach the public contour routes for domain platform.moderation."""
    # TODO: wire handlers when the contour gains real endpoints.
    app.include_router(router)


__all__ = ["register_public"]
