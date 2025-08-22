import asyncio

import pytest
from fastapi import HTTPException

from app.domains.premium.application.quota_service import QuotaService


@pytest.fixture()
def service() -> QuotaService:
    return QuotaService()


@pytest.mark.asyncio
async def test_dry_run(service: QuotaService) -> None:
    user = "u1"
    # dry run should not consume
    await service.check_and_consume(user, "echo", dry_run=True, plan="free")
    res = await service.check_and_consume(user, "echo", plan="free")
    assert res["remaining"] == 4


@pytest.mark.asyncio
async def test_idempotency_token(service: QuotaService) -> None:
    user = "u1"
    await service.check_and_consume(user, "echo", idempotency_token="tok1", plan="free")
    # second call with same token should not increase usage
    await service.check_and_consume(user, "echo", idempotency_token="tok1", plan="free")
    res = await service.check_and_consume(user, "echo", plan="free")
    assert res["remaining"] == 3


@pytest.mark.asyncio
async def test_concurrent_limit(service: QuotaService) -> None:
    user = "u1"
    results = []

    async def worker() -> None:
        try:
            await service.check_and_consume(user, "echo", plan="free")
            results.append(True)
        except HTTPException:
            results.append(False)

    await asyncio.gather(*[worker() for _ in range(20)])
    assert sum(results) == 5  # limit for free plan day=5
