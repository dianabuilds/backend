from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.db.session import get_db
from app.security import authenticate_admin  # placeholder for real helper

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login")
async def login_action(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        data = await request.json()
        username = (data or {}).get("username")
        password = (data or {}).get("password")
    else:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

    tokens = await authenticate_admin(db, username, password)

    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie("access_token", tokens.access_token, httponly=True, samesite="lax", path="/")
    if getattr(tokens, "refresh_token", None):
        response.set_cookie(
            "refresh_token",
            tokens.refresh_token,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return response


__all__ = ["router"]

