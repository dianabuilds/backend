from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix=f"/{{'{{'}}domain{{'}}'}}", tags=["{{DOMAIN}}"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

__all__ = ["router"]

