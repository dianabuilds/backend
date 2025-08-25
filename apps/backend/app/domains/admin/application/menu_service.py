from __future__ import annotations

import hashlib
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Tuple

from app.domains.users.infrastructure.models.user import User
from app.schemas.admin_menu import MenuItem, MenuResponse

logger = logging.getLogger(__name__)

# Базовая конфигурация меню (группы, ссылки, роли, фиче-флаги)
BASE_MENU: List[dict] = [
    {
        "id": "observability",
        "label": "Observability",
        "icon": "activity",
        "order": 1,
        "children": [
            {"id": "dashboard", "label": "Dashboard", "path": "/", "icon": "dashboard", "order": 1},
            {"id": "nav-traces", "label": "Traces", "path": "/traces", "icon": "traces", "order": 2},
            {
                "id": "telemetry-rum",
                "label": "RUM",
                "path": "/telemetry",
                "icon": "telemetry",
                "order": 3,
                "roles": ["admin", "moderator"],
            },
            {
                "id": "health",
                "label": "Health",
                "path": "/system/health",
                "icon": "health",
                "order": 4,
                "roles": ["admin"],
            },
        ],
    },
    {
        "id": "administration",
        "label": "Administration",
        "icon": "users",
        "order": 2,
        "children": [
            {"id": "users-list", "label": "Users", "path": "/users", "icon": "users", "order": 1},
            {"id": "nodes", "label": "Nodes", "path": "/nodes", "icon": "nodes", "order": 2},
            {"id": "tags", "label": "Tags", "path": "/tags", "icon": "tags", "order": 3},
            {
                "id": "quests",
                "label": "Quests",
                "path": "/quests",
                "icon": "quests",
                "order": 4,
                "roles": ["admin", "moderator"],
            },
            {
                "id": "moderation",
                "label": "Moderation",
                "path": "/moderation",
                "icon": "moderation",
                "order": 5,
                "roles": ["moderator", "admin"],
                "featureFlag": "moderation.enabled",
            },
            {"id": "ai-quests-main", "label": "Generator", "path": "/ai/quests", "icon": "ai", "order": 6},
            {"id": "ai-worlds", "label": "Worlds", "path": "/ai/worlds", "icon": "nodes", "order": 7},
            {"id": "ai-settings", "label": "AI Settings", "path": "/ai/settings", "icon": "ai", "order": 8},
            {"id": "ai-rate-limits", "label": "Rate limits", "path": "/ai/rate-limits", "icon": "rate-limit", "order": 9},
            {
                "id": "premium-plans",
                "label": "Plans",
                "path": "/premium/plans",
                "icon": "payments",
                "order": 10,
                "roles": ["admin"],
            },
            {
                "id": "premium-limits",
                "label": "Limits",
                "path": "/premium/limits",
                "icon": "rate-limit",
                "order": 11,
                "roles": ["admin"],
            },
            {
                "id": "cache",
                "label": "Cache",
                "path": "/tools/cache",
                "icon": "cache",
                "order": 12,
                "roles": ["admin"],
            },
            {
                "id": "rate-limit",
                "label": "Rate limit",
                "path": "/tools/rate-limit",
                "icon": "rate-limit",
                "order": 13,
                "roles": ["admin"],
            },
            {
                "id": "restrictions",
                "label": "Restrictions",
                "path": "/tools/restrictions",
                "icon": "restrictions",
                "order": 14,
                "roles": ["admin"],
            },
            {
                "id": "audit",
                "label": "Audit log",
                "path": "/tools/audit",
                "icon": "audit",
                "order": 15,
                "roles": ["admin"],
            },
            {
                "id": "flags",
                "label": "Feature flags",
                "path": "/tools/flags",
                "icon": "flags",
                "order": 16,
                "roles": ["admin"],
            },
            {
                "id": "search-settings",
                "label": "Search settings",
                "path": "/tools/search-settings",
                "icon": "search",
                "order": 17,
                "roles": ["admin"],
            },
            {
                "id": "workspace-metrics",
                "label": "Workspace metrics",
                "path": "/tools/workspace-metrics",
                "icon": "activity",
                "order": 18,
                "roles": ["admin"],
            },
            {
                "id": "payments-gateways",
                "label": "Gateways",
                "path": "/payments",
                "icon": "payments",
                "order": 19,
                "roles": ["admin"],
                "featureFlag": "payments",
            },
            {
                "id": "payments-transactions",
                "label": "Transactions",
                "path": "/payments/transactions",
                "icon": "audit",
                "order": 20,
                "roles": ["admin"],
                "featureFlag": "payments",
            },
        ],
    },
    {
        "id": "navigation",
        "label": "Navigation",
        "icon": "navigation",
        "order": 3,
        "children": [
            {"id": "navigation-main", "label": "Navigation", "path": "/navigation", "icon": "navigation", "order": 1},
            {"id": "nav-transitions", "label": "Transitions", "path": "/transitions", "icon": "transitions", "order": 2},
            {"id": "nav-echo", "label": "Echo", "path": "/echo", "icon": "echo", "order": 3},
        ],
    },
    {
        "id": "notifications-top",
        "label": "Notifications",
        "path": "/notifications",
        "icon": "notifications",
        "order": 4,
        "hidden": False,
    },
    {"id": "quests-top", "label": "Quests", "path": "/quests", "icon": "quests", "order": 5, "hidden": True},
    {
        "id": "achievements-top",
        "label": "Achievements",
        "path": "/achievements",
        "icon": "achievements",
        "order": 6,
        "hidden": False,
    },
]

