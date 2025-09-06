import importlib
import os
import sys
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

os.environ.setdefault("TESTING", "True")
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.core.preview import PreviewContext  # noqa: E402
from app.domains.quota.application.quota_service import QuotaService  # noqa: E402
from app.providers.cache import cache as shared_cache  # noqa: E402


async def _clear():
    keys = await shared_cache.scan("q:*")
    if keys:
        await shared_cache.delete(*keys)


@pytest.mark.asyncio
async def test_quota_service_updates_counters():
    await _clear()
    qs = QuotaService()
    now = datetime(2024, 1, 1, tzinfo=UTC)
    preview = PreviewContext(now=now)

    res1 = await qs.consume(
        user_id="u1",
        account_id="w1",
        key="ai_tokens",
        limit=5,
        preview=preview,
    )
    assert res1["remaining"] == 4

    res2 = await qs.consume(
        user_id="u1",
        account_id="w1",
        key="ai_tokens",
        limit=5,
        amount=2,
        preview=preview,
    )
    assert res2["remaining"] == 2

    period = now.strftime("%Y%m%d")
    value = await shared_cache.get(f"q:ai_tokens:{period}:u1:w1")
    assert int(value) == 3

    with pytest.raises(HTTPException):
        await qs.consume(
            user_id="u1",
            account_id="w1",
            key="ai_tokens",
            limit=5,
            amount=3,
            preview=preview,
        )


@pytest.mark.asyncio
async def test_quota_service_resets_periods():
    await _clear()
    qs = QuotaService()
    day1 = PreviewContext(now=datetime(2024, 1, 1, tzinfo=UTC))
    day2 = PreviewContext(now=datetime(2024, 1, 2, tzinfo=UTC))

    await qs.consume(
        user_id="u1",
        account_id="w1",
        key="notif_per_day",
        limit=5,
        preview=day1,
    )
    res_day2 = await qs.consume(
        user_id="u1",
        account_id="w1",
        key="notif_per_day",
        limit=5,
        preview=day2,
    )
    assert res_day2["remaining"] == 4

    await _clear()
    month1 = PreviewContext(now=datetime(2024, 1, 15, tzinfo=UTC))
    month2 = PreviewContext(now=datetime(2024, 2, 15, tzinfo=UTC))

    await qs.consume(
        user_id="u1",
        account_id="w1",
        key="compass_calls",
        limit=3,
        scope="month",
        preview=month1,
    )
    res_month2 = await qs.consume(
        user_id="u1",
        account_id="w1",
        key="compass_calls",
        limit=3,
        scope="month",
        preview=month2,
    )
    assert res_month2["remaining"] == 2
