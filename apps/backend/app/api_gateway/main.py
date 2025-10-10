from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
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

from packages.core.config import Settings, load_settings
from packages.core.db import get_async_engine
from packages.core.errors import ApiError
from packages.core.testing import is_test_mode

from .events_relay import ShutdownHook, start_events_relay
from .metrics_middleware import setup_http_metrics
from .settings import me_router as settings_me_router
from .settings import router as settings_router
from .wires import Container, build_container

DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

logger = logging.getLogger(__name__)

try:
    _redis_asyncio: ModuleType | None = import_module("redis.asyncio")
    _redis_exceptions = import_module("redis.exceptions")
    RedisError = cast(
        type[Exception], getattr(_redis_exceptions, "RedisError", Exception)
    )
except ImportError:  # pragma: no cover - optional dependency
    _redis_asyncio = None
    RedisError = type("RedisErrorFallback", (Exception,), {})

try:
    _fastapi_limiter: ModuleType | None = import_module("fastapi_limiter")
except ImportError:  # pragma: no cover - optional dependency
    _fastapi_limiter = None


def _configure_cors(app: FastAPI, settings: Settings) -> None:
    origins = DEFAULT_CORS_ORIGINS
    configured = (settings.cors_origins or "").strip()
    if configured:
        parsed = [item.strip() for item in configured.split(",") if item.strip()]
        if parsed:
            origins = parsed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _configure_observability(app: FastAPI, service_name: str) -> None:
    try:
        observability_module = import_module(
            "apps.backend.infra.observability.opentelemetry"
        )
    except ImportError:  # pragma: no cover - optional dependency
        return
    setup_otel = getattr(observability_module, "setup_otel", None)
    if callable(setup_otel):
        try:
            setup_otel(service_name=service_name)
        except Exception as exc:  # pragma: no cover - defensive logging only
            logger.exception("Failed to configure OpenTelemetry", exc_info=exc)


def _setup_openapi_security(app: FastAPI, settings: Settings) -> None:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema  # type: ignore[return-value]
        schema = get_openapi(
            title="Backend API",
            version="1.0.0",
            description="Backend service",
            routes=app.routes,
        )
        csrf_header = getattr(settings, "auth_csrf_header_name", "X-CSRF-Token")
        csrf_cookie = getattr(settings, "auth_csrf_cookie_name", "XSRF-TOKEN")
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
        app.openapi_schema = schema  # type: ignore[assignment]
        return schema

    app.openapi = custom_openapi  # type: ignore[assignment]


def _api_error_handler(request: Request, exc: ApiError) -> Response:
    body: dict[str, dict[str, Any]] = {"error": {"code": exc.code}}
    if exc.message:
        body["error"]["message"] = exc.message
    if getattr(exc, "extra", None):
        body["error"]["extra"] = dict(exc.extra)
    headers = dict(getattr(exc, "headers", {}))
    return JSONResponse(status_code=exc.status_code, content=body, headers=headers)


def _validation_error_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    try:
        return JSONResponse(
            status_code=400,
            content={"detail": "invalid_payload", "errors": exc.errors()},
        )
    except Exception as err:  # pragma: no cover - fallback only
        logger.exception("Validation handler fallback applied", exc_info=err)
        return JSONResponse(status_code=400, content={"detail": "invalid_payload"})


async def _setup_rate_limiter(app: Starlette, settings: Settings) -> list[ShutdownHook]:
    hooks: list[ShutdownHook] = []
    if _fastapi_limiter is None or _redis_asyncio is None:
        return hooks

    limiter_cls = getattr(_fastapi_limiter, "FastAPILimiter", None)
    if limiter_cls is None:
        return hooks

    redis_url = getattr(settings, "redis_url", None)
    if not redis_url:
        return hooks

    url = str(redis_url)
    try:
        redis_client = _redis_asyncio.from_url(
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


def create_lifespan(
    settings: Settings,
    *,
    container_factory: Callable[[], Container] = build_container,
) -> Callable[[FastAPI], Any]:
    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        sapp = cast(Starlette, app)
        sapp.state.test_mode = is_test_mode(settings)
        container: Container | None = None
        shutdown_callbacks: list[ShutdownHook] = []
        try:
            container = container_factory()
            sapp.state.container = container
            sapp.state.test_mode = is_test_mode(getattr(container, "settings", None))
        except Exception as exc:
            logger.exception("Failed to build dependency container", exc_info=exc)
            raise

        try:
            try:
                shutdown_callbacks.append(await start_events_relay(app))
            except Exception as exc:
                logger.exception("Failed to start events relay", exc_info=exc)
            try:
                shutdown_callbacks.extend(await _setup_rate_limiter(sapp, settings))
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

    return _lifespan


def _register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)


def _register_health_routes(app: FastAPI, settings: Settings) -> None:
    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/readyz", include_in_schema=False)
    async def readyz() -> dict[str, object]:
        details: dict[str, object] = {
            "redis": False,
            "database": False,
            "search": False,
        }
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


