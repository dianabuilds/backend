from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

import pytest

from domains.platform.notifications.adapters.consent_audit_sql import (
    SQLNotificationConsentAuditRepo,
)
from domains.platform.notifications.adapters.repo_sql import (
    SQLNotificationPreferenceRepo,
)
from domains.platform.notifications.application.preference_service import (
    PreferenceService,
)
from domains.platform.notifications.models.entities import (
    ConsentAuditRecord,
    DeliveryRequirement,
    DigestMode,
    NotificationChannel,
    NotificationMatrix,
    NotificationTopic,
    PreferenceRecord,
    TopicChannelRule,
)
from domains.platform.notifications.ports import (
    NotificationConsentAuditRepo,
    NotificationMatrixRepo,
    NotificationPreferenceRepo,
)


class _MemoryMatrixRepo(NotificationMatrixRepo):
    def __init__(self, matrix: NotificationMatrix) -> None:
        self._matrix = matrix

    async def load(self, *, use_cache: bool = True) -> NotificationMatrix:
        return self._matrix


class _MemoryPreferenceRepo(NotificationPreferenceRepo):
    def __init__(self) -> None:
        self._storage: dict[str, list[PreferenceRecord]] = {}

    async def list_for_user(self, user_id: str) -> list[PreferenceRecord]:
        return [replace(record) for record in self._storage.get(user_id, [])]

    async def replace_for_user(
        self, user_id: str, records: Sequence[PreferenceRecord]
    ) -> None:
        self._storage[user_id] = [replace(record) for record in records]


class _MemoryAuditRepo(NotificationConsentAuditRepo):
    def __init__(self) -> None:
        self.records: list[ConsentAuditRecord] = []

    async def append_many(self, records: Sequence[ConsentAuditRecord]) -> None:
        self.records.extend(records)


@pytest.fixture()
def sample_matrix() -> NotificationMatrix:
    channels = {
        "in_app": NotificationChannel(
            key="in_app",
            display_name="In-App",
            category="core",
            supports_digest=False,
            requires_consent=False,
            is_active=True,
            position=1,
        ),
        "email": NotificationChannel(
            key="email",
            display_name="Email",
            category="core",
            supports_digest=True,
            requires_consent=False,
            is_active=True,
            position=2,
        ),
    }
    topics = {
        "account.security": NotificationTopic(
            key="account.security",
            category="system",
            display_name="Account Security",
            default_digest=DigestMode.INSTANT,
            position=1,
        )
    }
    rules = {
        ("account.security", "in_app"): TopicChannelRule(
            topic_key="account.security",
            channel_key="in_app",
            delivery=DeliveryRequirement.MANDATORY,
            position=1,
        ),
        ("account.security", "email"): TopicChannelRule(
            topic_key="account.security",
            channel_key="email",
            delivery=DeliveryRequirement.DEFAULT_ON,
            default_digest=DigestMode.INSTANT,
            position=2,
        ),
    }
    return NotificationMatrix(topics=topics, channels=channels, rules=rules)


@pytest.mark.asyncio
async def test_preference_roundtrip(sample_matrix: NotificationMatrix) -> None:
    matrix_repo = _MemoryMatrixRepo(sample_matrix)
    pref_repo = _MemoryPreferenceRepo()
    audit_repo = _MemoryAuditRepo()
    service = PreferenceService(
        matrix_repo=matrix_repo,
        preference_repo=pref_repo,
        audit_repo=audit_repo,
        flag_service=None,
    )

    user_id = "00000000-0000-0000-0000-000000000001"

    defaults = await service.get_preferences(user_id, context={"sub": user_id})
    assert defaults["account.security"]["in_app"]["opt_in"] is True
    assert defaults["account.security"]["email"]["opt_in"] is True

    await service.set_preferences(
        user_id,
        {
            "account.security": {
                "email": {
                    "opt_in": False,
                    "digest": "weekly",
                    "quiet_hours": [22, 23, 0],
                }
            }
        },
        actor_id=user_id,
        source="user",
        context={"sub": user_id},
        request_id="req-1",
    )

    stored = pref_repo._storage[user_id]
    assert len(stored) == 2
    email_pref = next(p for p in stored if p.channel_key == "email")
    assert email_pref.opt_in is False
    assert email_pref.digest == "weekly"
    assert email_pref.quiet_hours == (0, 22, 23)

    updated = await service.get_preferences(user_id, context={"sub": user_id})
    assert updated["account.security"]["email"]["opt_in"] is False
    assert updated["account.security"]["email"]["digest"] == "weekly"
    assert updated["account.security"]["in_app"]["opt_in"] is True

    assert audit_repo.records, "Audit entries should be captured for changes"
    last_audit = audit_repo.records[-1]
    assert last_audit.new_state["opt_in"] is False
    assert last_audit.source == "user"


class _FailingPreferenceEngine:
    def begin(self):
        raise AssertionError("should not hit storage for invalid user ids")


class _FailingAuditEngine:
    def begin(self):
        raise AssertionError("should not write audit for invalid user ids")


@pytest.mark.asyncio
async def test_sql_preference_repo_ignores_invalid_user_ids():
    repo = SQLNotificationPreferenceRepo(_FailingPreferenceEngine())
    assert await repo.list_for_user("not-a-uuid") == []
    await repo.replace_for_user("not-a-uuid", [])


@pytest.mark.asyncio
async def test_sql_consent_audit_repo_ignores_invalid_user_ids():
    repo = SQLNotificationConsentAuditRepo(_FailingAuditEngine())
    record = ConsentAuditRecord(
        user_id="not-a-uuid",
        topic_key="topic.sample",
        channel_key="in_app",
        previous_state=None,
        new_state={},
        source="user",
        changed_by=None,
        request_id=None,
    )
    await repo.append_many([record])


@pytest.mark.asyncio
async def test_preference_service_overview(sample_matrix: NotificationMatrix) -> None:
    matrix_repo = _MemoryMatrixRepo(sample_matrix)
    pref_repo = _MemoryPreferenceRepo()
    audit_repo = _MemoryAuditRepo()
    service = PreferenceService(
        matrix_repo=matrix_repo,
        preference_repo=pref_repo,
        audit_repo=audit_repo,
        flag_service=None,
    )

    user_id = "00000000-0000-0000-0000-000000000002"
    context = {"sub": user_id}

    overview = await service.get_preferences_overview(user_id, context=context)
    assert overview["summary"]["total_channels"] == 2
    channels = {channel["key"]: channel for channel in overview["channels"]}
    assert channels["in_app"]["status"] == "required"
    assert channels["email"]["status"] == "recommended"

    await service.set_preferences(
        user_id,
        {"account.security": {"email": {"opt_in": False, "digest": "weekly"}}},
        actor_id=user_id,
        source="user",
        context=context,
        request_id="req-2",
    )

    updated = await service.get_preferences_overview(user_id, context=context)
    updated_channels = {channel["key"]: channel for channel in updated["channels"]}
    assert updated_channels["email"]["opt_in"] is False
    assert updated["summary"]["active_channels"] == 1
    assert updated["summary"].get("email_digest") == "weekly"
    assert isinstance(updated["summary"].get("updated_at"), str)
