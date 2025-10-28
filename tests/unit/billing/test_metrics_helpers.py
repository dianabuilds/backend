from __future__ import annotations

import pytest

from apps.backend.domains.platform.billing import metrics


class DummyCounter:
    def __init__(self) -> None:
        self.labels_args: list[dict[str, str]] = []
        self.inc_calls: list[float] = []

    def labels(self, **kwargs):
        self.labels_args.append(kwargs)
        return self

    def inc(self, value: float = 1.0):
        self.inc_calls.append(float(value))
        return self


class DummyGauge(DummyCounter):
    def __init__(self) -> None:
        super().__init__()
        self.set_calls: list[float] = []

    def set(self, value: float):
        self.set_calls.append(float(value))
        return self


@pytest.fixture(autouse=True)
def restore_metrics(monkeypatch: pytest.MonkeyPatch):
    original_attrs = {
        name: getattr(metrics, name)
        for name in (
            "TRANSACTIONS_TOTAL",
            "TRANSACTION_VALUE_USD",
            "SUBSCRIPTIONS_ACTIVE",
            "SUBSCRIPTIONS_MRR",
            "SUBSCRIPTIONS_ARPU",
            "SUBSCRIPTIONS_CHURN",
            "SUBSCRIPTIONS_BY_TOKEN",
            "SUBSCRIPTIONS_TOKEN_MRR",
            "SUBSCRIPTIONS_BY_NETWORK",
            "NETWORK_VOLUME",
            "NETWORK_FAILED",
            "NETWORK_PENDING",
            "CONTRACT_INVENTORY",
            "CONTRACT_EVENTS_TOTAL",
        )
    }
    yield
    for name, value in original_attrs.items():
        setattr(metrics, name, value)


def test_observe_transaction_increments_counters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counter = DummyCounter()
    value_counter = DummyCounter()
    monkeypatch.setattr(metrics, "TRANSACTIONS_TOTAL", counter)
    monkeypatch.setattr(metrics, "TRANSACTION_VALUE_USD", value_counter)

    metrics.observe_transaction(
        "succeeded",
        network="polygon",
        token="USDC",
        source="webhook",
        amount_cents=12345,
    )

    assert counter.labels_args[0] == {
        "status": "succeeded",
        "network": "polygon",
        "token": "USDC",
        "source": "webhook",
    }
    assert value_counter.inc_calls[0] == pytest.approx(123.45)


def test_observe_transaction_handles_missing_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metrics, "TRANSACTIONS_TOTAL", None)
    monkeypatch.setattr(metrics, "TRANSACTION_VALUE_USD", None)

    metrics.observe_transaction(
        "succeeded",
        network=None,
        token=None,
        source="webhook",
        amount_cents=100,
    )  # should not raise


def test_set_subscription_metrics_updates_gauges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = DummyGauge()
    mrr = DummyGauge()
    arpu = DummyGauge()
    churn = DummyGauge()
    by_token = DummyGauge()
    token_mrr = DummyGauge()
    by_network = DummyGauge()

    monkeypatch.setattr(metrics, "SUBSCRIPTIONS_ACTIVE", active)
    monkeypatch.setattr(metrics, "SUBSCRIPTIONS_MRR", mrr)
    monkeypatch.setattr(metrics, "SUBSCRIPTIONS_ARPU", arpu)
    monkeypatch.setattr(metrics, "SUBSCRIPTIONS_CHURN", churn)
    monkeypatch.setattr(metrics, "SUBSCRIPTIONS_BY_TOKEN", by_token)
    monkeypatch.setattr(metrics, "SUBSCRIPTIONS_TOKEN_MRR", token_mrr)
    monkeypatch.setattr(metrics, "SUBSCRIPTIONS_BY_NETWORK", by_network)

    metrics.set_subscription_metrics(
        active=5,
        mrr=120.5,
        arpu=24.1,
        churn_ratio=0.05,
        per_token=[{"token": "USDC", "total": 3, "mrr_usd": 90.0}],
        per_network=[{"network": "polygon", "chain_id": "137", "total": 2}],
    )

    assert active.set_calls == [5.0]
    assert mrr.set_calls == [120.5]
    assert arpu.set_calls == [24.1]
    assert churn.set_calls == [0.05]
    assert by_token.labels_args[0] == {"token": "USDC"}
    assert by_token.set_calls == [3.0]
    assert token_mrr.set_calls == [90.0]
    assert by_network.labels_args[0] == {"network": "polygon", "chain_id": "137"}
    assert by_network.set_calls == [2.0]


def test_set_network_metrics_updates_gauges(monkeypatch: pytest.MonkeyPatch) -> None:
    volume = DummyGauge()
    failed = DummyGauge()
    pending = DummyGauge()
    monkeypatch.setattr(metrics, "NETWORK_VOLUME", volume)
    monkeypatch.setattr(metrics, "NETWORK_FAILED", failed)
    monkeypatch.setattr(metrics, "NETWORK_PENDING", pending)

    metrics.set_network_metrics(
        [
            {
                "network": "polygon",
                "token": "USDC",
                "volume": 10.5,
                "failed": 1,
                "pending": 2,
            }
        ]
    )

    assert volume.labels_args[0] == {"network": "polygon", "token": "USDC"}
    assert volume.set_calls == [10.5]
    assert failed.set_calls == [1.0]
    assert pending.set_calls == [2.0]


def test_set_contract_inventory_updates_gauge(monkeypatch: pytest.MonkeyPatch) -> None:
    gauge = DummyGauge()
    monkeypatch.setattr(metrics, "CONTRACT_INVENTORY", gauge)

    metrics.set_contract_inventory({"enabled": 3, "disabled": 1})

    assert {"label": "enabled"} in gauge.labels_args
    assert gauge.set_calls == [3.0, 1.0]


def test_observe_contract_event(monkeypatch: pytest.MonkeyPatch) -> None:
    counter = DummyCounter()
    monkeypatch.setattr(metrics, "CONTRACT_EVENTS_TOTAL", counter)

    metrics.observe_contract_event(
        event="PaymentReceived", status="succeeded", chain_id="137", method="mint"
    )

    assert counter.labels_args[0] == {
        "event": "PaymentReceived",
        "status": "succeeded",
        "chain_id": "137",
        "method": "mint",
    }
