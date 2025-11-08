from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
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
_OWNER_ALIASES = {
    "Маркетинг": "team_marketing",
    "Продукт": "team_product",
    "Продакт": "team_product",
    "Продакт Quests": "team_quests_product",
    "Продакт Nodes": "team_nodes_product",
    "DevRel": "team_devrel",
    "Контент": "team_content",
    "Редакция контента": "team_content",
    "Саппорт": "team_support",
    "Аналитика": "team_analytics",
    "Data/ML": "team_data_ml",
    "team_public_site": "team_public_site",
}


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


def _normalize_owner_text(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return _OWNER_ALIASES.get(text, text)


def _normalize_owner_list(value: Any) -> list[str]:
    owners: list[str] = []
    if value is None:
        return owners
    items: Iterable[Any]
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = (value,)
    for item in items:
        normalized = _normalize_owner_text(item)
        if normalized and normalized not in owners:
            owners.append(normalized)
    return owners


def sanitize_block_meta(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    Normalize block meta:
    - ensure owners stored as list of slugs (supports legacy `owner` string);
    - normalize documentation key to `documentation_url`;
    - remove empty values while keeping other keys untouched.
    """
    mapping = as_mapping(meta)
    if not mapping:
        return {}
    sanitized: dict[str, Any] = {}
    owners: list[str] = []
    for key, value in mapping.items():
        if key == "owner":
            owners.extend(_normalize_owner_list(value))
            continue
        if key == "owners":
            owners.extend(_normalize_owner_list(value))
            continue
        if key == "documentation":
            if value is not None:
                sanitized["documentation_url"] = str(value)
            continue
        if key == "documentation_url":
            if value is not None:
                sanitized["documentation_url"] = str(value)
            continue
        sanitized[key] = value
    if owners:
        sanitized["owners"] = owners
    return sanitized


def as_locale_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        locales: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if not text:
                continue
            if text not in locales:
                locales.append(text)
        return tuple(locales)
    if isinstance(value, str):
        parts = [
            part.strip()
            for part in value.split(",")
            if isinstance(part, str) and part.strip()
        ]
        unique_locales: list[str] = []
        for part in parts:
            if part not in unique_locales:
                unique_locales.append(part)
        return tuple(unique_locales)
    return ()


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


def calc_delta(
    current: float | int | None, previous: float | int | None
) -> float | None:
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


def extract_trend(
    rows: Sequence[Mapping[str, Any]], field: str
) -> tuple[float, ...] | None:
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


def _coerce_block_key(candidate: Any, *, allow_id: bool = False) -> str | None:
    if isinstance(candidate, Mapping):
        for field in (
            "key",
            "block_key",
            "blockKey",
            "globalKey",
            "global_block_key",
            "globalBlockKey",
            "reference",
        ):
            value = candidate.get(field)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if allow_id:
            value = candidate.get("id")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
    if isinstance(candidate, str):
        cleaned = candidate.strip()
        return cleaned or None
    return None


def _iter_block_reference_candidates(
    value: Any,
    *,
    section_hint: str | None = None,
    allow_id: bool = False,
) -> list[tuple[str, str | None]]:
    refs: list[tuple[str, str | None]] = []
    if value is None:
        return refs
    if isinstance(value, Mapping):
        local_section = value.get("section")
        if isinstance(local_section, str) and local_section.strip():
            section_hint = local_section.strip()
        key = _coerce_block_key(value, allow_id=allow_id)
        if key:
            refs.append((key, section_hint))
        for item in value.values():
            refs.extend(
                _iter_block_reference_candidates(
                    item,
                    section_hint=section_hint,
                    allow_id=allow_id,
                )
            )
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            refs.extend(
                _iter_block_reference_candidates(
                    item, section_hint=section_hint, allow_id=allow_id
                )
            )
    else:
        key = _coerce_block_key(value, allow_id=allow_id)
        if key:
            refs.append((key, section_hint))
    return refs


def extract_shared_block_refs(
    data: Mapping[str, Any] | None,
    meta: Mapping[str, Any] | None,
) -> list[tuple[str, str | None]]:
    meta_map = as_mapping(meta)
    data_map = as_mapping(data)
    refs: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()

    def add_reference(key: str, section: str | None) -> None:
        normalized_key = key.strip()
        if not normalized_key:
            return
        normalized_section = None
        if section is not None:
            section_text = str(section).strip()
            if section_text:
                normalized_section = section_text
        pair = (normalized_key, normalized_section)
        if pair not in seen:
            seen.add(pair)
            refs.append(pair)

    for field in ("globalBlocks", "global_blocks"):
        for key, section in _iter_block_reference_candidates(meta_map.get(field)):
            add_reference(key, section)

    for fallback_key in ("header", "footer"):
        if fallback_key in meta_map:
            for key, section in _iter_block_reference_candidates(
                meta_map.get(fallback_key),
                section_hint=fallback_key,
            ):
                add_reference(key, section)

    blocks = data_map.get("blocks")
    if isinstance(blocks, Sequence):
        for block in blocks:
            if not isinstance(block, Mapping):
                continue
            block_type = str(block.get("type") or "").lower()
            source = str(block.get("source") or "").lower()
            allow_id = block_type in {"global", "global_block"} or source == "global"
            for key, section in _iter_block_reference_candidates(
                block,
                section_hint=block.get("section") or block.get("zone"),
                allow_id=allow_id,
            ):
                add_reference(key, section)

    shared = data_map.get("shared")
    if isinstance(shared, Mapping):
        assignments = None
        candidate = shared.get("assignments")
        if isinstance(candidate, Mapping):
            assignments = candidate
        else:
            legacy = shared.get("globalAssignments") or shared.get("global_assignments")
            if isinstance(legacy, Mapping):
                assignments = legacy
        if isinstance(assignments, Mapping):
            for section, value in assignments.items():
                resolved_key = _coerce_block_key(value)
                if resolved_key:
                    add_reference(
                        resolved_key, str(section) if section is not None else None
                    )

    return refs


def format_shared_block_refs(
    data: Mapping[str, Any] | None,
    meta: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for key, section in extract_shared_block_refs(data, meta):
        entry = {"key": key}
        if section:
            entry["section"] = section
        formatted.append(entry)
    return formatted


def _normalize_locale_code(value: Any, default_locale: str) -> str:
    text = str(value or "").strip()
    if not text:
        return default_locale
    return text


def _copy_locales_map(
    locales: Mapping[str, Mapping[str, Any]]
) -> dict[str, dict[str, Any]]:
    copied: dict[str, dict[str, Any]] = {}
    for locale, payload in locales.items():
        copied[locale] = dict(payload)
    return copied


def normalize_localized_document(
    document: Mapping[str, Any] | None,
    *,
    default_locale: str,
    allow_shared: bool = True,
) -> dict[str, Any]:
    base = as_mapping(document)
    normalized_default = default_locale.strip() or "ru"
    locales_section = base.get("locales")
    localized: dict[str, dict[str, Any]] = {}
    if isinstance(locales_section, Mapping):
        for locale_code, payload in locales_section.items():
            locale_key = _normalize_locale_code(locale_code, normalized_default)
            localized[locale_key] = as_mapping(payload)
    residual = {
        key: value for key, value in base.items() if key not in {"locales", "shared"}
    }
    if residual:
        current = localized.get(normalized_default, {})
        merged = dict(residual)
        merged.update(current)
        localized[normalized_default] = merged
    if not localized:
        localized[normalized_default] = {}
    shared_map: dict[str, Any] | None = None
    if allow_shared:
        shared_candidate = base.get("shared")
        if isinstance(shared_candidate, Mapping):
            shared_map = as_mapping(shared_candidate)
    result: dict[str, Any] = {"locales": _copy_locales_map(localized)}
    if shared_map:
        result["shared"] = dict(shared_map)
    return result


def project_localized_document(
    document: Mapping[str, Any] | None,
    *,
    default_locale: str,
    locale: str | None = None,
    allow_shared: bool = True,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], str, str | None]:
    canonical = normalize_localized_document(
        document,
        default_locale=default_locale,
        allow_shared=allow_shared,
    )
    locales_map = canonical.get("locales") or {}
    if not locales_map:
        locales_map = {default_locale: {}}
    normalized_default = default_locale.strip() or "ru"
    requested = (locale or "").strip()
    active_locale = (
        requested
        if requested and requested in locales_map
        else (
            normalized_default
            if normalized_default in locales_map
            else next(iter(locales_map))
        )
    )
    fallback_locale = (
        active_locale if requested and active_locale != requested else None
    )
    selected = dict(locales_map.get(active_locale, {}))
    if allow_shared:
        shared_map = canonical.get("shared")
        if isinstance(shared_map, Mapping) and shared_map:
            selected.setdefault("shared", dict(shared_map))
    return selected, _copy_locales_map(locales_map), active_locale, fallback_locale


def compute_page_diff(
    previous_data: Mapping[str, Any] | None,
    previous_meta: Mapping[str, Any] | None,
    current_data: Mapping[str, Any] | None,
    current_meta: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    previous_data = as_mapping(previous_data)
    current_data = as_mapping(current_data)
    diff: list[dict[str, Any]] = []
    diff.extend(
        compute_blocks_diff(previous_data.get("blocks"), current_data.get("blocks"))
    )

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
        compute_mapping_diff(
            as_mapping(previous_data), as_mapping(current_data), scope="data"
        )
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
    "extract_shared_block_refs",
    "format_shared_block_refs",
    "normalize_localized_document",
    "project_localized_document",
    "sanitize_block_meta",
    "as_locale_list",
]
