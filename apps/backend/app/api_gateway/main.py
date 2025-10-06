from __future__ import annotations

import inspect
import logging
from contextlib import asynccontextmanager
from importlib import import_module
from types import ModuleType
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text as sa_text
from sqlalchemy.exc import SQLAlchemyError
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response

from packages.core.db import get_async_engine
from packages.core.errors import ApiError
from packages.core.testing import is_test_mode

from .events_relay import ShutdownHook, start_events_relay
from .metrics_middleware import setup_http_metrics
from .settings import me_router as settings_me_router
from .settings import router as settings_router
from .wires import build_container

DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def _configure_cors(app: FastAPI) -> None:
    origins = DEFAULT_CORS_ORIGINS
    try:
        from packages.core.config import (
            load_settings,
        )  # local import to avoid cycle at import time

        configured = load_settings().cors_origins or ""
        if configured:
            parsed = [o.strip() for o in configured.split(",") if o.strip()]
            if parsed:
                origins = parsed
    except Exception as exc:
        logger.exception("Failed to load CORS settings", exc_info=exc)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


logger = logging.getLogger(__name__)


redis_asyncio: ModuleType | None
RedisError: type[Exception]
try:
    redis_asyncio = import_module("redis.asyncio")
    from redis.exceptions import RedisError as _RedisError  # type: ignore

    RedisError = _RedisError
except ImportError:  # pragma: no cover
    redis_asyncio = None

    RedisError = type("RedisErrorFallback", (Exception,), {})


fastapi_limiter_module: ModuleType | None
try:
    fastapi_limiter_module = import_module("fastapi_limiter")
except ImportError:  # pragma: no cover
    fastapi_limiter_module = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    sapp = cast(Starlette, app)
    sapp.state.test_mode = is_test_mode()
    try:
        container = build_container(env="dev")
        sapp.state.container = container
        sapp.state.test_mode = is_test_mode(getattr(container, "settings", None))
    except Exception as exc:
        logger.exception("Failed to build dependency container", exc_info=exc)
        raise

    shutdown_callbacks: list[ShutdownHook] = []

    try:
        try:
            shutdown_callbacks.append(await start_events_relay(app))
        except Exception as exc:
            logger.exception("Failed to start events relay", exc_info=exc)
        try:
            shutdown_callbacks.extend(await _setup_rate_limiter(sapp))
        except Exception as exc:
            logger.exception("Failed to initialize rate limiter", exc_info=exc)
        yield
    finally:
        while shutdown_callbacks:
            callback = shutdown_callbacks.pop()
            try:
                await callback()
            except Exception as exc:
                logger.exception("Error during shutdown callback", exc_info=exc)
        sapp.state.container = None


async def _setup_rate_limiter(app: Starlette) -> list[ShutdownHook]:
    hooks: list[ShutdownHook] = []
    if fastapi_limiter_module is None or redis_asyncio is None:
        return hooks

    limiter_cls = getattr(fastapi_limiter_module, "FastAPILimiter", None)
    if limiter_cls is None:
        return hooks

    container = getattr(app.state, "container", None)
    settings = getattr(container, "settings", None)
    redis_url = getattr(settings, "redis_url", None)
    if not redis_url:
        return hooks

    url = str(redis_url)
    try:
        redis_client = redis_asyncio.from_url(
            url, encoding="utf-8", decode_responses=True
        )
    except (RedisError, ValueError):
        logger.exception("Failed to create Redis client for limiter: %s", url)
        return hooks

    try:
        await redis_client.ping()
    except RedisError:
        logger.warning("Redis not reachable (%s): limiter disabled", url)
        await _close_redis_client(redis_client)
        return hooks

    try:
        await limiter_cls.init(redis_client)
    except Exception as exc:
        logger.exception(
            "Failed to initialize FastAPILimiter for %s", url, exc_info=exc
        )
        await _close_redis_client(redis_client)
        return hooks

    logger.info("FastAPILimiter initialized with Redis %s", url)

    async def _shutdown() -> None:
        try:
            close = getattr(limiter_cls, "close", None)
            if callable(close):
                result = close()
                if inspect.isawaitable(result):
                    await result
        except Exception as exc:
            logger.exception("FastAPILimiter.close failed", exc_info=exc)
        await _close_redis_client(redis_client)

    hooks.append(_shutdown)
    return hooks


