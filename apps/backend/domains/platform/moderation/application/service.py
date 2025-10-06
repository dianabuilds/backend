from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from datetime import datetime
from functools import wraps
from typing import Any

from ..adapters.base import ModerationSnapshotStore
from ..domain.records import (
    AIRuleRecord,
    AppealRecord,
    ContentRecord,
    ModeratorNoteRecord,
    ReportRecord,
    SanctionRecord,
    TicketMessageRecord,
    TicketRecord,
    UserRecord,
)
from .ai_rules import (
    create_rule as _ai_rules_create_rule,
)
from .ai_rules import (
    delete_rule as _ai_rules_delete_rule,
)
from .ai_rules import (
    get_rule as _ai_rules_get_rule,
)
from .ai_rules import (
    list_rules as _ai_rules_list_rules,
)
from .ai_rules import (
    rules_history as _ai_rules_rules_history,
)
from .ai_rules import (
    test_rule as _ai_rules_test_rule,
)
from .ai_rules import (
    update_rule as _ai_rules_update_rule,
)
from .appeals.commands import decide_appeal as _appeals_decide_appeal
from .appeals.queries import (
    get_appeal as _appeals_get_appeal,
)
from .appeals.queries import (
    list_appeals as _appeals_list_appeals,
)
from .common import (
    generate_id as _generate_id_value,
)
from .common import (
    isoformat_utc,
    parse_iso_datetime,
    utc_now,
)
from .content.commands import (
    decide_content as _content_decide_content,
)
from .content.commands import (
    edit_content as _content_edit_content,
)
from .content.queries import (
    get_content as _content_get_content,
)
from .content.queries import (
    list_content as _content_list_content,
)
from .overview.queries import get_overview as _overview_get_overview
from .reports import (
    get_report as _reports_get_report,
)
from .reports import (
    list_reports as _reports_list_reports,
)
from .reports import (
    resolve_report as _reports_resolve_report,
)
from .sanctions.commands import (
    add_note as _sanctions_add_note,
)
from .sanctions.commands import (
    issue_sanction as _sanctions_issue_sanction,
)
from .sanctions.commands import (
    update_sanction as _sanctions_update_sanction,
)
from .seed import seed_demo
from .snapshots import ModerationSnapshot, ModerationSnapshotCodec
from .tickets import (
    add_ticket_message as _tickets_add_ticket_message,
)
from .tickets import (
    escalate_ticket as _tickets_escalate_ticket,
)
from .tickets import (
    get_ticket as _tickets_get_ticket,
)
from .tickets import (
    list_ticket_messages as _tickets_list_ticket_messages,
)
from .tickets import (
    list_tickets as _tickets_list_tickets,
)
from .tickets import (
    update_ticket as _tickets_update_ticket,
)
from .users import (
    ensure_user_stub as _users_ensure_user_stub,
)
from .users import (
    get_user as _users_get_user,
)
from .users import (
    list_users as _users_list_users,
)
from .users import (
    update_roles as _users_update_roles,
)
from .users import (
    warnings_count_recent as _users_warnings_count_recent,
)

logger = logging.getLogger(__name__)


def _ensure_loaded_decorator(func):
    @wraps(func)
    async def wrapper(self: PlatformModerationService, *args, **kwargs):
        await self._ensure_loaded()
        return await func(self, *args, **kwargs)

    return wrapper


def _mutating_operation(func):
    @wraps(func)
    async def wrapper(self: PlatformModerationService, *args, **kwargs):
        await self._ensure_loaded()
        result = await func(self, *args, **kwargs)
        self._dirty = True
        await self._persist()
        return result

    return wrapper


