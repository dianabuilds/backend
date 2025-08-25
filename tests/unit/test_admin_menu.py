import sys
import types
from types import SimpleNamespace

# menu_service imports User from the users module, which pulls in the DB model and
# causes circular imports in tests. Stub it with a lightweight placeholder.
sys.modules.setdefault(
    "app.domains.users.infrastructure.models.user", types.SimpleNamespace(User=object)
)
from app.domains.admin.application.menu_service import build_menu  # noqa: E402


def collect_ids(items):
    res = []
    for item in items:
        res.append(item.id)
        res.extend(collect_ids(item.children))
    return res


def test_admin_sees_all_sections():
    user = SimpleNamespace(role="admin")
    menu = build_menu(user, [])
    ids = collect_ids(menu.items)
    assert {"content", "navigation", "monitoring", "administration"}.issubset(ids)


def test_moderator_moderation_flag():
    user = SimpleNamespace(role="moderator")
    menu = build_menu(user, ["moderation.enabled"])
    ids = collect_ids(menu.items)
    assert "moderation" in ids
    assert "premium-plans" not in ids
    assert "cache" not in ids


def test_user_has_limited_access():
    user = SimpleNamespace(role="user")
    menu = build_menu(user, [])
    ids = collect_ids(menu.items)
    assert "premium-plans" not in ids
    assert "moderation" not in ids
    assert "rum" not in ids
    assert "navigation-main" in ids
