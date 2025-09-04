from __future__ import annotations

from app.core.transition_metrics import (
    _fallback_used_counts,
    _no_route_counts,
    _preview_no_route_counts,
    _preview_route_lengths,
    _preview_transition_counts,
    _repeat_rates,
    _route_latencies,
    _route_lengths,
    _tag_entropies,
    _transition_counts,
    _transition_lock,
)


def reset_transition_metrics() -> None:
    with _transition_lock:
        _route_latencies.clear()
        _repeat_rates.clear()
        _route_lengths.clear()
        _tag_entropies.clear()
        _transition_counts.clear()
        _no_route_counts.clear()
        _fallback_used_counts.clear()
        _preview_route_lengths.clear()
        _preview_transition_counts.clear()
        _preview_no_route_counts.clear()
