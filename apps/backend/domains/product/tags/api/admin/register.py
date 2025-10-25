"""Router registration for the admin contour of domain product.tags."""

from fastapi import FastAPI

from .http import router


def register_admin(app: FastAPI) -> None:
    """Attach the admin contour routes for domain product.tags."""
    # TODO: wire handlers when the contour gains real endpoints.
    app.include_router(router)


__all__ = ["register_admin"]
