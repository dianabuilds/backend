from __future__ import annotations

import fastapi

from app.kernel.config import Settings, get_settings
from app.kernel import bootstrap_env_and_logging, create_app
from app.domains.auth.security import auth_user


# Bootstrap env and logging once
bootstrap_env_and_logging()

# Build settings and app via kernel loader
settings: Settings = get_settings()
app = create_app(settings)


@app.get("/users/me")
async def users_me(current=fastapi.Depends(auth_user)):
    try:
        return {
            "id": str(getattr(current, "id", "")),
            "username": getattr(current, "username", None),
            "role": getattr(current, "role", None),
            "email": getattr(current, "email", None),
        }
    except Exception:
        return {"id": None}