def _register_core_routers(app: FastAPI, settings: Settings) -> None:
    from domains.platform.admin.api.http import make_router as admin_router
    from domains.platform.audit.api.http import make_router as audit_router
    from domains.platform.billing.api.http import make_router as billing_router
    from domains.platform.events.api.http import make_router as events_router
    from domains.platform.flags.api.http import make_router as flags_router
    from domains.platform.iam.api.http import make_router as iam_router
    from domains.platform.media.api.http import make_router as media_router
    from domains.platform.moderation.api.register import (
        register_moderation as register_platform_moderation,
    )
    from domains.platform.notifications.api.admin_campaigns import (
        make_router as notifications_admin_router,
    )
    from domains.platform.notifications.api.admin_templates import (
        make_router as notifications_templates_router,
    )
    from domains.platform.notifications.api.http import (
        make_router as notifications_router,
    )
    from domains.platform.notifications.api.messages import (
        make_router as notifications_messages_router,
    )
    from domains.platform.notifications.api.ws import (
        make_router as notifications_ws_router,
    )
    from domains.platform.quota.api.http import make_router as quota_router
    from domains.platform.search.api.http import make_router as search_router
    from domains.platform.telemetry.api.admin_http import (
        make_router as telemetry_admin_router,
    )
    from domains.platform.telemetry.api.http import make_router as telemetry_router
    from domains.platform.users.api.http import make_router as users_router
    from domains.product.achievements.api.http import make_router as achievements_router
    from domains.product.ai.api.admin_http import make_router as ai_admin_router
    from domains.product.ai.api.http import make_router as ai_router
    from domains.product.content.api.home_http import (
        make_admin_router as home_admin_router,
    )
    from domains.product.content.api.home_http import (
        make_public_router as home_public_router,
    )
    from domains.product.content.api.http import make_router as content_router
    from domains.product.moderation.api.http import make_router as moderation_router
    from domains.product.navigation.api.http import make_router as navigation_router
    from domains.product.nodes.api import make_admin_router as nodes_admin_router
    from domains.product.nodes.api import make_public_router as nodes_router
    from domains.product.premium.api.http import make_router as premium_router
    from domains.product.profile.api.http import make_router as profile_router
    from domains.product.quests.api.http import make_router as quests_router
    from domains.product.referrals.api.http import make_router as referrals_router
    from domains.product.tags.api.http import make_router as tags_router
    from domains.product.worlds.api.http import make_router as worlds_router

    from .debug import make_router as debug_router

    app.include_router(profile_router())
    app.include_router(settings_router)
    app.include_router(settings_me_router)

    tags_admin_router_factory: Callable[[], Any] | None = None
    try:
        tags_admin_module = import_module("domains.product.tags.api.admin_http")
        tags_admin_router_factory = getattr(tags_admin_module, "make_router", None)
    except ModuleNotFoundError:
        logger.warning("Tags admin router unavailable; skipping admin endpoints")

    if settings.nodes_enabled:
        app.include_router(nodes_router())
        app.include_router(nodes_admin_router())
    if settings.tags_enabled:
        app.include_router(tags_router())
        if callable(tags_admin_router_factory):
            app.include_router(tags_admin_router_factory())
        else:
            logger.debug("Tags admin router skipped: dependency missing")
    if settings.quests_enabled:
        app.include_router(quests_router())
    if settings.navigation_enabled:
        app.include_router(navigation_router())
    if settings.content_enabled:
        app.include_router(content_router())
        app.include_router(home_public_router())
        app.include_router(home_admin_router())
    if settings.ai_enabled:
        app.include_router(ai_router())
        app.include_router(ai_admin_router())
    if settings.moderation_enabled:
        app.include_router(moderation_router())
    if settings.achievements_enabled:
        app.include_router(achievements_router())
    if settings.worlds_enabled:
        app.include_router(worlds_router())
    if settings.referrals_enabled:
        app.include_router(referrals_router())
    if settings.premium_enabled:
        app.include_router(premium_router())

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

    if getattr(settings, "enable_debug_routes", False):
        if settings.env == "prod":
            logger.warning("Debug router requested in prod; skipping registration")
        else:
            app.include_router(debug_router())


def create_app(
    *,
    settings: Settings | None = None,
    container_factory: Callable[[], Container] = build_container,
) -> FastAPI:
    settings = settings or load_settings()
    lifespan = create_lifespan(settings, container_factory=container_factory)
    app = FastAPI(
        lifespan=lifespan, swagger_ui_parameters={"persistAuthorization": True}
    )
    app.state.settings = settings

    _configure_observability(app, service_name="backend")
    try:
        setup_http_metrics(app)
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.exception("Failed to configure HTTP metrics", exc_info=exc)
    _configure_cors(app, settings)
    _setup_openapi_security(app, settings)
    _register_exception_handlers(app)
    _register_core_routers(app, settings)
    _register_health_routes(app, settings)

    return app


app = create_app()


__all__ = ["app", "create_app"]
