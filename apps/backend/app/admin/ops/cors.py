from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter()


@router.get("/cors")
def get_cors_config(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Return CORS configuration used by the application."""
    cors_config: dict[str, object] = {**settings.effective_origins()}
    cors_config.update(
        {
            "allow_credentials": settings.cors_allow_credentials,
            "allow_methods": settings.cors_allow_methods,
            "allow_headers": settings.cors_allow_headers,
            "expose_headers": settings.cors_expose_headers,
            "max_age": settings.cors_max_age,
        }
    )
    return cors_config
