from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from domains.product.site.domain import BlockTopPage

_DEFAULT_METRIC_LOCALE = "ru"
_SUPPORTED_METRIC_PERIODS = {"1d", "7d", "30d"}
_MAX_METRIC_ROWS = 32
_TREND_POINTS = 14
_SLA_WARNING_LAG_MS = 30 * 60 * 1000  # 30 minutes
_VIEWS_DROP_THRESHOLD = -0.25
_CTR_DROP_THRESHOLD = -0.3


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return dict(value)


def normalize_numeric(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, Decimal):
        if value == value.to_integral():
            return int(value)
        return float(value)
    if isinstance(value, str):
        try:
            numeric = float(value)
        except ValueError:
            return None
        if numeric.is_integer():
            return int(numeric)
        return numeric
    return None


def calc_delta(current: float | int | None, previous: float | int | None) -> float | None:
    if current is None or previous is None:
        return None
    previous_value = cast(float | int, previous)
    current_value = cast(float | int, current)
    prev = previous_value + 0.0
    if prev == 0:
        return None
    current_numeric = current_value + 0.0
    return (current_numeric - prev) / prev


def compute_ratio(numerator: Any, denominator: Any) -> float | None:
    num = normalize_numeric(numerator)
    denom = normalize_numeric(denominator)
    if num is None or denom in (None, 0):
        return None
    denom_value = cast(float | int, denom)
    denom_float = denom_value + 0.0
    if denom_float == 0:
        return None
    num_value = cast(float | int, num)
    num_float = num_value + 0.0
    return num_float / denom_float


def format_delta_percentage(delta: float) -> str:
    return f"{abs(delta) * 100:.0f}%"


def extract_trend(rows: Sequence[Mapping[str, Any]], field: str) -> tuple[float, ...] | None:
    if not rows:
        return None
    series: list[float] = []
    for row in rows:
        value = normalize_numeric(row.get(field))
        if value is None:
            continue
        series.append(value + 0.0)
    return tuple(series) if series else None


def parse_top_pages(payload: Any) -> list[BlockTopPage]:
    if not payload:
        return []
    try:
        data = payload if isinstance(payload, list) else json.loads(payload)
    except (ValueError, TypeError):
        return []
    result: list[BlockTopPage] = []
    for item in data:
        if not isinstance(item, Mapping):
            continue
        page_identifier = item.get("page_id")
        if page_identifier is None:
            continue
        try:
            page_id = UUID(str(page_identifier))
        except (ValueError, TypeError):
            continue
        result.append(
            BlockTopPage(
                page_id=page_id,
                slug=str(item.get("slug", "")),
                title=str(item.get("title", "")),
                impressions=normalize_numeric(item.get("impressions")),
                clicks=normalize_numeric(item.get("clicks")),
                ctr=normalize_numeric(item.get("ctr")),
            )
        )
    return result


def as_list_of_mapping(value: Any) -> list[Mapping[str, Any]] | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, Sequence):
        return None
    items: list[Mapping[str, Any]] = []
    for entry in value:
        if isinstance(entry, Mapping):
            items.append(entry)
    return items if items else None


def row_value(row: Mapping[str, Any], key: str, default: Any = None) -> Any:
    return row.get(key, default)


def blocks_index(value: Any) -> dict[str, tuple[int, Mapping[str, Any]]]:
    if not isinstance(value, Sequence):
        return {}
    indexed: dict[str, tuple[int, Mapping[str, Any]]] = {}
    for position, candidate in enumerate(value):
        if not isinstance(candidate, Mapping):
            continue
        block_id = candidate.get("id")
        if isinstance(block_id, str) and block_id:
            indexed[block_id] = (position, candidate)
    return indexed


