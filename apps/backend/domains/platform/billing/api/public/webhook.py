from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from domains.platform.billing.application.use_cases.exceptions import (
    BillingUseCaseError,
)

from ..deps import get_public_use_cases


def register(router: APIRouter) -> None:
    @router.post("/webhook")
    async def webhook(
        req: Request,
        use_cases=Depends(get_public_use_cases),
    ) -> dict[str, Any]:
        payload = await req.body()
        signature = req.headers.get("X-Signature") or req.headers.get("x-signature")
        try:
            return await use_cases.handle_webhook(payload=payload, signature=signature)
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.post("/contracts/webhook")
    async def contracts_webhook(
        req: Request,
        use_cases=Depends(get_public_use_cases),
    ) -> dict[str, Any]:
        raw = await req.body()
        signature = req.headers.get("X-Signature") or req.headers.get("x-signature")
        try:
            return await use_cases.handle_contracts_webhook(
                raw_body=raw, signature=signature
            )
        except BillingUseCaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
