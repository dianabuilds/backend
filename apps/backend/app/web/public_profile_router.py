from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.achievements.application.achievements_service import AchievementsService
from app.domains.achievements.infrastructure.repositories.achievements_repository import (
    AchievementsRepository,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db

router = APIRouter(tags=["public-profile"])

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/u/{username}", include_in_schema=False)
async def public_profile(
    request: Request,
    username: str,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> HTMLResponse:
    # Fetch user by username
    res = await db.execute(select(User).where(User.username == username))
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Achievements (unlocked only)
    ach_repo = AchievementsRepository(db)
    svc = AchievementsService(ach_repo)
    rows = await svc.list(user.id)
    unlocked = [
        {
            "id": str(a.id),
            "title": a.title,
            "icon": a.icon,
        }
        for (a, ua) in rows
        if ua is not None
    ]

    context = {
        "request": request,
        "username": user.username or "",
        "bio": user.bio or "",
        "avatar_url": user.avatar_url or "",
        "is_premium": bool(user.is_premium),
        "achievements": unlocked,
        "public_url": f"/u/{user.username}",
    }
    return templates.TemplateResponse("public_profile.html", context)