def compute_blocks_diff(previous: Any, current: Any) -> list[dict[str, Any]]:
    previous_index = blocks_index(previous)
    current_index = blocks_index(current)
    diff: list[dict[str, Any]] = []

    previous_ids = set(previous_index)
    current_ids = set(current_index)

    for block_id in sorted(current_ids - previous_ids):
        _, details = current_index[block_id]
        diff.append(
            {
                "type": "block",
                "blockId": block_id,
                "change": "added",
                "after": deepcopy(details),
            }
        )

    for block_id in sorted(previous_ids - current_ids):
        _, details = previous_index[block_id]
        diff.append(
            {
                "type": "block",
                "blockId": block_id,
                "change": "removed",
                "before": deepcopy(details),
            }
        )

    for block_id in sorted(previous_ids & current_ids):
        previous_pos, previous_block = previous_index[block_id]
        current_pos, current_block = current_index[block_id]
        if previous_pos != current_pos:
            diff.append(
                {
                    "type": "block",
                    "blockId": block_id,
                    "change": "moved",
                    "from": previous_pos,
                    "to": current_pos,
                }
            )
        if previous_block != current_block:
            diff.append(
                {
                    "type": "block",
                    "blockId": block_id,
                    "change": "updated",
                    "before": deepcopy(previous_block),
                    "after": deepcopy(current_block),
                }
            )

    return diff


def compute_mapping_diff(
    previous: Mapping[str, Any] | None,
    current: Mapping[str, Any] | None,
    *,
    scope: str,
) -> list[dict[str, Any]]:
    previous = previous or {}
    current = current or {}
    diff: list[dict[str, Any]] = []
    keys = set(previous) | set(current)
    for key in sorted(keys):
        previous_value = previous.get(key)
        current_value = current.get(key)
        if key not in previous:
            diff.append(
                {
                    "type": scope,
                    "field": key,
                    "change": "added",
                    "after": deepcopy(current_value),
                }
            )
        elif key not in current:
            diff.append(
                {
                    "type": scope,
                    "field": key,
                    "change": "removed",
                    "before": deepcopy(previous_value),
                }
            )
        elif previous_value != current_value:
            diff.append(
                {
                    "type": scope,
                    "field": key,
                    "change": "updated",
                    "before": deepcopy(previous_value),
                    "after": deepcopy(current_value),
                }
            )
    return diff


def compute_page_diff(
    previous_data: Mapping[str, Any] | None,
    previous_meta: Mapping[str, Any] | None,
    current_data: Mapping[str, Any] | None,
    current_meta: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    previous_data = as_mapping(previous_data)
    current_data = as_mapping(current_data)
    diff: list[dict[str, Any]] = []
    diff.extend(compute_blocks_diff(previous_data.get("blocks"), current_data.get("blocks")))

    filtered_previous_data = {k: v for k, v in previous_data.items() if k != "blocks"}
    filtered_current_data = {k: v for k, v in current_data.items() if k != "blocks"}
    diff.extend(
        compute_mapping_diff(
            filtered_previous_data,
            filtered_current_data,
            scope="data",
        )
    )
    diff.extend(compute_mapping_diff(previous_meta, current_meta, scope="meta"))
    return diff


def compute_global_block_diff(
    previous_data: Mapping[str, Any] | None,
    previous_meta: Mapping[str, Any] | None,
    current_data: Mapping[str, Any] | None,
    current_meta: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    diff: list[dict[str, Any]] = []
    diff.extend(
        compute_mapping_diff(as_mapping(previous_data), as_mapping(current_data), scope="data")
    )
    diff.extend(compute_mapping_diff(previous_meta, current_meta, scope="meta"))
    return diff


__all__ = [
    "_DEFAULT_METRIC_LOCALE",
    "_SUPPORTED_METRIC_PERIODS",
    "_MAX_METRIC_ROWS",
    "_TREND_POINTS",
    "_SLA_WARNING_LAG_MS",
    "_VIEWS_DROP_THRESHOLD",
    "_CTR_DROP_THRESHOLD",
    "utcnow",
    "as_mapping",
    "normalize_numeric",
    "calc_delta",
    "compute_ratio",
    "format_delta_percentage",
    "extract_trend",
    "parse_top_pages",
    "as_list_of_mapping",
    "row_value",
    "blocks_index",
    "compute_blocks_diff",
    "compute_mapping_diff",
    "compute_page_diff",
    "compute_global_block_diff",
]
