from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import Column, Integer, select
from sqlalchemy.orm import declarative_base

import sys
sys.path.append("apps/backend")
from app.common.scoping import apply_scope

Base = declarative_base()


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer)
    author_id = Column(Integer)


@pytest.fixture
def user() -> SimpleNamespace:
    return SimpleNamespace(id=1, role="user")


@pytest.fixture
def admin() -> SimpleNamespace:
    return SimpleNamespace(id=2, role="admin")


def _where_text(query):
    return str(query.whereclause.compile(compile_kwargs={"literal_binds": True}))


def test_scope_mine(user):
    q = select(Item)
    q, _ = apply_scope(q, user, "mine", 10)
    text = _where_text(q)
    assert "items.account_id = 10" in text
    assert "items.author_id = 1" in text


def test_scope_member(user):
    q = select(Item)
    q, _ = apply_scope(q, user, "member", 5)
    text = _where_text(q)
    assert "items.account_id = 5" in text
    assert "author_id" not in text


def test_scope_invited(user):
    q = select(Item)
    q, _ = apply_scope(q, user, "invited", 8)
    text = _where_text(q)
    assert "items.account_id = 8" in text


def test_scope_space(user):
    q = select(Item)
    q, _ = apply_scope(q, user, "space:7", None)
    text = _where_text(q)
    assert "items.account_id = 7" in text


def test_scope_global_admin(admin):
    q = select(Item)
    q, _ = apply_scope(q, admin, "global", None)
    assert q.whereclause is None


def test_scope_global_forbidden(user):
    q = select(Item)
    with pytest.raises(HTTPException):
        apply_scope(q, user, "global", None)
