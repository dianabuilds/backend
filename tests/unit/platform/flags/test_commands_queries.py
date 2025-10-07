import pytest

from domains.platform.flags.application.commands import (
    delete_flag,
    upsert_flag,
)
from domains.platform.flags.application.queries import (
    check_flag,
    list_flags,
)
from domains.platform.flags.domain.models import FeatureFlag, FlagStatus


class DummyService:
    def __init__(self, flags=None):
        self._flags = list(flags or [])
        self.upsert_payload = None
        self.deleted = None
        self.evaluated = []

    async def list(self):
        return list(self._flags)

    def effective(self, flag, claims=None):
        return flag.status is not FlagStatus.DISABLED

    async def upsert(self, payload):
        self.upsert_payload = payload
        data = dict(payload)
        flag = FeatureFlag(slug=data["slug"], status=FlagStatus.ALL)
        self._flags.append(flag)
        return flag

    async def delete(self, slug: str):
        self.deleted = slug

    async def evaluate(self, slug: str, claims=None):
        self.evaluated.append((slug, dict(claims or {})))
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
