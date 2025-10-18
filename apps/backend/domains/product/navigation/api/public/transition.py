from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend.app.api_gateway.routers import get_container
from apps.backend.infra.security.rate_limits import PUBLIC_RATE_LIMITS
from domains.platform.iam.application.facade import csrf_protect, get_current_user
from domains.product.navigation.application.use_cases.transition import (
    TransitionCommand,
    TransitionError,
    TransitionHandler,
    build_transition_handler,
)


def register_transition_routes(router: APIRouter) -> None:
    """Attach public navigation transition endpoints."""

    NAVIGATION_PUBLIC_RATE_LIMIT = PUBLIC_RATE_LIMITS["navigation"].as_dependencies()

    @router.post(
        "/next",
        dependencies=NAVIGATION_PUBLIC_RATE_LIMIT,
    )
    def next_step(
        body: dict,
        req: Request,
        handler: TransitionHandler = Depends(_get_handler),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        command = TransitionCommand(
            body=body,
            claims=claims,
            session_id_header=req.headers.get("x-session-id"),
            session_id_cookie=req.cookies.get("session_id"),
        )
        try:
            result = handler.execute(command)
        except TransitionError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
        return result.payload


def _get_handler(container=Depends(get_container)) -> TransitionHandler:
    return build_transition_handler(container)
