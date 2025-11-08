from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def sitecustomize_module(monkeypatch):
    module = importlib.import_module("apps.backend.sitecustomize")
    yield module
    importlib.reload(module)


def test_sitecustomize_enforces_selector_policy(monkeypatch, sitecustomize_module):
    applied = {}

    class DummySelector:
        pass

    class DummyProactor:
        pass

    monkeypatch.setattr(sitecustomize_module.sys, "platform", "win32")
    monkeypatch.setattr(
        sitecustomize_module.asyncio,
        "WindowsSelectorEventLoopPolicy",
        lambda: DummySelector(),
    )
    monkeypatch.setattr(
        sitecustomize_module.asyncio,
        "WindowsProactorEventLoopPolicy",
        DummyProactor,
    )
    monkeypatch.setattr(
        sitecustomize_module.asyncio,
        "get_event_loop_policy",
        lambda: DummyProactor(),
    )

    def fake_set(policy):
        applied["policy"] = policy

    monkeypatch.setattr(sitecustomize_module.asyncio, "set_event_loop_policy", fake_set)

    sitecustomize_module._apply_windows_selector_policy()

    assert isinstance(applied["policy"], DummySelector)


def test_sitecustomize_noop_on_non_windows(monkeypatch, sitecustomize_module):
    monkeypatch.setattr(sitecustomize_module.sys, "platform", "linux")

    called = False

    def fake_set(policy):
        nonlocal called
        called = True

    monkeypatch.setattr(
        sitecustomize_module.asyncio, "set_event_loop_policy", fake_set, raising=False
    )

    sitecustomize_module._apply_windows_selector_policy()

    assert called is False
