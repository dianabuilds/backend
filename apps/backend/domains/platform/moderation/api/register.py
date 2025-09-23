from fastapi import FastAPI

from .http import router as moderation_router


def register_moderation(app: FastAPI) -> None:
    """Attach moderation routes under /api/moderation to the app."""
    app.include_router(moderation_router)


__all__ = ["register_moderation"]
