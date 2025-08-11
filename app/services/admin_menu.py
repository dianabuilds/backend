from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import List, Tuple
import logging

from app.models.user import User
from app.schemas.admin_menu import MenuItem, MenuResponse

logger = logging.getLogger(__name__)

# Base menu configuration with groups and links.
# Order values are explicit so the sorting logic can be tested.
BASE_MENU: List[dict] = [
    {
        "id": "overview",
        "label": "Overview",
        "icon": "overview",
        "order": 1,
        "children": [
            {
                "id": "dashboard",
                "label": "Dashboard",
                "path": "/",
                "icon": "dashboard",
                "order": 1,
            }
        ],
    },
    {
        "id": "users",
        "label": "Users",
        "icon": "users",
        "order": 2,
        "children": [
            {
                "id": "users-list",
                "label": "Users",
                "path": "/users",
                "icon": "users",
                "order": 1,
            }
        ],
    },
    {
        "id": "content",
        "label": "Content",
        "icon": "content",
        "order": 3,
        "children": [
            {
                "id": "nodes",
                "label": "Nodes",
                "path": "/nodes",
                "icon": "nodes",
                "order": 1,
            },
            {
                "id": "tags",
                "label": "Tags",
                "path": "/tags",
                "icon": "tags",
                "order": 2,
            },
            {
                "id": "transitions",
                "label": "Transitions",
                "path": "/transitions",
                "icon": "transitions",
                "order": 3,
            },
            {
                "id": "moderation",
                "label": "Moderation",
                "path": "/moderation",
                "icon": "moderation",
                "order": 4,
            },
        ],
    },
    {
        "id": "navigation",
        "label": "Navigation",
        "icon": "navigation",
        "order": 4,
        "children": [
            {
                "id": "navigation-main",
                "label": "Navigation",
                "path": "/navigation",
                "icon": "navigation",
                "order": 1,
            }
        ],
    },
    {
        "id": "telemetry",
        "label": "Data/Telemetry",
        "icon": "telemetry",
        "order": 5,
        "children": [
            {
                "id": "echo",
                "label": "Echo traces",
                "path": "/echo",
                "icon": "echo",
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
                "id": "notifications",
                "label": "Notifications",
                "path": "/notifications",
                "icon": "notifications",
                "order": 3,
            },
            {
                "id": "achievements",
                "label": "Achievements",
                "path": "/achievements",
                "icon": "achievements",
                "order": 4,
            },
            {
                "id": "quests",
                "label": "Quests",
                "path": "/quests",
                "icon": "quests",
                "order": 5,
            },
            {
                "id": "search",
                "label": "Search",
                "path": "/search",
                "icon": "search",
                "order": 6,
            },
        ],
    },
    {
        "id": "tools",
        "label": "Service tools",
        "icon": "tools",
        "order": 6,
        "roles": ["admin"],
        "children": [
            {
                "id": "cache",
                "label": "Cache",
                "path": "/tools/cache",
                "icon": "cache",
                "order": 1,
            },
            {
                "id": "rate-limit",
                "label": "Rate limit",
                "path": "/tools/rate-limit",
                "icon": "rate-limit",
                "order": 2,
            },
            {
                "id": "restrictions",
                "label": "Restrictions",
                "path": "/tools/restrictions",
                "icon": "restrictions",
                "order": 3,
            },
            {
                "id": "audit",
                "label": "Audit log",
                "path": "/tools/audit",
                "icon": "audit",
                "order": 4,
            },
        ],
    },
    {
        "id": "system",
        "label": "System",
        "icon": "system",
        "order": 7,
        "roles": ["admin"],
        "children": [
            {
                "id": "health",
                "label": "Health",
                "path": "/system/health",
                "icon": "health",
                "order": 1,
            }
        ],
    },
    {
        "id": "payments",
        "label": "Payments",
        "path": "/payments",
        "icon": "payments",
        "order": 8,
        "roles": ["admin"],
        "featureFlag": "payments",
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
    result.sort(key=lambda x: (x.order, x.label))
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