async def _close_redis_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        result = close()
        if inspect.isawaitable(result):
            await result
    wait_closed = getattr(client, "wait_closed", None)
    if callable(wait_closed):
        result = wait_closed()
        if inspect.isawaitable(result):
            await result
    pool = getattr(client, "connection_pool", None)
    disconnect = getattr(pool, "disconnect", None)
    if callable(disconnect):
        result = disconnect()
        if inspect.isawaitable(result):
            await result


app = FastAPI(lifespan=lifespan, swagger_ui_parameters={"persistAuthorization": True})

# Observability bootstrap (optional deps, non-fatal)
observability_module: ModuleType | None
try:
    observability_module = import_module(
        "apps.backend.infra.observability.opentelemetry"
    )
except ImportError:  # pragma: no cover
    observability_module = None
else:
    try:
        setup_otel = observability_module.setup_otel
        setup_otel(service_name="backend")
    except Exception as exc:
        logger.exception("Failed to configure OpenTelemetry", exc_info=exc)

try:
    setup_http_metrics(app)
except Exception as exc:
    logger.exception("Failed to configure HTTP metrics", exc_info=exc)

_configure_cors(app)


def _setup_openapi_security() -> None:
    """Augment OpenAPI with auth schemes for Swagger UI.

    - BearerAuth: Authorization: Bearer <token>
    - CookieAuth: Cookie access_token=<token>
    - CsrfHeader: X-CSRF header for state-changing requests
    """

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title="Backend API",
            version="1.0.0",
            description="Backend service",
            routes=app.routes,
        )
        try:
            from packages.core.config import load_settings  # local import

            s = load_settings()
            csrf_header = s.auth_csrf_header_name
            csrf_cookie = s.auth_csrf_cookie_name
        except Exception as exc:
            logger.debug("Using default CSRF configuration", exc_info=exc)
            csrf_header = "X-CSRF-Token"
            csrf_cookie = "XSRF-TOKEN"

        comps = schema.setdefault("components", {}).setdefault("securitySchemes", {})
        comps.update(
            {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
                "CookieAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "access_token",
                },
                "CsrfHeader": {"type": "apiKey", "in": "header", "name": csrf_header},
                "CsrfCookie": {"type": "apiKey", "in": "cookie", "name": csrf_cookie},
                "AdminKey": {"type": "apiKey", "in": "header", "name": "X-Admin-Key"},
            }
        )
        # Make them appear in Swagger "Authorize" dialog (optional per-endpoint at runtime)
        schema.setdefault(
            "security",
            [
                {"BearerAuth": []},
                {"CookieAuth": []},
                {"CsrfHeader": []},
                {"CsrfCookie": []},
                {"AdminKey": []},
            ],
        )
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi


_setup_openapi_security()


# Return 400 for payload validation errors to match legacy API
def _validation_handler(request: Request, exc: RequestValidationError) -> Response:
    try:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "invalid_payload",
                "errors": exc.errors(),
            },
        )
    except Exception as exc:
        logger.exception("Validation handler fallback applied", exc_info=exc)
        return JSONResponse(status_code=400, content={"detail": "invalid_payload"})


app.add_exception_handler(RequestValidationError, _validation_handler)


# --- Health/Readiness ---
@app.get("/healthz", include_in_schema=False)
def healthz() -> dict:
    return {"ok": True}


