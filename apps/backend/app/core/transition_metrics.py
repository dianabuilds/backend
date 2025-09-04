# ruff: noqa: E501
from __future__ import annotations

import math
import threading
from collections import defaultdict, deque

_transition_lock = threading.Lock()
_route_latencies: deque[int] = deque(maxlen=1000)
_repeat_rates: deque[float] = deque(maxlen=1000)
_route_lengths: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=1000))
_tag_entropies: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=1000))
_transition_counts: dict[str, int] = defaultdict(int)
_no_route_counts: dict[str, int] = defaultdict(int)
_fallback_used_counts: dict[str, int] = defaultdict(int)
_preview_route_lengths: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=1000))
_preview_transition_counts: dict[str, int] = defaultdict(int)
_preview_no_route_counts: dict[str, int] = defaultdict(int)


def record_route_latency_ms(value: float) -> None:
    with _transition_lock:
        _route_latencies.append(int(value))


def record_repeat_rate(rate: float) -> None:
    with _transition_lock:
        _repeat_rates.append(rate)


def record_route_length(
    length: int, workspace_id: str | None, preview: bool = False
) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        if preview:
            _preview_route_lengths[ws].append(length)
            _preview_transition_counts[ws] += 1
        else:
            _route_lengths[ws].append(length)
            _transition_counts[ws] += 1


def record_tag_entropy(entropy: float, workspace_id: str | None) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        _tag_entropies[ws].append(entropy)


def record_no_route(workspace_id: str | None, preview: bool = False) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        if preview:
            _preview_no_route_counts[ws] += 1
            _preview_transition_counts[ws] += 1
        else:
            _no_route_counts[ws] += 1
            _transition_counts[ws] += 1


def record_fallback_used(workspace_id: str | None) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        _fallback_used_counts[ws] += 1


def _percentile(values: list[int], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = max(int(math.ceil(p * len(values_sorted))) - 1, 0)
    return float(values_sorted[k])


def prometheus() -> str:
    with _transition_lock:
        lat = list(_route_latencies)
        rates = list(_repeat_rates)
        lengths: dict[str, list[int]] = {
            ws: list(v) for ws, v in _route_lengths.items()
        }
        entropies = {ws: list(v) for ws, v in _tag_entropies.items()}
        totals = dict(_transition_counts)
        no_routes = dict(_no_route_counts)
        fallbacks = dict(_fallback_used_counts)
        prev_lengths: dict[str, list[int]] = {
            ws: list(v) for ws, v in _preview_route_lengths.items()
        }
        prev_totals = dict(_preview_transition_counts)
        prev_no_routes = dict(_preview_no_route_counts)
    lines: list[str] = []
    lines.append("# HELP route_latency_ms Route latency milliseconds")
    lines.append("# TYPE route_latency_ms summary")
    if lat:
        avg = sum(lat) / len(lat)
        p95 = _percentile(lat, 0.95)
        lines.append(f"route_latency_ms_avg {avg}")
        lines.append(f"route_latency_ms_p95 {p95}")
    else:
        lines.append("route_latency_ms_avg 0")
        lines.append("route_latency_ms_p95 0")
    lines.append("# HELP repeat_rate Repeat rate of filtered candidates")
    lines.append("# TYPE repeat_rate gauge")
    if rates:
        lines.append(f"repeat_rate {sum(rates) / len(rates)}")
    else:
        lines.append("repeat_rate 0")
    lines.append(
        "# HELP transition_no_route_percent Percentage of transitions without route"
    )
    lines.append("# TYPE transition_no_route_percent gauge")
    for ws, cnt in no_routes.items():
        total = totals.get(ws, 0)
        pct = (cnt / total * 100) if total else 0.0
        lines.append(f'transition_no_route_percent{{workspace="{ws}"}} {pct}')
    lines.append(
        "# HELP transition_preview_no_route_percent Percentage of preview transitions without route",
    )
    lines.append("# TYPE transition_preview_no_route_percent gauge")
    for ws, cnt in prev_no_routes.items():
        total = prev_totals.get(ws, 0)
        pct = (cnt / total * 100) if total else 0.0
        lines.append(f'transition_preview_no_route_percent{{workspace="{ws}"}} {pct}')
    lines.append(
        "# HELP transition_fallback_used_percent Percentage of transitions using fallback",
    )
    lines.append("# TYPE transition_fallback_used_percent gauge")
    for ws, cnt in fallbacks.items():
        total = totals.get(ws, 0)
        pct = (cnt / total * 100) if total else 0.0
        lines.append(f'transition_fallback_used_percent{{workspace="{ws}"}} {pct}')
    lines.append("# HELP tag_entropy_avg Average tag entropy per workspace")
    lines.append("# TYPE tag_entropy_avg gauge")
    for ws, vals in entropies.items():
        avg = sum(vals) / len(vals) if vals else 0.0
        lines.append(f'tag_entropy_avg{{workspace="{ws}"}} {avg}')
    lines.append("# HELP route_length Route length")
    lines.append("# TYPE route_length summary")
    for ws, lens in lengths.items():
        avg = sum(lens) / len(lens) if lens else 0.0
        p95 = _percentile(lens, 0.95) if lens else 0.0
        lines.append(f'route_length_avg{{workspace="{ws}"}} {avg}')
        lines.append(f'route_length_p95{{workspace="{ws}"}} {p95}')
    lines.append("# HELP preview_route_length Route length in preview")
    lines.append("# TYPE preview_route_length summary")
    for ws, lens in prev_lengths.items():
        avg = sum(lens) / len(lens) if lens else 0.0
        p95 = _percentile(lens, 0.95) if lens else 0.0
        lines.append(f'preview_route_length_avg{{workspace="{ws}"}} {avg}')
        lines.append(f'preview_route_length_p95{{workspace="{ws}"}} {p95}')
    return "\n".join(lines) + "\n"


def transition_stats() -> dict[str, dict]:
    with _transition_lock:
        out: dict[str, dict] = {}
        for ws in _transition_counts.keys():
            lengths = list(_route_lengths.get(ws, []))
            ents = list(_tag_entropies.get(ws, []))
            total = _transition_counts.get(ws, 0)
            no_r = _no_route_counts.get(ws, 0)
            fb = _fallback_used_counts.get(ws, 0)
            out[ws] = {
                "route_length_avg": sum(lengths) / len(lengths) if lengths else 0.0,
                "route_length_p95": _percentile(lengths, 0.95) if lengths else 0.0,
                "tag_entropy_avg": sum(ents) / len(ents) if ents else 0.0,
                "no_route_percent": (no_r / total * 100) if total else 0.0,
                "fallback_used_percent": (fb / total * 100) if total else 0.0,
            }
        return out
