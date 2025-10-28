from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.ports import BillingHistory, BillingHistoryRepo
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


class SQLBillingHistoryRepo(BillingHistoryRepo):
    """SQL adapter that exposes user transaction history."""

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def get_history(self, user_id: str, limit: int = 20) -> BillingHistory:
        safe_limit = int(max(1, min(limit, 100)))
        query = text(
            """
            SELECT id,
                   gateway_slug,
                   product_type,
                   product_id,
                   currency,
                   token,
                   network,
                   gross_cents,
                   status,
                   created_at,
                   confirmed_at,
                   failure_reason,
                   tx_hash,
                   meta
            FROM payment_transactions
            WHERE user_id = cast(:uid AS uuid)
            ORDER BY created_at DESC
            LIMIT :lim
            """
        )
        try:
            async with self._engine.begin() as conn:
                rows = (
                    (await conn.execute(query, {"uid": user_id, "lim": safe_limit}))
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            logger.warning(
                "Failed to load billing history for user %s: %s",
                user_id,
                exc,
                exc_info=exc,
            )
            return BillingHistory(items=[], coming_soon=True)

        items = []
        for row in rows:
            gross = row.get("gross_cents")
            amount = _to_amount(gross)
            amount_cents = _to_int(gross)
            meta = row.get("meta") or {}
            if not isinstance(meta, dict):
                try:
                    meta = dict(meta)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    meta = {}
            items.append(
                {
                    "id": _to_str(row.get("id")),
                    "status": row.get("status"),
                    "created_at": row.get("created_at"),
                    "confirmed_at": row.get("confirmed_at"),
                    "amount": amount,
                    "amount_cents": amount_cents,
                    "currency": row.get("currency"),
                    "token": row.get("token"),
                    "network": row.get("network"),
                    "tx_hash": row.get("tx_hash"),
                    "failure_reason": row.get("failure_reason"),
                    "provider": row.get("gateway_slug"),
                    "product_type": row.get("product_type"),
                    "product_id": _to_str(row.get("product_id")),
                    "gas": _extract_gas(meta),
                    "meta": meta,
                }
            )
        return BillingHistory(items=items, coming_soon=False)


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if isinstance(value, Decimal):
        return int(value)
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(text, 0) if text.startswith(("0x", "0X")) else int(text)
    except (TypeError, ValueError):
        return None


def _to_amount(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        cents = float(value)
    elif isinstance(value, (int, float)):
        cents = float(value)
    else:
        try:
            cents = float(value)
        except (TypeError, ValueError):
            return None
    return cents / 100.0


def _normalize_number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text, 0)
        except ValueError:
            try:
                number = float(text)
            except ValueError:
                return None
            return int(number) if number.is_integer() else number
    return None


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)


def _normalize_gas(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key in ("used", "limit", "price", "fee", "amount"):
            number = _normalize_number(value.get(key))
            if number is not None:
                field = "fee" if key == "amount" else key
                normalized[field] = number
        for key in ("token", "currency", "unit", "note", "source"):
            text = _normalize_text(value.get(key))
            if text is not None:
                normalized[key] = text
        return normalized or None
    number = _normalize_number(value)
    if number is not None:
        return {"fee": number}
    text = _normalize_text(value)
    if text:
        return {"note": text}
    return None


def _extract_gas(meta: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(meta, dict):
        return None
    candidates: list[Any] = []
    if "gas" in meta:
        candidates.append(meta.get("gas"))
    provider_meta = meta.get("provider_meta")
    if isinstance(provider_meta, dict):
        if "gas" in provider_meta:
            candidates.append(provider_meta.get("gas"))
    webhook_event = meta.get("webhook_event")
    if isinstance(webhook_event, dict):
        if "gas" in webhook_event:
            candidates.append(webhook_event.get("gas"))
        else:
            candidate = {
                "used": webhook_event.get("gas_used"),
                "price": webhook_event.get("gas_price"),
                "fee": webhook_event.get("gas_fee"),
                "token": webhook_event.get("gas_token") or webhook_event.get("token"),
            }
            if any(value is not None for value in candidate.values()):
                candidates.append(candidate)
    for candidate in candidates:
        normalized = _normalize_gas(candidate)
        if normalized:
            return normalized
    return None


__all__ = ["SQLBillingHistoryRepo"]
