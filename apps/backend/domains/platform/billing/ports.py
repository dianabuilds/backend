from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from domains.platform.billing.domain.models import Plan, Subscription

JsonDict = dict[str, Any]
JsonDictList = list[JsonDict]


@dataclass
class CheckoutResult:
    url: str | None
    provider: str
    external_id: str
    payload: JsonDict | None = None
    meta: JsonDict | None = None
    expires_at: str | None = None


@dataclass
class BillingSummary:
    plan: JsonDict | None
    subscription: JsonDict | None


@dataclass
class BillingHistory:
    items: JsonDictList
    coming_soon: bool = False


class PaymentProvider(Protocol):
    async def checkout(self, user_id: str, plan: Plan) -> CheckoutResult: ...
    async def verify_webhook(self, payload: bytes, signature: str | None) -> bool: ...


class PlanRepo(Protocol):
    async def list_active(self) -> list[Plan]: ...
    async def list_all(self) -> list[Plan]: ...
    async def get_by_slug(self, slug: str) -> Plan | None: ...
    async def get_by_id(self, plan_id: str) -> Plan | None: ...
    async def upsert(self, p: JsonDict) -> Plan: ...
    async def delete(self, plan_id: str) -> None: ...


class SubscriptionRepo(Protocol):
    async def get_active_for_user(self, user_id: str) -> Subscription | None: ...
    async def activate(
        self,
        user_id: str,
        plan_id: str,
        auto_renew: bool = True,
        ends_at: str | None = None,
    ) -> Subscription: ...


class LedgerRepo(Protocol):
    async def add_tx(self, tx: JsonDict) -> None: ...
    async def list_for_user(self, user_id: str, limit: int = 20) -> JsonDictList: ...

    # Optional convenience methods for admin listings
    async def list_recent(self, limit: int = 100) -> JsonDictList: ...
    async def get_by_external_id(self, external_id: str) -> JsonDict | None: ...
    async def get_by_tx_hash(self, tx_hash: str) -> JsonDict | None: ...
    async def update_transaction(
        self,
        transaction_id: str,
        *,
        status: str,
        tx_hash: str | None = None,
        network: str | None = None,
        token: str | None = None,
        confirmed_at: Any | None = None,
        failure_reason: str | None = None,
        meta_patch: JsonDict | None = None,
    ) -> JsonDict: ...
    async def list_pending(
        self, *, older_than_seconds: int, limit: int = 100
    ) -> JsonDictList: ...


class GatewayRepo(Protocol):
    async def list(self) -> JsonDictList: ...
    async def upsert(self, g: JsonDict) -> JsonDict: ...
    async def delete(self, slug: str) -> None: ...


class ContractsRepo(Protocol):
    async def list(self) -> JsonDictList: ...
    async def upsert(self, c: JsonDict) -> JsonDict: ...
    async def delete(self, id_or_slug: str) -> None: ...
    async def get(self, id_or_slug: str) -> JsonDict | None: ...
    async def get_by_address(self, address: str) -> JsonDict | None: ...
    async def list_events(
        self, id_or_slug: str | None, limit: int = 100
    ) -> JsonDictList: ...
    async def add_event(self, e: JsonDict) -> None: ...
    async def metrics_methods(
        self, id_or_slug: str | None, window: int = 1000
    ) -> JsonDictList: ...
    async def metrics_methods_ts(
        self, id_or_slug: str | None, days: int = 30
    ) -> JsonDictList: ...
    async def metrics_volume_ts(
        self, id_or_slug: str | None, days: int = 30
    ) -> JsonDictList: ...


class CryptoConfigRepo(Protocol):
    async def get(self, slug: str) -> JsonDict | None: ...
    async def set(self, slug: str, cfg: JsonDict) -> JsonDict: ...


class BillingAnalyticsRepo(Protocol):
    async def kpi(self) -> JsonDict: ...
    async def subscription_metrics(self) -> JsonDict: ...
    async def revenue_timeseries(self, days: int = 30) -> JsonDictList: ...
    async def network_breakdown(self) -> JsonDictList: ...


class BillingSummaryRepo(Protocol):
    async def get_summary(self, user_id: str) -> BillingSummary: ...


class BillingHistoryRepo(Protocol):
    async def get_history(self, user_id: str, limit: int = 20) -> BillingHistory: ...


class EventPublisher(Protocol):
    def publish(
        self, topic: str, payload: JsonDict, key: str | None = None
    ) -> None: ...


class NotificationService(Protocol):
    async def create_notification(self, command: Any) -> Any: ...


__all__ = [
    "PaymentProvider",
    "CheckoutResult",
    "PlanRepo",
    "SubscriptionRepo",
    "LedgerRepo",
    "GatewayRepo",
    "ContractsRepo",
    "CryptoConfigRepo",
    "BillingAnalyticsRepo",
    "BillingSummary",
    "BillingHistory",
    "BillingSummaryRepo",
    "BillingHistoryRepo",
    "EventPublisher",
    "NotificationService",
]