CACHE_TTL = 45  # seconds
_menu_cache: dict[Tuple[str, Tuple[str, ...]], Tuple[float, MenuResponse, str]] = {}


def _filter_and_convert(items: List[dict], role: str, flags: set[str]) -> List[MenuItem]:
    result: List[MenuItem] = []
    for raw in items:
        if raw.get("hidden"):
            continue
        allowed_roles = raw.get("roles")
        if allowed_roles and role not in allowed_roles:
            continue
        flag = raw.get("featureFlag")
        if flag and flag not in flags:
            continue
        children = _filter_and_convert(raw.get("children", []), role, flags)
        if not children and not raw.get("path") and not raw.get("external"):
            continue
        item = MenuItem(
            id=raw["id"],
            label=raw["label"],
            path=raw.get("path"),
            icon=raw.get("icon"),
            order=int(raw.get("order", 100)),
            children=children,
            roles=allowed_roles,
            feature_flag=flag,
            external=bool(raw.get("external", False)),
            divider=bool(raw.get("divider", False)),
            hidden=bool(raw.get("hidden", False)),
        )
        result.append(item)
    result.sort(key=lambda x: x.order)
    return result


def build_menu(user: User, flags: List[str]) -> MenuResponse:
    role = getattr(user, "role", "")
    items = _filter_and_convert(BASE_MENU, role, set(flags))
    items_dump = [item.model_dump(by_alias=True) for item in items]
    version = hashlib.sha256(json.dumps(items_dump, sort_keys=True).encode()).hexdigest()
    return MenuResponse(items=items, version=version, generated_at=datetime.now(timezone.utc))


def get_cached_menu(user: User, flags: List[str]) -> tuple[MenuResponse, str, bool]:
    key = (getattr(user, "role", ""), tuple(sorted(flags)))
    now = time.time()
    cached = _menu_cache.get(key)
    if cached and cached[0] > now:
        return cached[1], cached[2], True
    menu = build_menu(user, flags)
    etag = menu.version
    _menu_cache[key] = (now + CACHE_TTL, menu, etag)
    return menu, etag, False


def count_items(items: List[MenuItem]) -> int:
    total = 0
    for item in items:
        total += 1
        total += count_items(item.children)
    return total


def invalidate_menu_cache() -> None:
    _menu_cache.clear()
