from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from domains.platform.audit.application.service import AuditService
from domains.platform.audit.infrastructure import AuditLogPayload, safe_audit_log
from domains.platform.billing import metrics as billing_metrics
from domains.platform.billing.domain.models import Plan, Subscription
from domains.platform.billing.ports import (
    BillingHistoryRepo,
    BillingSummaryRepo,
    CheckoutResult,
    EventPublisher,
    LedgerRepo,
    NotificationService,
    PaymentProvider,
    PlanRepo,
    SubscriptionRepo,
)
from domains.platform.notifications.application.interactors.commands import (
    NotificationCreateCommand,
)

logger = logging.getLogger(__name__)


_SUCCESS_STATUSES = {"success", "succeeded", "captured", "completed"}
_FAILURE_STATUSES = {"failed", "declined", "error"}
_REFUND_STATUSES = {"refunded", "reversed"}


@dataclass
class BillingService:
    plans: PlanRepo
    subs: SubscriptionRepo
    ledger: LedgerRepo
    provider: PaymentProvider
    summary_repo: BillingSummaryRepo
    history_repo: BillingHistoryRepo
    events: EventPublisher | None = None
    notify_service: NotificationService | None = None
    audit_service: AuditService | None = None
    finance_ops_recipient: str | None = None

    async def list_plans(self) -> list[Plan]:
        return await self.plans.list_active()

    async def checkout(
        self, user_id: str, plan_slug: str, *, idempotency_key: str | None = None
    ) -> CheckoutResult:
        plan = await self.plans.get_by_slug(plan_slug)
        if not plan:
            raise ValueError("plan_not_found")
        result = await self.provider.checkout(user_id, plan)
        provider_meta = result.meta or {}
        token = provider_meta.get("token") or plan.price_token
        network = provider_meta.get("network")
        gross_cents = int(plan.price_cents or 0)
        meta_payload: dict[str, Any] = {
            "plan": {"id": plan.id, "slug": plan.slug},
            "checkout_external_id": result.external_id,
        }
        if idempotency_key:
            meta_payload["idempotency_key"] = idempotency_key
        if result.payload is not None:
            meta_payload["provider_payload"] = result.payload
        if provider_meta:
            meta_payload["provider_meta"] = provider_meta
        transaction_payload = {
            "user_id": user_id,
            "gateway_slug": result.provider,
            "product_type": "subscription_plan",
            "product_id": plan.id,
            "currency": plan.currency,
            "token": token,
            "network": network,
            "gross_cents": gross_cents,
            "fee_cents": 0,
            "net_cents": gross_cents,
            "tx_hash": None,
            "status": "pending",
            "meta": meta_payload,
        }
        try:
            await self.ledger.add_tx(transaction_payload)
        except Exception as exc:
            logger.warning(
                "Failed to persist pending transaction for checkout %s: %s",
                result.external_id,
                exc,
                exc_info=exc,
                extra={
                    "user_id": user_id,
                    "plan_slug": plan.slug,
                    "gateway": result.provider,
                    "tx_status": "pending",
                    "checkout_external_id": result.external_id,
                    "contract_slug": plan.contract_slug,
                },
            )
        else:
            billing_metrics.observe_transaction(
                "pending",
                network=network,
                token=token,
                source="checkout",
                amount_cents=gross_cents,
            )
        return result

    async def handle_webhook(
        self, payload: bytes, signature: str | None
    ) -> dict[str, Any]:
        ok = await self.provider.verify_webhook(payload, signature)
        if not ok:
            return {"ok": False, "reason": "invalid_signature"}
        try:
            data = json.loads(payload.decode("utf-8"))
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as exc:  # pragma: no cover - defensive
            logger.warning("billing webhook json decode failed: %s", exc, exc_info=exc)
            return {"ok": False, "reason": "invalid_json"}

        external_id = _normalize_str(
            data.get("external_id") or data.get("checkout_id") or data.get("id")
        )
        tx_hash = _normalize_str(data.get("tx_hash") or data.get("transaction_hash"))
        status_raw = _normalize_str(data.get("status")) or "succeeded"
        status = status_raw.lower()
        network = _normalize_str(data.get("network"))
        token = _normalize_str(data.get("token"))
        failure_reason = _normalize_str(data.get("failure_reason"))
        event_user_id = _normalize_str(data.get("user_id"))
        plan_slug = _normalize_str(data.get("plan_slug"))
        plan_id = _normalize_str(data.get("plan_id"))
        currency_hint = _normalize_str(data.get("currency"))
        meta_patch = {"webhook_event": data}
        confirmed_at = None
        if status in _SUCCESS_STATUSES or status == "completed":
            confirmed_at = datetime.now(UTC)
            status = "succeeded"
        elif status in _FAILURE_STATUSES:
            status = "failed"
        elif status in _REFUND_STATUSES:
            status = "refunded"

        transaction: dict[str, Any] | None = None
        if tx_hash:
            transaction = await self.ledger.get_by_tx_hash(tx_hash)
        if transaction is None and external_id:
            transaction = await self.ledger.get_by_external_id(external_id)

        if transaction:
            plan_id = plan_id or _normalize_str(transaction.get("product_id"))
            meta = transaction.get("meta")
            if isinstance(meta, dict):
                plan_info = meta.get("plan")
                if isinstance(plan_info, dict):
                    plan_id = plan_id or _normalize_str(plan_info.get("id"))
                    plan_slug = plan_slug or _normalize_str(plan_info.get("slug"))
            existing_status = (transaction.get("status") or "").lower()
            if (
                existing_status in {"succeeded", "failed", "refunded"}
                and existing_status == status
            ):
                logger.debug(
                    "Webhook duplicate for transaction %s",
                    transaction.get("id"),
                    extra={
                        "tx_id": transaction.get("id"),
                        "tx_hash": transaction.get("tx_hash"),
                        "external_id": external_id,
                        "status": existing_status,
                    },
                )
                return {"ok": True, "duplicate": True}
            updated = await self.ledger.update_transaction(
                transaction["id"],
                status=status,
                tx_hash=tx_hash or transaction.get("tx_hash"),
                network=network,
                token=token,
                confirmed_at=confirmed_at,
                failure_reason=failure_reason,
                meta_patch=meta_patch,
            )
            billing_metrics.observe_transaction(
                updated.get("status"),
                network=updated.get("network") or network,
                token=updated.get("token") or token,
                source="webhook_update",
                amount_cents=updated.get("gross_cents"),
            )
            user_for_tx = _normalize_str(transaction.get("user_id")) or event_user_id
            amount_cents = int(
                updated.get("gross_cents") or transaction.get("gross_cents") or 0
            )
            currency_value = (
                _normalize_str(updated.get("currency"))
                or _normalize_str(transaction.get("currency"))
                or currency_hint
                or "USD"
            )
            token_value = _normalize_str(updated.get("token")) or token
            network_value = _normalize_str(updated.get("network")) or network
            tx_hash_value = _normalize_str(updated.get("tx_hash")) or tx_hash
            failure_value = failure_reason or _normalize_str(
                updated.get("failure_reason")
            )
            gateway_value = _normalize_str(
                updated.get("gateway_slug")
            ) or _normalize_str(transaction.get("gateway_slug"))
            await self._handle_transaction_outcome(
                status=status,
                transaction=updated,
                previous=transaction,
                user_id=user_for_tx,
                plan_id=plan_id,
                plan_slug=plan_slug,
                amount_cents=amount_cents,
                currency=currency_value,
                token=token_value,
                network=network_value,
                tx_hash=tx_hash_value,
                external_id=external_id,
                failure_reason=failure_value,
                gateway=gateway_value,
            )
            return {"ok": True, "updated": True, "status": updated.get("status")}

        if not event_user_id:
            logger.warning(
                "Webhook without matching transaction or user external_id=%s tx_hash=%s",
                external_id,
                tx_hash,
                extra={
                    "tx_hash": tx_hash,
                    "external_id": external_id,
                    "webhook_status": status,
                },
            )
            return {"ok": False, "reason": "transaction_not_found"}

        gross_cents = int(data.get("amount_cents") or 0)
        if plan_slug and not plan_id:
            try:
                plan = await self.plans.get_by_slug(plan_slug)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Failed to resolve plan slug '%s' from webhook: %s",
                    plan_slug,
                    exc,
                    exc_info=exc,
                )
                plan = None
            plan_id = plan.id if plan else plan_id
        tx_payload = {
            "user_id": event_user_id,
            "gateway_slug": "evm",
            "product_type": data.get("product_type") or "subscription_plan",
            "product_id": plan_id,
            "currency": currency_hint or "USD",
            "token": token,
            "network": network,
            "gross_cents": gross_cents,
            "fee_cents": int(data.get("fee_cents") or 0),
            "net_cents": int(data.get("net_cents") or gross_cents),
            "tx_hash": tx_hash,
            "status": status,
            "created_at": datetime.now(UTC),
            "confirmed_at": confirmed_at,
            "failure_reason": failure_reason,
            "meta": {
                "checkout_external_id": external_id,
                "webhook_event": data,
            },
        }
        try:
            await self.ledger.add_tx(tx_payload)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Failed to insert webhook transaction",
                exc_info=exc,
                extra={
                    "tx_hash": tx_hash,
                    "external_id": external_id,
                    "user_id": event_user_id,
                    "status": status,
                },
            )
            return {"ok": False, "reason": "insert_failed"}
        billing_metrics.observe_transaction(
            status,
            network=network,
            token=token,
            source="webhook_insert",
            amount_cents=gross_cents,
        )
        created_record = None
        if tx_hash:
            created_record = await self.ledger.get_by_tx_hash(tx_hash)
        elif external_id:
            created_record = await self.ledger.get_by_external_id(external_id)
        base_record = created_record or {}
        amount_cents = int(base_record.get("gross_cents") or gross_cents or 0)
        currency_value = (
            _normalize_str(base_record.get("currency"))
            or _normalize_str(tx_payload.get("currency"))
            or currency_hint
            or "USD"
        )
        token_value = _normalize_str(base_record.get("token")) or token
        network_value = _normalize_str(base_record.get("network")) or network
        tx_hash_value = _normalize_str(base_record.get("tx_hash")) or tx_hash
        failure_value = failure_reason or _normalize_str(
            base_record.get("failure_reason")
        )
        gateway_value = _normalize_str(
            base_record.get("gateway_slug")
        ) or _normalize_str(tx_payload.get("gateway_slug"))
        await self._handle_transaction_outcome(
            status=status,
            transaction=created_record or dict(tx_payload),
            previous=None,
            user_id=event_user_id,
            plan_id=plan_id,
            plan_slug=plan_slug,
            amount_cents=amount_cents,
            currency=currency_value,
            token=token_value,
            network=network_value,
            tx_hash=tx_hash_value,
            external_id=external_id,
            failure_reason=failure_value,
            gateway=gateway_value,
        )
        return {"ok": True, "created": True}

    async def _handle_transaction_outcome(
        self,
        *,
        status: str,
        transaction: dict[str, Any],
        previous: dict[str, Any] | None,
        user_id: str | None,
        plan_id: str | None,
        plan_slug: str | None,
        amount_cents: int,
        currency: str | None,
        token: str | None,
        network: str | None,
        tx_hash: str | None,
        external_id: str | None,
        failure_reason: str | None,
        gateway: str | None,
    ) -> None:
        occurred_at = datetime.now(UTC)
        normalized_status = (status or "").lower() or "unknown"
        resolved_plan: Plan | None = None
        resolved_plan_id = plan_id
        resolved_plan_slug = plan_slug

        async def _fetch_plan_by_id(pid: str) -> Plan | None:
            try:
                return await self.plans.get_by_id(pid)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "billing failed to fetch plan by id %s: %s", pid, exc, exc_info=exc
                )
                return None

        async def _fetch_plan_by_slug(pslug: str) -> Plan | None:
            try:
                return await self.plans.get_by_slug(pslug)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "billing failed to fetch plan by slug %s: %s",
                    pslug,
                    exc,
                    exc_info=exc,
                )
                return None

        if plan_id:
            resolved_plan = await _fetch_plan_by_id(plan_id)
        if resolved_plan is None and plan_slug:
            resolved_plan = await _fetch_plan_by_slug(plan_slug)

        if resolved_plan is not None:
            resolved_plan_id = resolved_plan.id or resolved_plan_id
            resolved_plan_slug = resolved_plan.slug or resolved_plan_slug

        previous_subscription: Subscription | None = None
        if user_id:
            try:
                previous_subscription = await self.subs.get_active_for_user(user_id)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "billing failed to load previous subscription for user %s: %s",
                    user_id,
                    exc,
                    exc_info=exc,
                )

        subscription = previous_subscription
        plan_for_activation = resolved_plan_id
        if (
            normalized_status == "succeeded"
            and user_id
            and plan_for_activation
            and plan_for_activation.strip()
        ):
            should_activate = True
            if (
                previous_subscription is not None
                and previous_subscription.plan_id == plan_for_activation
            ):
                should_activate = False
            if should_activate:
                try:
                    subscription = await self.subs.activate(
                        user_id, plan_for_activation
                    )
                except Exception as exc:
                    logger.exception(
                        "billing subscription activation failed",
                        exc_info=exc,
                        extra={
                            "user_id": user_id,
                            "plan_id": plan_for_activation,
                            "plan_slug": resolved_plan_slug,
                            "tx_hash": tx_hash,
                        },
                    )
                    subscription = previous_subscription

        previous_plan_info: dict[str, Any] | None = None
        if previous_subscription and previous_subscription.plan_id:
            prev_plan_slug = None
            if (
                resolved_plan is not None
                and previous_subscription.plan_id == resolved_plan.id
            ):
                prev_plan_slug = resolved_plan.slug
            else:
                prev_plan = await _fetch_plan_by_id(previous_subscription.plan_id)
                if prev_plan is not None:
                    prev_plan_slug = prev_plan.slug
            previous_plan_info = {
                "plan_id": previous_subscription.plan_id,
                "slug": prev_plan_slug,
            }

        if resolved_plan_slug is None and resolved_plan is not None:
            resolved_plan_slug = resolved_plan.slug
        if resolved_plan_id is None and resolved_plan is not None:
            resolved_plan_id = resolved_plan.id

        event_plan_payload = _plan_event_payload(
            resolved_plan, plan_id=resolved_plan_id, plan_slug=resolved_plan_slug
        )
        subscription_payload = _subscription_event_payload(subscription)
        previous_subscription_payload = _subscription_event_payload(
            previous_subscription
        )
        transaction_payload = _transaction_event_payload(
            transaction=transaction,
            status=normalized_status,
            amount_cents=amount_cents,
            currency=currency,
            token=token,
            network=network,
            tx_hash=tx_hash,
            external_id=external_id,
            gateway=gateway,
        )

        if (
            self.events is not None
            and user_id
            and normalized_status == "succeeded"
            and resolved_plan_slug
        ):
            event_payload = {
                "user_id": user_id,
                "plan": event_plan_payload,
                "subscription": subscription_payload,
                "previous_subscription": previous_subscription_payload,
                "previous_plan": previous_plan_info,
                "transaction": transaction_payload,
                "occurred_at": occurred_at.isoformat(),
            }
            try:
                self.events.publish("billing.plan.changed.v1", event_payload, user_id)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "billing failed to publish plan changed event",
                    exc_info=exc,
                    extra={
                        "user_id": user_id,
                        "plan_slug": resolved_plan_slug,
                        "tx_hash": tx_hash,
                    },
                )

        meta_payload = {
            "status": normalized_status,
            "plan_id": resolved_plan_id,
            "plan_slug": resolved_plan_slug,
            "token": token,
            "network": network,
            "tx_hash": tx_hash,
            "external_id": external_id,
            "failure_reason": failure_reason,
        }

        async def _notify(
            recipient: str | None,
            title: str,
            message: str,
            *,
            topic: str,
        ) -> None:
            if recipient is None or self.notify_service is None:
                return
            command = NotificationCreateCommand(
                user_id=recipient,
                title=title,
                message=message,
                type_="billing",
                topic_key=topic,
                meta=meta_payload,
            )
            try:
                await self.notify_service.create_notification(command)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "billing notification dispatch failed",
                    exc_info=exc,
                    extra={"user_id": recipient, "topic": topic},
                )

        amount_label = _format_amount(amount_cents, currency)
        plan_label = resolved_plan_slug or (
            resolved_plan.title if resolved_plan else None
        )

        if normalized_status == "succeeded":
            user_title = "Подписка активирована"
            plan_descr = plan_label or "план"
            user_message = (
                f"Платёж {amount_label} подтверждён. Активирован {plan_descr}."
            )
            await _notify(
                user_id,
                user_title,
                user_message,
                topic="billing.payment.succeeded",
            )
            if self.finance_ops_recipient:
                ops_message = (
                    f"Успешный платёж {amount_label}"
                    f" пользователя {user_id} ({plan_descr}, сеть {network or 'n/a'})."
                )
                await _notify(
                    self.finance_ops_recipient,
                    "Платёж подтверждён",
                    ops_message,
                    topic="billing.ops.payment",
                )
        elif normalized_status == "failed":
            reason = f" Причина: {failure_reason}." if failure_reason else ""
            user_message = (
                f"Платёж {amount_label} не прошёл.{reason} "
                "Проверьте баланс кошелька или повторите попытку."
            )
            await _notify(
                user_id,
                "Платёж не прошёл",
                user_message,
                topic="billing.payment.failed",
            )
        elif normalized_status == "refunded":
            user_message = (
                f"Платёж {amount_label} был возвращён. Средства вернутся на кошелёк."
            )
            await _notify(
                user_id,
                "Платёж возвращён",
                user_message,
                topic="billing.payment.refunded",
            )

        await safe_audit_log(
            self.audit_service,
            AuditLogPayload(
                actor_id=user_id,
                action=f"billing.transaction.{normalized_status}",
                resource_type="billing/transaction",
                resource_id=str(transaction.get("id")),
                before=_normalize_for_audit(previous),
                after=_normalize_for_audit(transaction),
                extra={
                    **meta_payload,
                    "amount_cents": amount_cents,
                    "gateway": gateway,
                },
            ),
            logger=logger,
            error_slug="billing_audit_failed",
            log_extra={
                "transaction_id": transaction.get("id"),
                "status": normalized_status,
                "user_id": user_id,
            },
        )

        logger.info(
            "billing transaction outcome processed",
            extra={
                "transaction_id": transaction.get("id"),
                "user_id": user_id,
                "status": normalized_status,
                "plan_id": resolved_plan_id,
                "plan_slug": resolved_plan_slug,
                "tx_hash": tx_hash,
                "network": network,
                "token": token,
            },
        )

    async def reconcile_pending_transactions(
        self, *, older_than_seconds: int = 120, limit: int = 100
    ) -> dict[str, Any]:
        pending = await self.ledger.list_pending(
            older_than_seconds=older_than_seconds, limit=limit
        )
        for tx in pending:
            meta = tx.get("meta") or {}
            meta.setdefault("retries", 0)
            meta["retries"] = int(meta["retries"]) + 1
            try:
                await self.ledger.update_transaction(
                    tx["id"],
                    status=tx.get("status") or "pending",
                    tx_hash=tx.get("tx_hash"),
                    network=tx.get("network"),
                    token=tx.get("token"),
                    confirmed_at=tx.get("confirmed_at"),
                    failure_reason=tx.get("failure_reason"),
                    meta_patch={"retries": meta["retries"]},
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(
                    "billing reconcile update failed",
                    exc_info=exc,
                    extra={
                        "tx_id": tx.get("id"),
                        "tx_hash": tx.get("tx_hash"),
                        "user_id": tx.get("user_id"),
                        "status": tx.get("status"),
                    },
                )
        return {"count": len(pending)}

    async def get_subscription_for_user(self, user_id: str) -> dict[str, Any] | None:
        sub = await self.subs.get_active_for_user(user_id)
        return None if not sub else sub.__dict__

    async def get_summary_for_user(self, user_id: str) -> dict[str, Any]:
        summary = await self.summary_repo.get_summary(user_id)
        history = await self.history_repo.get_history(user_id, limit=20)
        last_payment = _select_last_payment(history.items)
        debt = _calculate_debt(history.items, summary.plan)
        return {
            "plan": summary.plan,
            "subscription": summary.subscription,
            "payment": {
                "mode": "evm_wallet",
                "title": "EVM wallet",
                "message": "Currently we only support EVM (SIWE) wallets. Card payments are coming soon.",
                "coming_soon": True,
            },
            "debt": debt,
            "last_payment": last_payment,
        }

    async def get_history_for_user(
        self, user_id: str, limit: int = 20
    ) -> dict[str, Any]:
        safe_limit = int(max(1, min(limit, 100)))
        history = await self.history_repo.get_history(user_id, limit=safe_limit)
        return {"items": history.items, "coming_soon": history.coming_soon}


__all__ = ["BillingService"]


def _select_last_payment(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in items:
        normalized = _normalize_payment(item)
        if normalized:
            return normalized
    return None


def _calculate_debt(
    items: list[dict[str, Any]], plan: dict[str, Any] | None
) -> dict[str, Any]:
    outstanding_cents = 0
    currency = None
    affected_count = 0
    last_issue: dict[str, Any] | None = None
    trouble_statuses = {"pending", "processing", "failed", "declined", "error"}

    for item in items:
        status = str(item.get("status") or "").lower()
        if status not in trouble_statuses:
            continue
        cents = _coerce_cents(item.get("amount_cents"))
        if cents is None:
            continue
        outstanding_cents += cents
        affected_count += 1
        currency = currency or item.get("currency")
        if last_issue is None or _is_newer(item, last_issue):
            last_issue = item

    currency = currency or _resolve_currency(plan) or "USD"
    amount = outstanding_cents / 100.0 if outstanding_cents else None
    return {
        "amount_cents": outstanding_cents,
        "amount": amount,
        "currency": currency,
        "is_overdue": outstanding_cents > 0,
        "transactions": affected_count,
        "last_issue": _normalize_payment(last_issue),
    }


def _normalize_payment(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    amount_cents = _coerce_cents(item.get("amount_cents"))
    amount_raw = item.get("amount")
    amount: float | None
    if isinstance(amount_raw, (int, float)):
        amount = float(amount_raw)
    elif isinstance(amount_raw, str):
        text = amount_raw.strip()
        try:
            amount = float(text) if text else None
        except ValueError:
            amount = None
    elif amount_cents is not None:
        amount = amount_cents / 100.0
    else:
        amount = None

    gas = item.get("gas")
    normalized_gas = _normalize_for_audit(gas) if isinstance(gas, dict) else None

    payload = {
        "id": _normalize_str(item.get("id")),
        "status": _normalize_str(item.get("status")),
        "created_at": _normalize_datetime_value(item.get("created_at")),
        "confirmed_at": _normalize_datetime_value(item.get("confirmed_at")),
        "amount": amount,
        "amount_cents": amount_cents,
        "currency": _normalize_str(item.get("currency")),
        "token": _normalize_str(item.get("token")),
        "network": _normalize_str(item.get("network")),
        "tx_hash": _normalize_str(item.get("tx_hash")),
        "provider": _normalize_str(item.get("provider")),
        "product_type": _normalize_str(item.get("product_type")),
        "product_id": _normalize_str(item.get("product_id")),
        "failure_reason": _normalize_str(item.get("failure_reason")),
        "gas": normalized_gas,
    }
    gateway = _normalize_str(item.get("gateway") or item.get("gateway_slug"))
    if gateway is not None:
        payload["gateway"] = gateway
    external_id = _normalize_str(
        item.get("external_id") or _extract_checkout_external_id(item)
    )
    if external_id is not None:
        payload["external_id"] = external_id
    return payload


def _normalize_datetime_value(value: Any) -> str | None:
    iso = _datetime_to_iso(value)
    if iso is not None:
        return iso
    return _normalize_str(value)


def _coerce_cents(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None
    return None


def _is_newer(candidate: dict[str, Any], current: dict[str, Any]) -> bool:
    candidate_ts = _extract_timestamp(candidate)
    current_ts = _extract_timestamp(current)
    if candidate_ts and current_ts:
        return candidate_ts > current_ts
    if candidate_ts and current_ts is None:
        return True
    return False


def _extract_timestamp(payload: dict[str, Any]) -> datetime | None:
    for key in ("confirmed_at", "created_at"):
        value = payload.get(key)
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            try:
                return datetime.fromisoformat(text)
            except ValueError:
                continue
    return None


def _resolve_currency(plan: dict[str, Any] | None) -> str | None:
    if not isinstance(plan, dict):
        return None
    for key in ("currency", "price_currency", "price_token"):
        value = _normalize_str(plan.get(key))
        if value:
            return value
    return None


def _plan_event_payload(
    plan: Plan | None, *, plan_id: str | None, plan_slug: str | None
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if plan and plan.id:
        payload["id"] = plan.id
    elif plan_id:
        payload["id"] = plan_id
    if plan and plan.slug:
        payload["slug"] = plan.slug
    elif plan_slug:
        payload["slug"] = plan_slug
    if plan:
        payload.update(
            {
                "title": plan.title,
                "price_cents": plan.price_cents,
                "currency": plan.currency,
                "price_token": plan.price_token,
                "price_usd_estimate": plan.price_usd_estimate,
                "billing_interval": plan.billing_interval,
                "features": plan.features,
                "monthly_limits": plan.monthly_limits,
            }
        )
    return payload


def _subscription_event_payload(
    subscription: Subscription | None,
) -> dict[str, Any] | None:
    if subscription is None:
        return None
    return {
        "id": subscription.id,
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "auto_renew": subscription.auto_renew,
        "started_at": _datetime_to_iso(subscription.started_at),
        "ends_at": _datetime_to_iso(subscription.ends_at),
    }


def _transaction_event_payload(
    *,
    transaction: dict[str, Any] | None,
    status: str,
    amount_cents: int,
    currency: str | None,
    token: str | None,
    network: str | None,
    tx_hash: str | None,
    external_id: str | None,
    gateway: str | None,
) -> dict[str, Any]:
    base = transaction or {}
    return {
        "id": base.get("id"),
        "status": status,
        "tx_hash": tx_hash or base.get("tx_hash"),
        "network": network or base.get("network"),
        "token": token or base.get("token"),
        "amount_cents": int(base.get("gross_cents") or amount_cents or 0),
        "currency": currency or base.get("currency") or "USD",
        "gateway": gateway or base.get("gateway_slug"),
        "external_id": external_id or _extract_checkout_external_id(base),
        "confirmed_at": _datetime_to_iso(base.get("confirmed_at")),
        "created_at": _datetime_to_iso(base.get("created_at")),
    }


def _extract_checkout_external_id(transaction: dict[str, Any] | None) -> str | None:
    if not isinstance(transaction, dict):
        return None
    meta = transaction.get("meta")
    if isinstance(meta, dict):
        checkout_id = meta.get("checkout_external_id")
        if checkout_id:
            return str(checkout_id)
        provider_meta = meta.get("provider_meta")
        if isinstance(provider_meta, dict):
            external = provider_meta.get("external_id")
            if external:
                return str(external)
    return None


def _normalize_for_audit(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    def _convert(value: Any) -> Any:
        if isinstance(value, datetime):
            return _datetime_to_iso(value)
        if isinstance(value, dict):
            return {k: _convert(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_convert(v) for v in value]
        return value

    return {key: _convert(val) for key, val in payload.items()}


def _datetime_to_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()
    return None


def _format_amount(amount_cents: int | None, currency: str | None) -> str:
    cents = amount_cents or 0
    amount = cents / 100.0
    code = currency or "USD"
    return f"{amount:.2f} {code}"


def _normalize_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    try:
        return str(value)
    except (TypeError, ValueError):
        return None
