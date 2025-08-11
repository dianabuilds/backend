from datetime import datetime

import pytest

from app.schemas.admin_menu import MenuItem, MenuResponse
from app.services.admin_menu import build_menu


class DummyUser:
    def __init__(self, role: str) -> None:
        self.role = role


def test_build_menu_filters_and_sorts():
    user = DummyUser("admin")
    menu = build_menu(user, [])
    ids = [item.id for item in menu.items]
    assert ids == ["first", "second", "group", "admin-only"]
    group_children = [c.id for c in menu.items[2].children]
    assert group_children == ["g1", "g2"]

    menu_flag = build_menu(user, ["extra"])
    group_children_flag = [c.id for c in menu_flag.items[2].children]
    assert group_children_flag == ["g1", "g2", "flagged"]

    mod_menu = build_menu(DummyUser("moderator"), [])
    mod_ids = [item.id for item in mod_menu.items]
    assert "admin-only" not in mod_ids
    group_children_mod = [c.id for c in mod_menu.items[2].children]
    assert group_children_mod == ["g2"]


def test_menu_depth_validation():
    third_level = MenuItem(id="c", label="C")
    second_level = MenuItem(id="b", label="B", children=[third_level])
    root = MenuItem(id="a", label="A", children=[second_level])
    with pytest.raises(ValueError):
        MenuResponse(items=[root], version="v", generated_at=datetime.utcnow())
