"""Router registration for the admin contour of domain product.profile."""

from fastapi import FastAPI

from .http import router


def register_admin(app: FastAPI) -> None:
    """Attach the admin contour routes for domain product.profile."""
    app.include_router(router)


__all__ = ["register_admin"]