@app.get("/readyz", include_in_schema=False)
async def readyz() -> dict[str, object]:
    details: dict[str, object] = {"redis": False, "database": False, "search": False}
    try:
        settings = load_settings()
    except Exception as exc:
        logger.exception("Readyz settings load failed", exc_info=exc)
        return {"ok": False}

    ok = True
    redis_url = getattr(settings, "redis_url", None)
    redis_client = None
    if redis_url:
        try:
            redis_module = import_module("redis")
            redis_client = redis_module.Redis.from_url(
                str(redis_url), decode_responses=True
            )
            redis_client.ping()
        except ModuleNotFoundError:
            logger.warning(
                "Redis package not installed; readyz will report redis=false"
            )
            ok = False
        except RedisError as exc:
            logger.warning("Redis health check failed: %s", exc)
            ok = False
        else:
            details["redis"] = True
        finally:
            if redis_client is not None:
                try:
                    redis_client.close()
                except Exception as exc:
                    logger.debug(
                        "Failed to close Redis client during readyz", exc_info=exc
                    )
    else:
        ok = False

    try:
        engine = get_async_engine("readyz", url=settings.database_url)
        async with engine.begin() as conn:
            await conn.execute(sa_text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Database health check failed: %s", exc)
        ok = False
    else:
        details["database"] = True

    container = getattr(app.state, "container", None)
    details["search"] = bool(getattr(container, "search", None))

    return {"ok": ok, "components": details}


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
from domains.platform.moderation.api.register import (
    register_moderation as register_platform_moderation,
)  # noqa: E402
from domains.platform.notifications.api.admin_campaigns import (
    make_router as notifications_admin_router,  # noqa: E402
)
from domains.platform.notifications.api.admin_templates import (
    make_router as notifications_templates_router,  # noqa: E402
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
from domains.product.ai.api.admin_http import (
    make_router as ai_admin_router,  # noqa: E402
)
from domains.product.ai.api.http import make_router as ai_router  # noqa: E402
from domains.product.content.api.http import make_router as content_router  # noqa: E402
from domains.product.moderation.api.http import (
    make_router as moderation_router,
)  # noqa: E402
from domains.product.navigation.api.http import (
    make_router as navigation_router,
)  # noqa: E402
from domains.product.nodes.api import (
    make_admin_router as nodes_admin_router,
)  # noqa: E402
from domains.product.nodes.api import (
    make_public_router as nodes_router,
)
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

from .debug import make_router as debug_router  # noqa: E402

# Product routers
app.include_router(profile_router())
app.include_router(settings_router)
app.include_router(settings_me_router)
# Product routers behind flags from DDD Settings
from packages.core.config import load_settings  # noqa: E402

_s = load_settings()
if _s.nodes_enabled:
    app.include_router(nodes_router())
    app.include_router(nodes_admin_router())
if _s.tags_enabled:
    app.include_router(tags_router())
    app.include_router(tags_admin_router())
if _s.quests_enabled:
    app.include_router(quests_router())
if _s.navigation_enabled:
    app.include_router(navigation_router())
if _s.content_enabled:
    app.include_router(content_router())
if _s.ai_enabled:
    app.include_router(ai_router())
    app.include_router(ai_admin_router())
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
app.include_router(notifications_templates_router())
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
register_platform_moderation(app)
# Debug only in non-prod
try:
    if getattr(_s, "enable_debug_routes", False):
        if _s.env == "prod":
            logger.warning("Debug router requested in prod; skipping registration")
        else:
            app.include_router(debug_router())
except Exception as exc:
    logger.warning("Failed to register debug router", exc_info=exc)


def _api_error_handler(request: Request, exc: ApiError) -> Response:
    body: dict[str, dict[str, Any]] = {"error": {"code": exc.code}}
    if exc.message:
        body["error"]["message"] = exc.message
    if getattr(exc, "extra", None):
        body["error"]["extra"] = dict(exc.extra)
    headers = dict(getattr(exc, "headers", {}))
    return JSONResponse(status_code=exc.status_code, content=body, headers=headers)


app.add_exception_handler(ApiError, _api_error_handler)
