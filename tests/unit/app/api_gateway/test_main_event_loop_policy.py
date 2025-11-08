from __future__ import annotations

from apps.backend.app.api_gateway import main


def test_windows_selector_policy_applied(monkeypatch):
    applied: dict[str, object] = {}

    class DummyPolicy:
        pass

    def fake_factory() -> DummyPolicy:
        applied["factory"] = True
        return DummyPolicy()

    def fake_set(policy: object) -> None:
        applied["policy"] = policy

    monkeypatch.setattr(main.sys, "platform", "win32")
    monkeypatch.setattr(
        main.asyncio, "WindowsSelectorEventLoopPolicy", fake_factory, raising=False
    )
    monkeypatch.setattr(main.asyncio, "set_event_loop_policy", fake_set)

    main._ensure_windows_selector_policy()

    assert applied.get("factory") is True
    assert isinstance(applied.get("policy"), DummyPolicy)


def test_selector_policy_not_applied_off_windows(monkeypatch):
    called = False

    def fake_set(policy: object) -> None:  # pragma: no cover - defensive
        nonlocal called
        called = True

    monkeypatch.setattr(main.sys, "platform", "linux")
    monkeypatch.setattr(main.asyncio, "set_event_loop_policy", fake_set, raising=False)

    main._ensure_windows_selector_policy()

    assert called is False
