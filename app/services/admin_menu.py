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
            # {
            #     "id": "moderation",
            #     "label": "Moderation",
            #     "path": "/moderation",
            #     "icon": "moderation",
            #     "order": 3,
            # },
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
                "id": "nav-traces",
                "label": "Traces",
                "path": "/traces",
                "icon": "traces",
                "order": 4,
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
        "id": "notifications-top",
        "label": "Notifications",
        "path": "/notifications",
        "icon": "notifications",
        "order": 2,  # рядом вверху
        "hidden": True,  # hidden by default, can be enabled by flags later
    },
    {
        "id": "quests-top",
        "label": "Quests",
        "path": "/quests",
        "icon": "quests",
        "order": 3,
        "hidden": False,
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
    {
        "id": "achievements-top",
        "label": "Achievements",
        "path": "/achievements",
        "icon": "achievements",
        "order": 9,  # внизу, ниже контента
        "hidden": True,
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
    # Сортируем только по order; стабильная сортировка сохранит исходный порядок при равных order
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
    """Очистить кеш меню, чтобы следующая загрузка отдала актуальную конфигурацию."""
    _menu_cache.clear()


def invalidate_menu_cache() -> None:
    """Очистить кеш меню, чтобы следующая загрузка отдала актуальную конфигурацию."""
    _menu_cache.clear()