class PlatformModerationService:
    def __init__(
        self, storage: ModerationSnapshotStore | None = None, *, seed_demo: bool = True
    ):
        self._lock = asyncio.Lock()
        self._users: dict[str, UserRecord] = {}
        self._sanctions: dict[str, SanctionRecord] = {}
        self._notes: dict[str, ModeratorNoteRecord] = {}
        self._reports: dict[str, ReportRecord] = {}
        self._content: dict[str, ContentRecord] = {}
        self._tickets: dict[str, TicketRecord] = {}
        self._ticket_messages: dict[str, TicketMessageRecord] = {}
        self._appeals: dict[str, AppealRecord] = {}
        self._ai_rules: dict[str, AIRuleRecord] = {}
        self._idempotency: dict[str, str] = {}
        self._storage = storage
        self._seed_requested = seed_demo
        self._loaded = False
        self._dirty = False
        self._snapshot_codec = ModerationSnapshotCodec(
            isoformat=self._iso,
            parse_datetime=self._parse_datetime,
            now_factory=self._now,
        )

    def _now(self) -> datetime:
        return utc_now()

    def _iso(self, dt: datetime | None) -> str | None:
        return isoformat_utc(dt)

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self._storage and self._storage.enabled():
            snapshot = await self._storage.load()
            if snapshot:
                await self._restore_from_snapshot(snapshot)
            elif self._seed_requested:
                async with self._lock:
                    self._seed_demo()
                self._dirty = True
                await self._persist()
        elif self._seed_requested:
            async with self._lock:
                self._seed_demo()
        self._loaded = True
        self._dirty = False

    async def _snapshot(self) -> dict[str, Any]:
        async with self._lock:
            snapshot = ModerationSnapshot(
                users=dict(self._users),
                sanctions=dict(self._sanctions),
                notes=dict(self._notes),
                reports=dict(self._reports),
                content=dict(self._content),
                tickets=dict(self._tickets),
                ticket_messages=dict(self._ticket_messages),
                appeals=dict(self._appeals),
                ai_rules=dict(self._ai_rules),
                idempotency=dict(self._idempotency),
            )
        return self._snapshot_codec.dump(snapshot)

    async def _restore_from_snapshot(self, payload: Mapping[str, Any]) -> None:
        snapshot = self._snapshot_codec.load(payload)
        async with self._lock:
            self._users = snapshot.users
            self._sanctions = snapshot.sanctions
            self._notes = snapshot.notes
            self._reports = snapshot.reports
            self._content = snapshot.content
            self._tickets = snapshot.tickets
            self._ticket_messages = snapshot.ticket_messages
            self._appeals = snapshot.appeals
            self._ai_rules = snapshot.ai_rules
            self._idempotency = snapshot.idempotency
            self._dirty = False

    async def _persist(self) -> None:
        if not self._storage or not self._storage.enabled() or not self._dirty:
            self._dirty = False
            return
        snapshot = await self._snapshot()
        await self._storage.save(snapshot)
        self._dirty = False

    def _parse_datetime(self, value: Any) -> datetime | None:
        return parse_iso_datetime(value, logger_override=logger)

    def _generate_id(self, prefix: str) -> str:
        return _generate_id_value(prefix)

    def _seed_demo(self) -> None:
        seed_demo(self)

    @_ensure_loaded_decorator
    async def get_overview(self, *args: Any, **kwargs: Any) -> Any:
        return await _overview_get_overview(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def list_content(self, *args: Any, **kwargs: Any) -> Any:
        return await _content_list_content(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def get_content(self, *args: Any, **kwargs: Any) -> Any:
        return await _content_get_content(self, *args, **kwargs)

    @_mutating_operation
    async def decide_content(self, *args: Any, **kwargs: Any) -> Any:
        return await _content_decide_content(self, *args, **kwargs)

    @_mutating_operation
    async def edit_content(self, *args: Any, **kwargs: Any) -> Any:
        return await _content_edit_content(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def list_reports(self, *args: Any, **kwargs: Any) -> Any:
        return await _reports_list_reports(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def get_report(self, *args: Any, **kwargs: Any) -> Any:
        return await _reports_get_report(self, *args, **kwargs)

    @_mutating_operation
    async def resolve_report(self, *args: Any, **kwargs: Any) -> Any:
        return await _reports_resolve_report(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def list_tickets(self, *args: Any, **kwargs: Any) -> Any:
        return await _tickets_list_tickets(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def get_ticket(self, *args: Any, **kwargs: Any) -> Any:
        return await _tickets_get_ticket(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def list_ticket_messages(self, *args: Any, **kwargs: Any) -> Any:
        return await _tickets_list_ticket_messages(self, *args, **kwargs)

    @_mutating_operation
    async def add_ticket_message(self, *args: Any, **kwargs: Any) -> Any:
        return await _tickets_add_ticket_message(self, *args, **kwargs)

    @_mutating_operation
    async def update_ticket(self, *args: Any, **kwargs: Any) -> Any:
        return await _tickets_update_ticket(self, *args, **kwargs)

    @_mutating_operation
    async def escalate_ticket(self, *args: Any, **kwargs: Any) -> Any:
        return await _tickets_escalate_ticket(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def list_appeals(self, *args: Any, **kwargs: Any) -> Any:
        return await _appeals_list_appeals(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def get_appeal(self, *args: Any, **kwargs: Any) -> Any:
        return await _appeals_get_appeal(self, *args, **kwargs)

    @_mutating_operation
    async def decide_appeal(self, *args: Any, **kwargs: Any) -> Any:
        return await _appeals_decide_appeal(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def list_rules(self, *args: Any, **kwargs: Any) -> Any:
        return await _ai_rules_list_rules(self, *args, **kwargs)

    @_mutating_operation
    async def create_rule(self, *args: Any, **kwargs: Any) -> Any:
        return await _ai_rules_create_rule(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def get_rule(self, *args: Any, **kwargs: Any) -> Any:
        return await _ai_rules_get_rule(self, *args, **kwargs)

    @_mutating_operation
    async def update_rule(self, *args: Any, **kwargs: Any) -> Any:
        return await _ai_rules_update_rule(self, *args, **kwargs)

    @_mutating_operation
    async def delete_rule(self, *args: Any, **kwargs: Any) -> Any:
        return await _ai_rules_delete_rule(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def test_rule(self, *args: Any, **kwargs: Any) -> Any:
        return await _ai_rules_test_rule(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def rules_history(self, *args: Any, **kwargs: Any) -> Any:
        return await _ai_rules_rules_history(self, *args, **kwargs)

    @_mutating_operation
    async def issue_sanction(self, *args: Any, **kwargs: Any) -> Any:
        return await _sanctions_issue_sanction(self, *args, **kwargs)

    @_mutating_operation
    async def update_sanction(self, *args: Any, **kwargs: Any) -> Any:
        return await _sanctions_update_sanction(self, *args, **kwargs)

    @_mutating_operation
    async def add_note(self, *args: Any, **kwargs: Any) -> Any:
        return await _sanctions_add_note(self, *args, **kwargs)

    @_mutating_operation
    async def ensure_user_stub(self, *args: Any, **kwargs: Any) -> Any:
        return await _users_ensure_user_stub(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def warnings_count_recent(self, *args: Any, **kwargs: Any) -> Any:
        return await _users_warnings_count_recent(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def list_users(self, *args: Any, **kwargs: Any) -> Any:
        return await _users_list_users(self, *args, **kwargs)

    @_ensure_loaded_decorator
    async def get_user(self, *args: Any, **kwargs: Any) -> Any:
        return await _users_get_user(self, *args, **kwargs)

    @_mutating_operation
    async def update_roles(self, *args: Any, **kwargs: Any) -> Any:
        return await _users_update_roles(self, *args, **kwargs)
