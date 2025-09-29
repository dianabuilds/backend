from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/billing", tags=["billing"])

    @router.get("/plans")
    async def list_plans(req: Request) -> dict[str, Any]:
        c = get_container(req)
        plans = await c.billing.service.list_plans()
        return {"items": [p.__dict__ for p in plans]}

    @router.post(
        "/checkout",
        dependencies=([Depends(RateLimiter(times=5, seconds=60))] if RateLimiter else []),
    )
    async def checkout(
        req: Request,
        body: dict[str, Any],
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        plan_slug = str(body.get("plan"))
        if not plan_slug:
            raise HTTPException(status_code=400, detail="plan_required")
        res = await c.billing.service.checkout(user_id, plan_slug)
        return {"ok": True, "checkout": res.__dict__}

    @router.post("/webhook")
    async def webhook(
        req: Request, x_signature: str | None = Header(default=None)
    ) -> dict[str, Any]:
        c = get_container(req)
        payload = await req.body()
        return await c.billing.service.handle_webhook(payload, x_signature)

    @router.get("/subscriptions/me")
    async def my_subscription(req: Request, claims=Depends(get_current_user)) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        sub = await c.billing.service.get_subscription_for_user(user_id)
        return {"subscription": sub}

    @router.get("/summary")
    async def billing_summary(
        req: Request,
        user_id: str = Query(..., description="User ID"),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        summary = await c.billing.service.get_summary_for_user(user_id)
        return summary

    @router.get("/history")
    async def billing_history(
        req: Request,
        user_id: str = Query(..., description="User ID"),
        limit: int = Query(20, ge=1, le=100),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        history = await c.billing.service.get_history_for_user(user_id, limit=limit)
        return history

    @router.get("/me/summary")
    async def my_billing_summary(
        req: Request,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated")
        c = get_container(req)
        return await c.billing.service.get_summary_for_user(user_id)

    @router.get("/me/history")
    async def my_billing_history(
        req: Request,
        claims=Depends(get_current_user),
        limit: int = Query(20, ge=1, le=100),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated")
        c = get_container(req)
        return await c.billing.service.get_history_for_user(user_id, limit=limit)

    # Admin
    @router.post("/admin/plans")
    async def admin_upsert_plan(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        # capture 'before' for audit
        before = None
        try:
            if body.get("slug"):
                before_obj = await c.billing.plans.get_by_slug(str(body.get("slug")))
                before = before_obj.__dict__ if before_obj else None
        except Exception:
            before = None
        plan = await c.billing.plans.upsert(body)
        # audit log
        try:
            await c.audit.service.log(
                actor_id=getattr(req.state, "auth_context", {}).get("actor_id"),
                action="plan.upsert",
                resource_type="plan",
                resource_id=plan.slug,
                before=before,
                after=plan.__dict__,
                extra={"route": "/v1/billing/admin/plans"},
            )
        except Exception:
            pass
        return {"plan": plan.__dict__}

    @router.delete("/admin/plans/{plan_id}")
    async def admin_delete_plan(
        req: Request,
        plan_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.billing.plans.delete(plan_id)
        return {"ok": True}

    @router.get("/admin/plans/all")
    async def admin_list_all_plans(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        plans = await c.billing.plans.list_all()
        return {"items": [p.__dict__ for p in plans]}

    @router.post("/admin/plans/bulk_limits")
    async def admin_bulk_limits(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        items = body.get("items") or []
        updated: list[dict[str, Any]] = []
        for it in items:
            slug = str(it.get("slug") or "").strip()
            if not slug:
                continue
            existing = await c.billing.plans.get_by_slug(slug)
            base = existing.__dict__ if existing else {}
            payload = {
                "id": base.get("id"),
                "slug": slug,
                "title": base.get("title") or slug,
                "price_cents": base.get("price_cents"),
                "currency": base.get("currency"),
                "is_active": base.get("is_active", True),
                "order": base.get("order", 100),
                "monthly_limits": it.get("monthly_limits") or base.get("monthly_limits"),
                "features": base.get("features"),
            }
            plan = await c.billing.plans.upsert(payload)
            updated.append(plan.__dict__)
        return {"items": updated}

    @router.get("/admin/plans/{slug}/audit")
    async def admin_plan_audit(
        req: Request, slug: str, limit: int = 100, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.audit.repo.list(limit=int(limit))
        filtered = [
            it
            for it in items
            if (it or {}).get("resource_type") == "plan" and (it or {}).get("resource_id") in {slug}
        ]
        return {"items": filtered}

    @router.get("/admin/providers")
    async def admin_list_providers(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.billing.gateways.list()
        return {"items": items}

    @router.post("/admin/providers")
    async def admin_upsert_provider(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        payload = {
            "slug": body.get("slug"),
            "type": body.get("type", "custom"),
            "enabled": body.get("enabled", True),
            "priority": body.get("priority", 100),
            "config": body.get("config") or {},
        }
        # Link provider to contract via config field `linked_contract`
        lc = body.get("contract_slug") or body.get("linked_contract")
        if lc:
            try:
                cfg = dict(payload["config"]) if payload["config"] else {}
            except Exception:
                cfg = {}
            cfg["linked_contract"] = str(lc)
            payload["config"] = cfg
        item = await c.billing.gateways.upsert(payload)
        return {"provider": item}

    @router.delete("/admin/providers/{slug}")
    async def admin_delete_provider(
        req: Request,
        slug: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.billing.gateways.delete(slug)
        return {"ok": True}

    @router.get("/admin/transactions")
    async def admin_list_transactions(
        req: Request,
        limit: int = 100,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.billing.ledger.list_recent(limit=int(limit))
        return {"items": items}

    # Contracts admin
    @router.get("/admin/contracts")
    async def admin_list_contracts(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.billing.contracts.list()
        return {"items": items}

    @router.post("/admin/contracts")
    async def admin_upsert_contract(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        payload = {
            "id": body.get("id"),
            "slug": body.get("slug") or body.get("address") or body.get("title"),
            "title": body.get("title"),
            "chain": body.get("chain"),
            "address": body.get("address"),
            "type": body.get("type"),
            "enabled": body.get("enabled", True),
            "status": body.get("status", "active"),
            "testnet": body.get("testnet", False),
            "methods": body.get("methods"),
            "abi": body.get("abi"),
            "abi_present": bool(body.get("abi") is not None),
            "webhook_url": body.get("webhook_url"),
        }
        item = await c.billing.contracts.upsert(payload)
        return {"contract": item}

    @router.delete("/admin/contracts/{id_or_slug}")
    async def admin_delete_contract(
        req: Request,
        id_or_slug: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.billing.contracts.delete(id_or_slug)
        return {"ok": True}

    @router.get("/admin/contracts/{id_or_slug}/events")
    async def admin_contract_events(
        req: Request, id_or_slug: str, limit: int = 100, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.billing.contracts.list_events(id_or_slug, limit=int(limit))
        return {"items": items}

    @router.post("/admin/contracts/{id_or_slug}/events")
    async def admin_add_contract_event(
        req: Request,
        id_or_slug: str,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        ct = await c.billing.contracts.get(id_or_slug)
        if not ct:
            raise HTTPException(status_code=404, detail="contract_not_found")
        payload = {
            "contract_id": ct["id"],
            "event": body.get("event") or "event",
            "method": body.get("method"),
            "tx_hash": body.get("tx_hash"),
            "status": body.get("status"),
            "amount": body.get("amount"),
            "token": body.get("token"),
            "meta": body.get("meta") or {},
        }
        await c.billing.contracts.add_event(payload)
        return {"ok": True}

    @router.get("/admin/contracts/events")
    async def admin_all_contract_events(
        req: Request, limit: int = 100, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.billing.contracts.list_events(None, limit=int(limit))
        return {"items": items}

    @router.get("/admin/contracts/metrics")
    async def admin_contract_metrics(
        req: Request,
        id_or_slug: str | None = None,
        window: int = 1000,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        methods = await c.billing.contracts.metrics_methods(id_or_slug, window=int(window))
        return {"methods": methods}

    # KPIs
    @router.get("/admin/kpi")
    async def admin_kpi(req: Request, _admin: None = Depends(require_admin)) -> dict[str, Any]:
        c = get_container(req)
        # Basic KPIs from ledger (best-effort on schema)
        try:
            from sqlalchemy import text  # type: ignore

            dsn = c.billing.plans._engine  # reuse engine via repo when possible
            engine = dsn
            async with engine.begin() as conn:
                s_ok = await conn.execute(
                    text(
                        "SELECT count(*) AS n FROM payment_transactions WHERE status in ('captured','succeeded','success')"
                    )
                )
                s_err = await conn.execute(
                    text(
                        "SELECT count(*) AS n FROM payment_transactions WHERE status in ('failed','error','declined')"
                    )
                )
                s_vol = await conn.execute(
                    text(
                        "SELECT coalesce(sum(gross_cents),0) AS v FROM payment_transactions WHERE status in ('captured','succeeded','success')"
                    )
                )
                ok = int((s_ok.mappings().first() or {}).get("n", 0))
                err = int((s_err.mappings().first() or {}).get("n", 0))
                vol = int((s_vol.mappings().first() or {}).get("v", 0))
        except Exception:
            ok = err = vol = 0
        # Avg confirmation time (requires meta.confirmed_at; best effort)
        avg_confirm_ms = 0.0
        try:
            from sqlalchemy import text  # type: ignore

            engine = c.billing.plans._engine
            sql = text(
                """
                SELECT avg(extract(epoch from (to_timestamp((meta->>'confirmed_at')::double precision) - created_at))*1000.0) AS ms
                FROM payment_transactions
                WHERE (meta ? 'confirmed_at')
            """
            )
            async with engine.begin() as conn:
                r = (await conn.execute(sql)).mappings().first()
                if r and r.get("ms") is not None:
                    avg_confirm_ms = float(r.get("ms") or 0.0)
        except Exception:
            avg_confirm_ms = 0.0
        return {
            "success": ok,
            "errors": err,
            "volume_cents": vol,
            "avg_confirm_ms": avg_confirm_ms,
        }

    @router.get("/admin/metrics")
    async def admin_metrics(req: Request, _admin: None = Depends(require_admin)) -> dict[str, Any]:
        c = get_container(req)
        active_subs = 0
        mrr = 0.0
        arpu = 0.0
        churn_30d = 0.0
        try:
            from sqlalchemy import text  # type: ignore

            engine = c.billing.plans._engine
            async with engine.begin() as conn:
                # Active subs
                r = (
                    (
                        await conn.execute(
                            text("SELECT count(*) n FROM user_subscriptions WHERE status='active'")
                        )
                    )
                    .mappings()
                    .first()
                )
                active_subs = int((r or {}).get("n", 0))
                # MRR: sum of active subs plan price normalized to month (assume features.interval in subscription_plans.features)
                sql = text(
                    """
                    SELECT coalesce(sum(CASE WHEN (sp.features->>'interval') = 'year' THEN (sp.price_cents/12.0) ELSE sp.price_cents END),0) AS cents
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON sp.id = us.plan_id
                    WHERE us.status='active'
                    """
                )
                r2 = (await conn.execute(sql)).mappings().first()
                mrr_cents = float((r2 or {}).get("cents", 0.0))
                mrr = mrr_cents / 100.0
                arpu = mrr / max(active_subs, 1)
                # churn 30d: ended subs in last 30d over active subs + ended
                sql_ch = text(
                    "SELECT count(*) n FROM user_subscriptions WHERE status!='active' AND updated_at >= now() - interval '30 days'"
                )
                r3 = (await conn.execute(sql_ch)).mappings().first()
                ended = int((r3 or {}).get("n", 0))
                churn_30d = ended / max(active_subs + ended, 1)
        except Exception:
            pass
        return {"active_subs": active_subs, "mrr": mrr, "arpu": arpu, "churn_30d": churn_30d}

    @router.get("/admin/revenue_ts")
    async def admin_revenue_ts(
        req: Request, days: int = 30, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        rows: list[dict[str, Any]] = []
        try:
            from sqlalchemy import text  # type: ignore

            engine = c.billing.plans._engine
            sql = text(
                """
                SELECT date_trunc('day', created_at) AS day, sum(gross_cents) AS cents
                FROM payment_transactions
                WHERE status in ('captured','succeeded','success')
                  AND created_at >= now() - (:days::text || ' days')::interval
                GROUP BY day
                ORDER BY day
                """
            )
            async with engine.begin() as conn:
                res = await conn.execute(sql, {"days": int(max(1, min(days, 365)))})
                rows = [
                    {"day": r[0].isoformat(), "amount": float(r[1] or 0.0) / 100.0} for r in res
                ]
        except Exception:
            rows = []
        return {"series": rows}

    # Crypto config (in-memory; persist later if needed)
    @router.get("/admin/crypto-config")
    async def get_crypto_config(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        row = await c.billing.crypto_config_store.get("default")
        return {"config": (row or {}).get("config") or {}}

    @router.post("/admin/crypto-config")
    async def set_crypto_config(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        base_row = await c.billing.crypto_config_store.get("default")
        base = dict((base_row or {}).get("config") or {})
        base.update(
            {
                "rpc_endpoints": body.get("rpc_endpoints") or base.get("rpc_endpoints") or {},
                "retries": (
                    body.get("retries") if body.get("retries") is not None else base.get("retries")
                ),
                "gas_price_cap": (
                    body.get("gas_price_cap")
                    if body.get("gas_price_cap") is not None
                    else base.get("gas_price_cap")
                ),
                "fallback_networks": body.get("fallback_networks")
                or base.get("fallback_networks")
                or {},
            }
        )
        row = await c.billing.crypto_config_store.set("default", base)
        return {"config": row.get("config") or {}}

    # Public (signed) webhook for contract events ingestion
    @router.post("/contracts/webhook")
    async def contracts_webhook(req: Request) -> dict[str, Any]:
        raw = await req.body()
        sig = req.headers.get("X-Signature") or req.headers.get("x-signature")
        if not sig:
            raise HTTPException(status_code=401, detail="missing_signature")
        # Verify HMAC SHA256 signature using secret from settings
        import hashlib
        import hmac

        s = get_container(req).settings
        secret = getattr(s, "billing_webhook_secret", None)
        if not secret:
            raise HTTPException(status_code=503, detail="webhook_secret_not_configured")
        calc = hmac.new(str(secret).encode("utf-8"), raw, hashlib.sha256).hexdigest()
        if calc.lower() != str(sig).lower():
            raise HTTPException(status_code=403, detail="invalid_signature")
        # Accept JSON payload
        try:
            payload = await req.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail="invalid_json") from e
        c = get_container(req)
        # Resolve contract: by slug or address
        ct = None
        id_or_slug = str(payload.get("contract")) if payload.get("contract") else None
        address = str(payload.get("address")) if payload.get("address") else None
        if id_or_slug:
            ct = await c.billing.contracts.get(id_or_slug)
        if not ct and address:
            ct = await c.billing.contracts.get_by_address(address)
        if not ct:
            raise HTTPException(status_code=404, detail="contract_not_found")
        evt = {
            "contract_id": ct["id"],
            "event": payload.get("event") or "PaymentReceived",
            "method": payload.get("method"),
            "tx_hash": payload.get("tx_hash"),
            "status": payload.get("status"),
            "amount": payload.get("amount"),
            "token": payload.get("token"),
            "meta": payload.get("meta") or {},
        }
        await c.billing.contracts.add_event(evt)
        return {"ok": True}

    @router.get("/admin/contracts/metrics_ts")
    async def admin_contract_metrics_ts(
        req: Request,
        id_or_slug: str | None = None,
        days: int = 30,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        methods = await c.billing.contracts.metrics_methods_ts(id_or_slug, days=int(days))
        volume = await c.billing.contracts.metrics_volume_ts(id_or_slug, days=int(days))
        return {"methods": methods, "volume": volume}

    return router
