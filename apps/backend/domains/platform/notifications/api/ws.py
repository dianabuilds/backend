from __future__ import annotations

import logging
from typing import Any

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jwt import PyJWTError

from packages.core.config import load_settings

logger = logging.getLogger(__name__)


def make_router() -> APIRouter:
    router = APIRouter()

    @router.websocket("/v1/notifications/ws")
    async def notifications_ws(websocket: WebSocket) -> None:
        await websocket.accept()  # tentative accept to read cookies/headers
        app_settings = getattr(getattr(websocket.app, "state", None), "settings", None)
        s = app_settings if app_settings is not None else load_settings()

        candidates: list[tuple[str, str]] = []
        query_token = (
            websocket.query_params.get("token") if websocket.query_params else None
        )
        if query_token:
            trimmed = query_token.strip()
            if trimmed:
                candidates.append(("query", trimmed))
        auth_header = websocket.headers.get("authorization")
        if auth_header:
            scheme, _, credential = auth_header.partition(" ")
            if scheme.lower() == "bearer" and credential:
                trimmed = credential.strip()
                if trimmed:
                    candidates.append(("header", trimmed))
        cookie_token = websocket.cookies.get("access_token")
        if cookie_token:
            trimmed = cookie_token.strip()
            if trimmed:
                candidates.append(("cookie", trimmed))

        user_id: str | None = None
        for _source, token in candidates:
            logger.info(
                "notifications.ws.candidate source=%s len=%s head=%s",
                _source,
                len(token),
                token[:16],
            )
            try:
                claims: dict[str, Any] = jwt.decode(
                    token,
                    key=s.auth_jwt_secret.get_secret_value(),
                    algorithms=[s.auth_jwt_algorithm],
                    options={"verify_aud": False},
                )
                user_id = str(claims.get("sub") or "")
                if user_id:
                    break
            except (PyJWTError, ValueError) as exc:
                logger.info(
                    "notifications.ws.jwt_invalid source=%s error=%s",
                    _source,
                    exc,
                )
                continue
        if not user_id:
            refresh_token = websocket.cookies.get("refresh_token")
            if refresh_token:
                try:
                    claims = jwt.decode(
                        refresh_token,
                        key=s.auth_jwt_secret.get_secret_value(),
                        algorithms=[s.auth_jwt_algorithm],
                        options={"verify_aud": False},
                    )
                    if claims.get("typ") == "refresh":
                        user_id = str(claims.get("sub") or "")
                        if user_id:
                            logger.info("notifications.ws.auth_via_refresh")
                except (PyJWTError, ValueError):
                    logger.info("notifications.ws.refresh_invalid")
        if not user_id:
            logger.info(
                "notifications.ws.no_token",
                extra={
                    "sources": [source for source, _ in candidates],
                    "cookie_keys": list(websocket.cookies.keys()),
                },
            )
            await websocket.close(code=4401)
            return
        # Get manager from app container
        try:
            container = websocket.app.state.container  # type: ignore[attr-defined]
            manager = container.notifications.ws_manager
        except AttributeError:
            await websocket.close(code=1011)
            return
        await manager.connect(user_id, websocket)
        try:
            while True:
                # Keep-alive loop; receive and ignore pings/messages from client
                await websocket.receive_text()
        except WebSocketDisconnect as exc:
            logger.info(
                "notifications.ws.disconnect code=%s reason=%s",
                getattr(exc, "code", None),
                getattr(exc, "reason", None),
            )
            await manager.disconnect(user_id, websocket)
        except (RuntimeError, ConnectionError, OSError) as exc:
            logger.info("notifications.ws.error_disconnect", exc_info=exc)
            await manager.disconnect(user_id, websocket)

    return router
