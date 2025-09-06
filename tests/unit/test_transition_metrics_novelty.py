from __future__ import annotations

from app.domains.telemetry.application.transition_metrics_service import TransitionMetrics


def test_novelty_prometheus() -> None:
    tm = TransitionMetrics()
    tm.observe_latency("ws", "m", 10)
    tm.observe_novelty_rate("ws", "m", 0.3)
    output = tm.prometheus()
    assert 'novelty_rate{workspace_id="ws",mode="m"} 0.3' in output
