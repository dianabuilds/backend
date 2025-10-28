"""End-to-end smoke script for the billing EVM flow.

The script performs the following steps against the configured database:
1. Provision demo gateway/contract/plan records (idempotent upsert).
2. Execute checkout for a demo user and capture the generated payload.
3. Simulate an on-chain webhook with the configured secret.
4. Inspect ledger, emitted events, notifications and audit entries.

Usage:
    python apps/backend/scripts/billing_e2e.py --database-url postgresql://...

The script uses the same environment loading logic as the backend. You may
override specific values via CLI flags. Run inside a virtualenv with project
dependencies installed.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import sys
import uuid
from dataclasses import asdict
from typing import Any

from apps.backend.domains.platform.billing.wires import build_container
from domains.platform.billing.domain.models import Plan


class EventRecorder:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def publish(
        self, topic: str, payload: dict[str, Any], key: str | None = None
    ) -> None:
        self.records.append({"topic": topic, "payload": payload, "key": key})


class NotificationRecorder:
    def __init__(self) -> None:
        self.commands: list[Any] = []

    async def create_notification(self, command: Any) -> dict[str, Any]:
        self.commands.append(command)
        return {"ok": True, "id": f"notif-{len(self.commands)}"}


class AuditRecorder:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def log(self, **kwargs: Any) -> dict[str, Any]:
        self.entries.append(kwargs)
        return {"ok": True}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Billing EVM end-to-end flow")
    parser.add_argument(
        "--user-id", default=str(uuid.uuid4()), help="User ID to run the flow for"
    )
    parser.add_argument(
        "--plan-slug", default="demo-evm-plan", help="Slug for the demo plan"
    )
    parser.add_argument(
        "--plan-title", default="Demo EVM Plan", help="Title for the demo plan"
    )
    parser.add_argument(
        "--price-cents", type=int, default=5000, help="Plan price in cents"
    )
    parser.add_argument("--currency", default="USD", help="Fiat currency code")
    parser.add_argument("--token", default="USDC", help="Token symbol for the plan")
    parser.add_argument("--network", default="polygon", help="EVM network identifier")
    parser.add_argument(
        "--contract-slug",
        default="demo-evm-contract",
        help="Slug for the payment contract",
    )
    parser.add_argument(
        "--contract-address",
        default="0xDeMo000000000000000000000000000000000000",
        help="EVM contract address",
    )
    parser.add_argument("--chain-id", default="137", help="Chain ID for the contract")
    parser.add_argument(
        "--gateway-slug",
        default="evm-default",
        help="Gateway slug to bind with the plan",
    )
    parser.add_argument(
        "--webhook-secret",
        default="demo-secret",
        help="Webhook secret shared with relay/contract",
    )
    parser.add_argument(
        "--rpc-url", default="https://rpc-polygon.ankr.com", help="Primary RPC endpoint"
    )
    parser.add_argument(
        "--fallback-rpc", default="", help="Fallback RPC endpoint (optional)"
    )
    parser.add_argument(
        "--amount-wei",
        type=int,
        default=0,
        help="Override transfer amount in wei (optional)",
    )
    parser.add_argument(
        "--tx-hash", default="", help="Force tx hash (otherwise generated)"
    )
    parser.add_argument(
        "--finance-ops-id",
        default="finance-demo",
        help="User ID for finance ops notifications",
    )
    parser.add_argument(
        "--idempotency-key", default=str(uuid.uuid4()), help="Checkout idempotency key"
    )
    return parser


async def _ensure_crypto_config(
    container: Any, network: str, rpc_url: str, fallback_rpc: str
) -> None:
    config = {
        "rpc_endpoints": {network: rpc_url},
        "fallback_networks": {network: fallback_rpc} if fallback_rpc else {},
        "retries": 3,
        "gas_price_cap": None,
    }
    await container.crypto_config_store.set("default", config)


async def _ensure_contract(container: Any, args: argparse.Namespace) -> dict[str, Any]:
    contract_payload = {
        "slug": args.contract_slug,
        "title": f"{args.contract_slug} (demo)",
        "chain": args.network,
        "chain_id": args.chain_id,
        "address": args.contract_address,
        "type": "evm",
        "enabled": True,
        "status": "active",
        "testnet": args.network.endswith("testnet"),
        "methods": {"mint": {"name": "mint"}},
        "mint_method": "mint",
        "burn_method": "burn",
        "abi": None,
        "webhook_url": None,
        "webhook_secret": args.webhook_secret,
        "fallback_rpc": (
            {"primary": args.rpc_url, "secondary": args.fallback_rpc}
            if args.fallback_rpc
            else None
        ),
    }
    return await container.contracts.upsert(contract_payload)


async def _ensure_gateway(container: Any, args: argparse.Namespace) -> dict[str, Any]:
    gateway_payload = {
        "slug": args.gateway_slug,
        "type": "evm",
        "enabled": True,
        "priority": 10,
        "config": {"contract_slug": args.contract_slug},
    }
    return await container.gateways.upsert(gateway_payload)


async def _ensure_plan(container: Any, args: argparse.Namespace) -> Plan:
    features = {
        "evm": {
            "network": args.network,
            "token": args.token,
            "amount_wei": args.amount_wei or args.price_cents * 10**16,
        }
    }
    plan_payload = {
        "slug": args.plan_slug,
        "title": args.plan_title,
        "description": "Demo EVM plan created by billing_e2e.py",
        "price_cents": args.price_cents,
        "price_token": args.token,
        "currency": args.currency,
        "billing_interval": "month",
        "gateway_slug": args.gateway_slug,
        "contract_slug": args.contract_slug,
        "monthly_limits": {"requests": 1000},
        "features": features,
        "is_active": True,
    }
    return await container.plans.upsert(plan_payload)


def _make_webhook_payload(
    *,
    external_id: str,
    tx_hash: str,
    user_id: str,
    plan: Plan,
    status: str,
    network: str | None,
    token: str | None,
) -> dict[str, Any]:
    return {
        "external_id": external_id,
        "tx_hash": tx_hash,
        "status": status,
        "user_id": user_id,
        "plan_slug": plan.slug,
        "plan_id": plan.id,
        "amount_cents": plan.price_cents,
        "currency": plan.currency or "USD",
        "network": network,
        "token": token,
    }


def _sign_payload(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


async def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    container = build_container()
    service = container.service

    event_recorder = EventRecorder()
    notification_recorder = NotificationRecorder()
    audit_recorder = AuditRecorder()

    service.events = event_recorder
    service.notify_service = notification_recorder
    service.audit_service = audit_recorder
    service.finance_ops_recipient = args.finance_ops_id

    await _ensure_crypto_config(
        container, args.network, args.rpc_url, args.fallback_rpc
    )
    contract = await _ensure_contract(container, args)
    await _ensure_gateway(container, args)
    plan = await _ensure_plan(container, args)

    user_id = args.user_id
    idempotency_key = args.idempotency_key

    checkout = await service.checkout(
        user_id, plan.slug, idempotency_key=idempotency_key
    )
    print("Checkout payload:")
    print(
        json.dumps(
            {
                "external_id": checkout.external_id,
                "provider": checkout.provider,
                "expires_at": checkout.expires_at,
                "payload": checkout.payload,
                "meta": checkout.meta,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    tx_hash = args.tx_hash or f"0x{uuid.uuid4().hex}"
    webhook_payload = _make_webhook_payload(
        external_id=checkout.external_id,
        tx_hash=tx_hash,
        user_id=user_id,
        plan=plan,
        status="succeeded",
        network=(checkout.meta or {}).get("network"),
        token=(checkout.meta or {}).get("token"),
    )
    payload_bytes = json.dumps(webhook_payload).encode("utf-8")
    signature = _sign_payload(payload_bytes, args.webhook_secret)
    webhook_result = await service.handle_webhook(payload_bytes, signature)

    print("\nWebhook result:")
    print(json.dumps(webhook_result, indent=2, ensure_ascii=False))

    ledger_record = await service.ledger.get_by_tx_hash(tx_hash)
    summary = await service.get_summary_for_user(user_id)

    print("\nLedger transaction:")
    print(json.dumps(ledger_record or {}, indent=2, default=str, ensure_ascii=False))

    print("\nPlan change events:")
    for item in event_recorder.records:
        print(json.dumps(item, indent=2, ensure_ascii=False))

    print("\nNotifications:")
    for cmd in notification_recorder.commands:
        try:
            payload = asdict(cmd)
        except TypeError:
            payload = cmd
        print(json.dumps(payload, indent=2, default=str, ensure_ascii=False))

    print("\nAudit entries:")
    for entry in audit_recorder.entries:
        print(json.dumps(entry, indent=2, default=str, ensure_ascii=False))

    print("\nUser summary:")
    print(json.dumps(summary, indent=2, default=str, ensure_ascii=False))

    print(
        "\nContract in use:",
        json.dumps(contract, indent=2, default=str, ensure_ascii=False),
    )
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        exit_code = 130
    sys.exit(exit_code)
