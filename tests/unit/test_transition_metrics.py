from __future__ import annotations

from app.core import transition_metrics as tm


def setup_function() -> None:
    with tm._transition_lock:
        tm._route_lengths.clear()
        tm._tag_entropies.clear()
        tm._transition_counts.clear()
        tm._no_route_counts.clear()
        tm._fallback_used_counts.clear()
        tm._preview_route_lengths.clear()
        tm._preview_transition_counts.clear()
        tm._preview_no_route_counts.clear()


def test_transition_stats() -> None:
    tm.record_route_length(5, "ws1")
    tm.record_tag_entropy(1.0, "ws1")
    tm.record_no_route("ws1")
    tm.record_fallback_used("ws1")
    stats = tm.transition_stats()
    assert stats["ws1"]["route_length_avg"] == 5
    assert stats["ws1"]["route_length_p95"] == 5
    assert stats["ws1"]["tag_entropy_avg"] == 1.0
    assert stats["ws1"]["no_route_percent"] == 50.0
    assert stats["ws1"]["fallback_used_percent"] == 50.0


def test_preview_metrics() -> None:
    tm.record_route_length(3, "ws1", preview=True)
    tm.record_no_route("ws1", preview=True)
    with tm._transition_lock:
        assert tm._preview_route_lengths["ws1"][0] == 3
        assert tm._preview_transition_counts["ws1"] == 2
        assert tm._preview_no_route_counts["ws1"] == 1
