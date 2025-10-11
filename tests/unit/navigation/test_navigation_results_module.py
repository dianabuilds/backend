from __future__ import annotations

from domains.product.navigation.domain import results


def test_results_module_re_exports():
    assert "TransitionDecision" in results.__all__
    assert results.TransitionCandidate.__name__ == "TransitionCandidate"
