from __future__ import annotations

# mypy: ignore-errors
import hashlib
import json
import logging
import time
from datetime import datetime, timezone

from app.domains.users.infrastructure.models.user import User
from app.schemas.admin_menu import MenuItem, MenuResponse

logger = logging.getLogger(__name__)

# Базовая конфигурация меню (группы, ссылки, роли, фиче-флаги)
BASE_MENU: list[dict] = [
    {
        "id": "content",
        "label": "Content",
        "icon": "file",
        "order": 1,
        "children": [
            {
                "id": "nodes",
                "label": "Nodes",
                "path": "/nodes",
                "icon": "nodes",
                "order": 1,
            },
            {
                "id": "quests",
                "label": "Quests",
                "path": "/quests",
                "icon": "quests",
                "order": 2,
                "roles": ["admin", "moderator"],
            },
            {
                "id": "tags",
                "label": "Tags",
                "path": "/tags",
                "icon": "tags",
                "order": 3,
            },
            {
                "id": "ai-worlds",
                "label": "Worlds",
                "path": "/ai/worlds",
                "icon": "nodes",
                "order": 4,
            },
            {
                "id": "achievements",
                "label": "Achievements",
                "path": "/achievements",
                "icon": "achievements",
                "order": 5,
            },
            {
                "id": "ai-quests-main",
                "label": "Generator",
                "path": "/ai/quests",
                "icon": "ai",
                "order": 6,
            },
        ],
    },
    {
        "id": "navigation",
        "label": "Navigation",
        "icon": "navigation",
        "order": 2,
        "children": [
            {
                "id": "navigation-main",
                "label": "Navigation",
                "path": "/navigation",
                "icon": "navigation",
                "order": 1,
            },
            {
                "id": "nav-transitions",
                "label": "Transitions",
                "path": "/transitions",
                "icon": "transitions",
                "order": 2,
            },
            {
                "id": "nav-echo",
                "label": "Echo",
                "path": "/echo",
                "icon": "echo",
                "order": 3,
            },
            {
                "id": "nav-trace",
                "label": "Trace",
                "path": "/transitions/trace",
                "icon": "navigation",
                "order": 4,
            },
        ],
    },
    {
        "id": "monitoring",
        "label": "Monitoring",
        "icon": "activity",
        "order": 3,
        "children": [
            {
                "id": "dashboard",
                "label": "Dashboard",
                "path": "/",
                "icon": "dashboard",
                "order": 1,
            },
            {
                "id": "traces",
                "label": "Traces",
                "path": "/traces",
                "icon": "traces",
                "order": 2,
            },
            {
                "id": "rum",
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
            {
                "id": "workspace-metrics",
                "label": "Workspace metrics",
                "path": "/tools/workspace-metrics",
                "icon": "activity",
                "order": 5,
                "roles": ["admin"],
            },
        ],
    },
    {
        "id": "administration",
        "label": "Administration",
        "icon": "users",
        "order": 4,
        "children": [
            {
                "id": "users-list",
                "label": "Users",
                "path": "/users",
                "icon": "users",
                "order": 1,
            },
            {
                "id": "premium-plans",
                "label": "Plans",
                "path": "/premium/plans",
                "icon": "payments",
                "order": 2,
                "roles": ["admin"],
            },
            {
                "id": "premium-limits",
                "label": "Limits",
                "path": "/premium/limits",
                "icon": "rate-limit",
                "order": 3,
                "roles": ["admin"],
            },
            {
                "id": "rate-limits",
                "label": "Rate limits",
                "path": "/tools/rate-limit",
                "icon": "rate-limit",
                "order": 4,
                "roles": ["admin"],
            },
            {
                "id": "restrictions",
                "label": "Restrictions",
                "path": "/tools/restrictions",
                "icon": "restrictions",
                "order": 5,
                "roles": ["admin"],
            },
            {
                "id": "flags",
                "label": "Feature flags",
                "path": "/tools/flags",
                "icon": "flags",
                "order": 6,
                "roles": ["admin"],
            },
            {
                "id": "search-settings",
                "label": "Search settings",
                "path": "/tools/search-settings",
                "icon": "search",
                "order": 7,
                "roles": ["admin"],
            },
            {
                "id": "audit",
                "label": "Audit log",
                "path": "/tools/audit",
                "icon": "audit",
                "order": 8,
                "roles": ["admin"],
            },
            {
                "id": "cache",
                "label": "Cache",
                "path": "/tools/cache",
                "icon": "cache",
                "order": 9,
                "roles": ["admin"],
            },
            {
                "id": "ai-system-settings",
                "label": "AI Settings",
                "path": "/ai/system",
                "icon": "settings",
                "order": 10,
                "roles": ["admin"],
            },
        ],
    },
    {
        "id": "global-settings",
        "label": "Global settings",
        "icon": "settings",
        "order": 5,
        "roles": ["admin"],
        "children": [
            {
                "id": "global-authentication",
                "label": "Authentication",
                "path": "/settings/authentication",
                "icon": "lock",
                "order": 1,
            },
            {
                "id": "global-payments",
                "label": "Payments",
                "path": "/settings/payments",
                "icon": "credit-card",
                "order": 2,
            },
            {
                "id": "global-integrations",
                "label": "Integrations",
                "path": "/settings/integrations",
                "icon": "plug",
                "order": 3,
            },
            {
                "id": "global-metrics",
                "label": "Metrics",
                "path": "/settings/metrics",
                "icon": "activity",
                "order": 4,
            },
            {
                "id": "global-feature-flags",
                "label": "Feature flags",
                "path": "/settings/feature-flags",
                "icon": "flag",
                "order": 5,
            },
        ],
    },
]

CACHE_TTL = 45  # seconds
_menu_cache: dict[tuple[str, tuple[str, ...]], tuple[float, MenuResponse, str]] = {}


def _filter_and_convert(
    items: list[dict], role: str, flags: set[str]
) -> list[MenuItem]:
    result: list[MenuItem] = []
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


def build_menu(user: User, flags: list[str]) -> MenuResponse:
    role = getattr(user, "role", "")
    items = _filter_and_convert(BASE_MENU, role, set(flags))
    items_dump = [item.model_dump(by_alias=True) for item in items]
    version = hashlib.sha256(
        json.dumps(items_dump, sort_keys=True).encode()
    ).hexdigest()
    return MenuResponse(
        items=items, version=version, generated_at=datetime.now(timezone.utc)
    )


def get_cached_menu(user: User, flags: list[str]) -> tuple[MenuResponse, str, bool]:
    key = (getattr(user, "role", ""), tuple(sorted(flags)))
    now = time.time()
    cached = _menu_cache.get(key)
    if cached and cached[0] > now:
        return cached[1], cached[2], True
    menu = build_menu(user, flags)
    etag = menu.version
    _menu_cache[key] = (now + CACHE_TTL, menu, etag)
    return menu, etag, False


def count_items(items: list[MenuItem]) -> int:
    total = 0
    for item in items:
        total += 1
        total += count_items(item.children)
    return total


def invalidate_menu_cache() -> None:
    _menu_cache.clear()
