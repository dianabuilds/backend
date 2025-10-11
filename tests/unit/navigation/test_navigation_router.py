from __future__ import annotations

from fastapi import APIRouter

from domains.product.navigation.api import http as navigation_http


def test_make_router_registers_routes(monkeypatch):
    calls = {"transition": None, "relations": None, "admin": None}

    def fake_register_transition(router: APIRouter):
        calls["transition"] = router

    def fake_register_relations(router: APIRouter):
        calls["relations"] = router

    def fake_register_admin(router: APIRouter, dependency):
        calls["admin"] = (router, dependency)

    def fake_require_role(role: str):
        assert role == "moderator"

        def dependency():
            return True

        return dependency

    monkeypatch.setattr(
        navigation_http, "register_transition_routes", fake_register_transition
    )
    monkeypatch.setattr(
        navigation_http, "register_relations_routes", fake_register_relations
    )
    monkeypatch.setattr(
        navigation_http, "register_admin_relations_routes", fake_register_admin
    )
    monkeypatch.setattr(navigation_http, "require_role_db", fake_require_role)

    router = navigation_http.make_router()

    assert isinstance(router, APIRouter)
    assert router.prefix == "/v1/navigation"
    assert calls["transition"] is router
    assert calls["relations"] is router
    admin_router, admin_dep = calls["admin"]
    assert admin_router is router
    assert callable(admin_dep)
    assert admin_dep() is True
