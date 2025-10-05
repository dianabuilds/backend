import pytest

from apps.backend.domains.platform.flags.application.use_cases import (
    check_flag,
    delete_flag,
    list_flags,
    upsert_flag,
)
from apps.backend.domains.platform.flags.domain.models import FeatureFlag, FlagStatus


class DummyService:
    def __init__(self, flags=None):
        self._flags = flags or []
        self.upsert_payload = None
        self.deleted = None
        self.evaluated = []
        self.raise_eval = False

    async def list(self):
        return list(self._flags)

    def _eval_flag(self, flag, claims):
        if self.raise_eval:
            raise RuntimeError("boom")
        return flag.status is not FlagStatus.DISABLED

    async def upsert(self, payload):
        self.upsert_payload = payload
        flag = FeatureFlag(slug=payload["slug"], status=FlagStatus.ALL)
        self._flags.append(flag)
        return flag

    async def delete(self, slug: str):
        self.deleted = slug

    async def evaluate(self, slug: str, claims):
        self.evaluated.append((slug, dict(claims)))
        return slug == "demo"


def make_flag(status=FlagStatus.ALL):
    return FeatureFlag(slug="demo", status=status)


@pytest.mark.asyncio
async def test_list_flags_uses_presenter():
    service = DummyService(flags=[make_flag(), make_flag(status=FlagStatus.DISABLED)])
    result = await list_flags(service)
    assert result["items"][0]["slug"] == "demo"
    assert result["items"][0]["effective"] is True
    assert result["items"][1]["effective"] is False


@pytest.mark.asyncio
async def test_list_flags_handles_eval_error():
    service = DummyService(flags=[make_flag()])
    service.raise_eval = True
    result = await list_flags(service)
    assert result["items"][0]["effective"] is False


@pytest.mark.asyncio
async def test_upsert_flag_returns_presented_flag():
    service = DummyService()
    payload = {"slug": "new-flag"}
    result = await upsert_flag(service, payload)
    assert result["flag"]["slug"] == "new-flag"
    assert service.upsert_payload == payload


@pytest.mark.asyncio
async def test_delete_flag_returns_ok():
    service = DummyService()
    result = await delete_flag(service, "demo")
    assert result == {"ok": True}
    assert service.deleted == "demo"


@pytest.mark.asyncio
async def test_check_flag_uses_service():
    service = DummyService()
    result = await check_flag(service, "demo", {"user": "test"})
    assert result == {"slug": "demo", "on": True}
    assert service.evaluated == [("demo", {"user": "test"})]
