from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:  # pragma: no cover - optional dependency
    from prometheus_client import REGISTRY, Counter, Gauge  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Counter = None  # type: ignore
    Gauge = None  # type: ignore
    REGISTRY = None  # type: ignore

_SUCCESS_STATUSES = {"succeeded", "captured", "completed", "success"}


def _sanitize(value: object | None, *, default: str = "unknown") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
    else:
        try:
            text = str(value).strip()
        except (TypeError, ValueError):
            return default
    return text or default


def _coerce_float(value: object | None, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return float(text)
        except ValueError:
            return default
    return default


def _build_counter(
    name: str, documentation: str, *, labelnames: Iterable[str]
):  # pragma: no cover - thin wrapper
    if Counter is None:
        return None
    try:
        return Counter(name, documentation, labelnames=tuple(labelnames))  # type: ignore[misc]
    except ValueError:
        registry: Any | None = REGISTRY  # type: ignore[assignment]
        if registry is not None:
            existing = getattr(registry, "_names_to_collectors", {}).get(name)
            if existing is not None:
                return existing
        return None


def _build_gauge(
    name: str, documentation: str, *, labelnames: Iterable[str] = ()
):  # pragma: no cover - thin wrapper
    if Gauge is None:
        return None
    try:
        return Gauge(name, documentation, labelnames=tuple(labelnames))  # type: ignore[misc]
    except ValueError:
        registry: Any | None = REGISTRY  # type: ignore[assignment]
        if registry is not None:
            existing = getattr(registry, "_names_to_collectors", {}).get(name)
            if existing is not None:
                return existing
        return None


TRANSACTIONS_TOTAL = _build_counter(
    "billing_transactions_total",
    "Total billing transactions observed by status and origin.",
    labelnames=("status", "network", "token", "source"),
)
TRANSACTION_VALUE_USD = _build_counter(
    "billing_transaction_value_usd_total",
    "Accumulated transaction volume in USD-equivalent.",
    labelnames=("network", "token", "source"),
)
CONTRACT_EVENTS_TOTAL = _build_counter(
    "billing_contract_events_total",
    "Total contract events processed.",
    labelnames=("event", "status", "chain_id", "method"),
)

SUBSCRIPTIONS_ACTIVE = _build_gauge(
    "billing_subscriptions_active",
    "Active user subscriptions.",
)
SUBSCRIPTIONS_MRR = _build_gauge(
    "billing_subscriptions_mrr_usd",
    "Monthly recurring revenue (USD).",
)
SUBSCRIPTIONS_ARPU = _build_gauge(
    "billing_subscriptions_arpu_usd",
    "Average revenue per user (USD).",
)
SUBSCRIPTIONS_CHURN = _build_gauge(
    "billing_subscriptions_churn_ratio",
    "30 day churn ratio.",
)
SUBSCRIPTIONS_BY_TOKEN = _build_gauge(
    "billing_subscriptions_token_total",
    "Active subscriptions grouped by pricing token.",
    labelnames=("token",),
)
SUBSCRIPTIONS_TOKEN_MRR = _build_gauge(
    "billing_subscriptions_token_mrr_usd",
    "MRR grouped by pricing token (USD).",
    labelnames=("token",),
)
SUBSCRIPTIONS_BY_NETWORK = _build_gauge(
    "billing_subscriptions_network_total",
    "Active subscriptions grouped by contract network.",
    labelnames=("network", "chain_id"),
)
NETWORK_VOLUME = _build_gauge(
    "billing_transactions_network_volume_usd",
    "Transaction volume per network/token in USD.",
    labelnames=("network", "token"),
)
NETWORK_FAILED = _build_gauge(
    "billing_transactions_network_failed_total",
    "Failed transactions per network/token.",
    labelnames=("network", "token"),
)
NETWORK_PENDING = _build_gauge(
    "billing_transactions_network_pending_total",
    "Pending transactions per network/token.",
    labelnames=("network", "token"),
)
CONTRACT_INVENTORY = _build_gauge(
    "billing_contracts_inventory_total",
    "Contracts inventory grouped by status/testnet flag.",
    labelnames=("label",),
)


def observe_transaction(
    status: str | None,
    *,
    network: str | None = None,
    token: str | None = None,
    source: str = "unknown",
    amount_cents: int | float | None = None,
) -> None:
    """Record transaction level metrics (no-op when Prometheus disabled)."""

    status_label = _sanitize(status)
    network_label = _sanitize(network)
    token_label = _sanitize(token, default="N/A")
    source_label = _sanitize(source, default="unknown")

    if TRANSACTIONS_TOTAL is not None:
        TRANSACTIONS_TOTAL.labels(
            status=status_label,
            network=network_label,
            token=token_label,
            source=source_label,
        ).inc()

    if (
        amount_cents is not None
        and status_label in _SUCCESS_STATUSES
        and TRANSACTION_VALUE_USD is not None
    ):
        usd = float(amount_cents) / 100.0
        TRANSACTION_VALUE_USD.labels(
            network=network_label,
            token=token_label,
            source=source_label,
        ).inc(usd)


def set_subscription_metrics(
    *,
    active: int,
    mrr: float,
    arpu: float,
    churn_ratio: float,
    per_token: Iterable[dict[str, object]] | None = None,
    per_network: Iterable[dict[str, object]] | None = None,
) -> None:
    """Expose subscription gauges."""

    if SUBSCRIPTIONS_ACTIVE is not None:
        SUBSCRIPTIONS_ACTIVE.set(float(active))
    if SUBSCRIPTIONS_MRR is not None:
        SUBSCRIPTIONS_MRR.set(float(mrr))
    if SUBSCRIPTIONS_ARPU is not None:
        SUBSCRIPTIONS_ARPU.set(float(arpu))
    if SUBSCRIPTIONS_CHURN is not None:
        SUBSCRIPTIONS_CHURN.set(float(churn_ratio))

    if SUBSCRIPTIONS_BY_TOKEN is not None and per_token is not None:
        for item in per_token:
            if not isinstance(item, dict):
                continue
            token_label = _sanitize(item.get("token"), default="N/A")
            total = _coerce_float(item.get("total"))
            SUBSCRIPTIONS_BY_TOKEN.labels(token=token_label).set(total)
            if SUBSCRIPTIONS_TOKEN_MRR is not None:
                mrr_usd = _coerce_float(item.get("mrr_usd"))
                SUBSCRIPTIONS_TOKEN_MRR.labels(token=token_label).set(mrr_usd)

    if SUBSCRIPTIONS_BY_NETWORK is not None and per_network is not None:
        for item in per_network:
            if not isinstance(item, dict):
                continue
            network_label = _sanitize(item.get("network"))
            chain_label = _sanitize(item.get("chain_id"))
            total = _coerce_float(item.get("total"))
            SUBSCRIPTIONS_BY_NETWORK.labels(
                network=network_label, chain_id=chain_label
            ).set(total)


def set_network_metrics(rows: Iterable[dict[str, object]]) -> None:
    """Expose network breakdown gauges."""

    if NETWORK_VOLUME is None or NETWORK_FAILED is None or NETWORK_PENDING is None:
        return

    for row in rows:
        if not isinstance(row, dict):
            continue
        network_label = _sanitize(row.get("network"))
        token_label = _sanitize(row.get("token"), default="N/A")
        volume = _coerce_float(row.get("volume"))
        failed = _coerce_float(row.get("failed"))
        pending = _coerce_float(row.get("pending"))
        NETWORK_VOLUME.labels(network=network_label, token=token_label).set(volume)
        NETWORK_FAILED.labels(network=network_label, token=token_label).set(failed)
        NETWORK_PENDING.labels(network=network_label, token=token_label).set(pending)


def set_contract_inventory(stats: dict[str, int]) -> None:
    """Expose contract inventory gauges."""

    if CONTRACT_INVENTORY is None:
        return
    for key, value in stats.items():
        CONTRACT_INVENTORY.labels(label=_sanitize(key)).set(float(value))


def observe_contract_event(
    *,
    event: str | None,
    status: str | None,
    chain_id: str | None,
    method: str | None,
) -> None:
    """Record contract events metric."""

    if CONTRACT_EVENTS_TOTAL is None:
        return
    CONTRACT_EVENTS_TOTAL.labels(
        event=_sanitize(event),
        status=_sanitize(status),
        chain_id=_sanitize(chain_id),
        method=_sanitize(method, default="unknown"),
    ).inc()


__all__ = [
    "observe_transaction",
    "set_subscription_metrics",
    "set_network_metrics",
    "set_contract_inventory",
    "observe_contract_event",
]
