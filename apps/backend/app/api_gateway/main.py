from __future__ import annotations

import threading
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from .wires import build_container

try:
    import redis.asyncio as aioredis  # type: ignore
    from fastapi_limiter import FastAPILimiter  # type: ignore
except Exception:  # pragma: no cover
    FastAPILimiter = None  # type: ignore
    aioredis = None  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI inherits from Starlette; cast for type checkers to see `.state`.
    sapp = cast(Starlette, app)
    sapp.state.container = build_container(env="dev")
    # Start events relay in background (if supported)
    try:

        def _run_events():
            try:
                sapp.state.container.events.run(block_ms=5000)
            except Exception:
                pass

        t = threading.Thread(target=_run_events, name="events-relay", daemon=True)
        t.start()
        sapp.state._events_thread = t  # type: ignore[attr-defined]
    except Exception:
        pass
    # Initialize rate limiter
    try:
        if FastAPILimiter is not None and aioredis is not None:
            s = sapp.state.container.settings
            if s.redis_url:
                r = aioredis.from_url(
                    str(s.redis_url), encoding="utf-8", decode_responses=True
                )
                await FastAPILimiter.init(r)
    except Exception:
        pass
    try:
        yield
    finally:
        sapp.state.container = None


app = FastAPI(lifespan=lifespan)


# Return 400 for payload validation errors to match legacy API
def _validation_handler(request, exc: RequestValidationError):  # type: ignore[override]
    try:
        # Keep FastAPI error structure but standardize wrapper
        return JSONResponse(
            status_code=400,
            content={
                "detail": "invalid_payload",
                "errors": exc.errors(),
            },
        )
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "invalid_payload"})


app.add_exception_handler(RequestValidationError, _validation_handler)


# --- Health/Readiness ---
@app.get("/healthz", include_in_schema=False)
def healthz() -> dict:
    return {"ok": True}


@app.get("/readyz", include_in_schema=False)
async def readyz() -> dict:

    # Access container via global app state (Starlette)
    # This handler is async to allow DB ping via async engine
    # We build a minimal result with components
    ok = True
    details: dict[str, object] = {"redis": False, "database": False, "search": False}
    try:
        # Redis check
        try:
            import redis  # type: ignore

            s = load_settings()
            r = redis.Redis.from_url(str(s.redis_url), decode_responses=True)
            r.ping()
            details["redis"] = True
        except Exception:
            details["redis"] = False
            ok = False
        # DB check
        try:
            from sqlalchemy import text as _text  # type: ignore
            from sqlalchemy.ext.asyncio import create_async_engine  # type: ignore

            s = load_settings()
            dsn = str(s.database_url)
            engine = create_async_engine(dsn)
            async with engine.begin() as conn:
                await conn.execute(_text("SELECT 1"))
            details["database"] = True
        except Exception:
            details["database"] = False
            # keep ok for non-DB setups
        # Search check (container presence)
        try:
            # If container exists and has search, mark as ready
            # Note: FastAPI app.state.container is set in lifespan

            # We can't access Request here easily; rely on app state
            # noinspection PyUnresolvedReferences
            # type: ignore[attr-defined]
            c = app.state.container  # type: ignore[attr-defined]
            details["search"] = bool(getattr(c, "search", None))
        except Exception:
            details["search"] = False
        return {"ok": bool(ok), "components": details}
    except Exception:
        return {"ok": False}


# Product routers registration
from domains.platform.admin.api.http import make_router as admin_router  # noqa: E402
from domains.platform.audit.api.http import make_router as audit_router  # noqa: E402
from domains.platform.billing.api.http import (
    make_router as billing_router,
)  # noqa: E402

# Platform routers registration
from domains.platform.events.api.http import make_router as events_router  # noqa: E402
from domains.platform.flags.api.http import make_router as flags_router  # noqa: E402
from domains.platform.iam.api.http import make_router as iam_router  # noqa: E402
from domains.platform.media.api.http import make_router as media_router  # noqa: E402
from domains.platform.notifications.api.admin_campaigns import (
    make_router as notifications_admin_router,  # noqa: E402
)
from domains.platform.notifications.api.http import (
    make_router as notifications_router,  # noqa: E402
)
from domains.platform.notifications.api.messages import (
    make_router as notifications_messages_router,  # noqa: E402
)
from domains.platform.notifications.api.ws import (
    make_router as notifications_ws_router,  # noqa: E402
)
from domains.platform.quota.api.http import make_router as quota_router  # noqa: E402
from domains.platform.search.api.http import make_router as search_router  # noqa: E402
from domains.platform.telemetry.api.admin_http import (
    make_router as telemetry_admin_router,  # noqa: E402
)
from domains.platform.telemetry.api.http import (
    make_router as telemetry_router,
)  # noqa: E402
from domains.platform.users.api.http import make_router as users_router  # noqa: E402
from domains.product.achievements.api.http import (
    make_router as achievements_router,
)  # noqa: E402
from domains.product.ai.api.http import make_router as ai_router  # noqa: E402
from domains.product.moderation.api.http import (
    make_router as moderation_router,
)  # noqa: E402
from domains.product.navigation.api.http import (
    make_router as navigation_router,
)  # noqa: E402
from domains.product.nodes.api.http import make_router as nodes_router  # noqa: E402
from domains.product.premium.api.http import make_router as premium_router  # noqa: E402
from domains.product.profile.api.http import make_router as profile_router  # noqa: E402
from domains.product.quests.api.http import make_router as quests_router  # noqa: E402
from domains.product.referrals.api.http import (
    make_router as referrals_router,
)  # noqa: E402
from domains.product.tags.api.admin_http import (
    make_router as tags_admin_router,
)  # noqa: E402
from domains.product.tags.api.http import make_router as tags_router  # noqa: E402
from domains.product.worlds.api.http import make_router as worlds_router  # noqa: E402

# Product routers
app.include_router(profile_router())
# Product routers behind flags from DDD Settings
from packages.core.config import load_settings  # type: ignore  # noqa: E402

_s = load_settings()
if _s.nodes_enabled:
    app.include_router(nodes_router())
if _s.tags_enabled:
    app.include_router(tags_router())
    app.include_router(tags_admin_router())
if _s.quests_enabled:
    app.include_router(quests_router())
if _s.navigation_enabled:
    app.include_router(navigation_router())
if _s.ai_enabled:
    app.include_router(ai_router())
if _s.moderation_enabled:
    app.include_router(moderation_router())
if _s.achievements_enabled:
    app.include_router(achievements_router())
if _s.worlds_enabled:
    app.include_router(worlds_router())
# Product routers behind flags from DDD Settings
if _s.referrals_enabled:
    app.include_router(referrals_router())
if _s.premium_enabled:
    app.include_router(premium_router())

# Platform routers
app.include_router(events_router())
app.include_router(telemetry_router())
app.include_router(telemetry_admin_router())
app.include_router(quota_router())
app.include_router(notifications_router())
app.include_router(notifications_admin_router())
app.include_router(notifications_messages_router())
app.include_router(notifications_ws_router())
app.include_router(iam_router())
app.include_router(search_router())
app.include_router(media_router())
app.include_router(audit_router())
app.include_router(billing_router())
app.include_router(flags_router())
app.include_router(admin_router())
app.include_router(users_router())
