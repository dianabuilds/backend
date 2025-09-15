from __future__ import annotations

from typing import Any

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from packages.core.config import load_settings


def make_router() -> APIRouter:
    router = APIRouter()

    @router.websocket("/v1/notifications/ws")
    async def notifications_ws(websocket: WebSocket) -> None:
        await websocket.accept()  # tentative accept to read cookies/headers
        s = load_settings()
        token = websocket.cookies.get("access_token") or None
        if not token:
            # allow token via query for dev
            token = (
                websocket.query_params.get("token") if websocket.query_params else None
            )
        user_id: str | None = None
        if token:
            try:
                claims: dict[str, Any] = jwt.decode(
                    token,
                    key=s.auth_jwt_secret,
                    algorithms=[s.auth_jwt_algorithm],
                    options={"verify_aud": False},
                )
                user_id = str(claims.get("sub") or "")
            except Exception:
                pass
        if not user_id:
            await websocket.close(code=4401)
            return
        # Get manager from app container
        try:
            container = websocket.app.state.container  # type: ignore[attr-defined]
            manager = container.notifications.ws_manager
        except Exception:
            await websocket.close(code=1011)
            return
        await manager.connect(user_id, websocket)
        try:
            while True:
                # Keep-alive loop; receive and ignore pings/messages from client
                await websocket.receive_text()
        except WebSocketDisconnect:
            await manager.disconnect(user_id, websocket)
        except Exception:
            await manager.disconnect(user_id, websocket)

    return router
