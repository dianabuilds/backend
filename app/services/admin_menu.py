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

# Base menu configuration. Items here are intentionally unsorted to test sorting.
BASE_MENU: List[dict] = [
    {"id": "second", "label": "Second", "path": "/second", "order": 2},
    {"id": "first", "label": "First", "path": "/first", "order": 1},
    {
        "id": "group",
        "label": "Group",
        "order": 3,
        "children": [
            {"id": "g2", "label": "G2", "path": "/g2", "order": 2},
            {"id": "g1", "label": "G1", "path": "/g1", "order": 1, "roles": ["admin"]},
            {
                "id": "flagged",
                "label": "Flagged",
                "path": "/flag",
                "order": 3,
                "featureFlag": "extra",
            },
        ],
    },
    {"id": "admin-only", "label": "Admin", "path": "/admin", "order": 4, "roles": ["admin"]},
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
