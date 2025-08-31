from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol

import jwt
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.payments.application.payments_service import (
    payment_service,  # domain fallback
)
from app.domains.payments.infrastructure.models.payment_models import (
    PaymentGatewayConfig,
)
from app.domains.premium.infrastructure.models.premium_models import UserSubscription


class PaymentGateway(Protocol):
    slug: str
    type: str

    async def verify(
        self, *, token: str, amount: int, currency: str | None = None
    ) -> bool: ...


class CryptoJWTGateway:
    def __init__(self, slug: str, cfg: dict[str, Any]) -> None:
        self.slug = slug
        self.type = "crypto_jwt"
        self.secret = str(cfg.get("jwt_secret", "") or cfg.get("secret", ""))
        self.alg = str(cfg.get("jwt_algorithm", "HS256"))
        self.expected_currency = cfg.get("currency")

    async def verify(
        self, *, token: str, amount: int, currency: str | None = None
    ) -> bool:
        try:
            data = jwt.decode(token, self.secret, algorithms=[self.alg])
        except jwt.PyJWTError:
            return False
        if int(data.get("amount") or -1) != int(amount):
            return False
        if self.expected_currency and (data.get("currency") != self.expected_currency):
            return False
        if currency and data.get("currency") and data.get("currency") != currency:
            return False
        return True


class StripeJWTGateway:
    def __init__(self, slug: str, cfg: dict[str, Any]) -> None:
        self.slug = slug
        self.type = "stripe_jwt"
        self.secret = str(cfg.get("jwt_secret", "") or cfg.get("secret", ""))
        self.alg = str(cfg.get("jwt_algorithm", "HS256"))

    async def verify(
        self, *, token: str, amount: int, currency: str | None = None
    ) -> bool:
        try:
            data = jwt.decode(token, self.secret, algorithms=[self.alg])
        except jwt.PyJWTError:
            return False
        if int(data.get("amount") or -1) != int(amount):
            return False
        if currency and data.get("currency") and data.get("currency") != currency:
            return False
        return True


def _build_gateway(pg: PaymentGatewayConfig) -> PaymentGateway | None:
    cfg = pg.config or {}
    t = (pg.type or "").lower()
    if t == "crypto_jwt":
        return CryptoJWTGateway(pg.slug, cfg)
    if t == "stripe_jwt":
        return StripeJWTGateway(pg.slug, cfg)
    return None


async def load_active_gateways(db: AsyncSession) -> list[PaymentGateway]:
    res = await db.execute(
        select(PaymentGatewayConfig)
        .where(PaymentGatewayConfig.enabled.is_(True))
        .order_by(PaymentGatewayConfig.priority.asc())
    )
    items = list(res.scalars().all())
    out: list[PaymentGateway] = []
    for it in items:
        g = _build_gateway(it)
        if g:
            out.append(g)
    return out


async def verify_payment(
    db: AsyncSession,
    *,
    amount: int,
    currency: str | None,
    token: str,
    preferred_slug: str | None = None,
) -> tuple[bool, str | None]:
    gateways = await load_active_gateways(db)
    if not gateways:
        ok = await payment_service.verify(token, amount)
        return ok, "legacy"

    order: list[PaymentGateway] = gateways[:]
    if preferred_slug:
        order.sort(key=lambda g: (g.slug != preferred_slug, g.slug))
    else:
        try:
            data = jwt.decode(
                token, options={"verify_signature": False, "verify_exp": False}
            )  # type: ignore[arg-type]
            gw = data.get("gateway")
            if gw:
                order.sort(key=lambda g: (g.slug != gw, g.slug))
        except Exception:
            pass

    for gw in order:
        ok = await gw.verify(token=token, amount=amount, currency=currency)
        if ok:
            return True, gw.slug
    return False, None


async def get_active_subscriptions_stats(
    db: AsyncSession,
) -> tuple[int, float]:
    """Return current active subscriptions count and pct change vs last week."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    current_q = (
        select(func.count())
        .select_from(UserSubscription)
        .where(
            UserSubscription.status == "active",
            UserSubscription.started_at <= now,
            or_(
                UserSubscription.ends_at.is_(None),
                UserSubscription.ends_at > now,
            ),
        )
    )
    current = (await db.execute(current_q)).scalar() or 0

    past_q = (
        select(func.count())
        .select_from(UserSubscription)
        .where(
            UserSubscription.status == "active",
            UserSubscription.started_at <= week_ago,
            or_(
                UserSubscription.ends_at.is_(None),
                UserSubscription.ends_at > week_ago,
            ),
        )
    )
    past = (await db.execute(past_q)).scalar() or 0

    pct_change = ((current - past) / past * 100.0) if past else 0.0
    return current, pct_change
