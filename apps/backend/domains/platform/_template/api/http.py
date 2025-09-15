from __future__ import annotations

from fastapi import APIRouter


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/<your_domain>")

    @router.post("/operate")
    def operate(body: dict) -> dict:  # pragma: no cover - template
        # TODO: вызовите логику/диспетчер
        return {"ok": True, "echo": body}

    return router
