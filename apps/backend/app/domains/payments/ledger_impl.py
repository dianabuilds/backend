from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.payments.infrastructure.models.payment_models import (
    PaymentGatewayConfig,
    PaymentTransaction,
)


def _round_cents(x: float) -> int:
    return int(x + 0.5) if x >= 0 else -int((-x) + 0.5)


def _compute_fee_from_config(
    cfg: dict[str, Any] | None, gross_cents: int, currency: str | None
) -> tuple[int, dict[str, Any]]:
    cfg = cfg or {}
    mode = (cfg.get("fee_mode") or "").lower()
    pct = float(cfg.get("fee_percent") or 0.0)
    fixed = int(cfg.get("fee_fixed_cents") or 0)
    min_fee = int(cfg.get("min_fee_cents") or 0)

    fee = 0
    if mode == "percent":
        fee = _round_cents(gross_cents * (pct / 100.0))
    elif mode == "fixed":
        fee = fixed
    elif mode == "mixed":
        fee = _round_cents(gross_cents * (pct / 100.0)) + fixed
    else:
        fee = 0

    if min_fee and fee < min_fee:
        fee = min_fee
    if fee < 0:
        fee = 0
    if fee > gross_cents:
        fee = gross_cents

    meta = {
        "fee": {
            "mode": mode or "none",
            "percent": pct,
            "fixed_cents": fixed,
            "min_fee_cents": min_fee,
        }
    }
    return fee, meta


async def capture_transaction(
    db: AsyncSession,
    *,
    user_id,
    gateway_slug: str | None,
    product_type: str,
    product_id,
    gross_cents: int,
    currency: str | None = "USD",
    status: str = "captured",
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg: dict[str, Any] | None = None
    if gateway_slug:
        res = await db.execute(
            select(PaymentGatewayConfig).where(
                PaymentGatewayConfig.slug == gateway_slug
            )
        )
        gw = res.scalars().first()
        if gw:
            cfg = gw.config or {}

    fee_cents, meta_fee = _compute_fee_from_config(cfg, gross_cents, currency)
    net_cents = max(gross_cents - fee_cents, 0)
    meta: dict[str, Any] = {"currency": currency, **meta_fee}
    if extra_meta:
        meta.update(extra_meta)

    tx = PaymentTransaction(
        user_id=user_id,
        gateway_slug=gateway_slug or None,
        product_type=product_type,
        product_id=product_id,
        currency=currency or "USD",
        gross_cents=int(gross_cents),
        fee_cents=int(fee_cents),
        net_cents=int(net_cents),
        status=status,
        meta=meta,
    )
    db.add(tx)
    await db.flush()

    return {
        "transaction_id": str(tx.id),
        "gateway": gateway_slug,
        "gross_cents": gross_cents,
        "fee_cents": fee_cents,
        "net_cents": net_cents,
        "currency": currency or "USD",
    }
