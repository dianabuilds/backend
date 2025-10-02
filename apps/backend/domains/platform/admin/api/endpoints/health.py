from __future__ import annotations

from fastapi import APIRouter


def register(router: APIRouter) -> None:
    @router.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    @router.get("/readyz")
    async def readyz() -> dict[str, bool]:
        return {"ok": True}
