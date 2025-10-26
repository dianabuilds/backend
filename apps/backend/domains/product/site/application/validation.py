from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft7Validator

from domains.product.content.schema import load_home_config_schema
from domains.product.site.domain import SiteValidationError


@dataclass(slots=True)
class ValidatedDraft:
    data: dict[str, Any]
    meta: dict[str, Any]


class PageDraftValidator:
    """Validate and normalize site page draft payloads."""

    def __init__(self) -> None:
        schema = load_home_config_schema()
        self._validator = Draft7Validator(schema)

    def validate(
        self,
        payload: Mapping[str, Any] | None,
        meta: Mapping[str, Any] | None,
    ) -> ValidatedDraft:
        normalized_data = self._normalize_payload(payload)
        normalized_meta = self._normalize_meta(meta)
        combined = dict(normalized_data)
        if normalized_meta:
            combined["meta"] = normalized_meta

        blocks = normalized_data.get("blocks", [])
        block_ids = self._extract_block_ids(blocks)
        duplicates = self._find_duplicate_ids(block_ids)

        general_errors: list[dict[str, Any]] = []
        block_errors: dict[str, list[dict[str, Any]]] = {}

        if duplicates:
            general_errors.append(
                {
                    "path": "/blocks",
                    "message": "Идентификаторы блоков должны быть уникальными",
                    "validator": "duplicate",
                }
            )
            for dup_id in duplicates:
                block_errors.setdefault(dup_id, []).append(
                    {
                        "path": "/id",
                        "message": "Идентификатор блока должен быть уникальным",
                        "validator": "duplicate",
                    }
                )

        for error in self._validator.iter_errors(combined):
            formatted = self._format_schema_error(error)
            scope = list(error.path)
            if scope and scope[0] == "blocks":
                index = scope[1] if len(scope) > 1 else None
                block_id = self._resolve_block_id(block_ids, index)
                field_path = (
                    "/" + "/".join(str(segment) for segment in scope[2:]) if len(scope) > 2 else "/"
                )
                scoped_error = dict(formatted)
                scoped_error["path"] = field_path
                if block_id:
                    block_errors.setdefault(block_id, []).append(scoped_error)
                else:
                    general_errors.append(scoped_error)
            else:
                general_errors.append(formatted)

        has_errors = general_errors or any(block_errors.values())
        if has_errors:
            raise SiteValidationError(
                "site_page_validation_failed",
                general=general_errors,
                blocks=block_errors,
            )

        return ValidatedDraft(data=normalized_data, meta=normalized_meta)

    @staticmethod
    def _normalize_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            return {"blocks": []}
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            if key == "meta":
                continue
            if key == "blocks":
                normalized["blocks"] = PageDraftValidator._normalize_blocks(value)
            else:
                normalized[key] = value
        normalized.setdefault("blocks", [])
        return normalized

    @staticmethod
    def _normalize_blocks(value: Any) -> list[Any]:
        if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)):
            return []
        blocks: list[Any] = []
        for item in value:
            if isinstance(item, Mapping):
                block = dict(item)
                if "data_source" in block and "dataSource" not in block:
                    block["dataSource"] = block.pop("data_source")
                data_source = block.get("dataSource")
                if isinstance(data_source, Mapping):
                    block["dataSource"] = PageDraftValidator._normalize_data_source(data_source)
                layout = block.get("layout")
                if isinstance(layout, Mapping):
                    block["layout"] = dict(layout)
                slots = block.get("slots")
                if isinstance(slots, Mapping):
                    block["slots"] = dict(slots)
                blocks.append(block)
            else:
                blocks.append(item)
        return blocks

    @staticmethod
    def _normalize_data_source(value: Mapping[str, Any]) -> dict[str, Any]:
        normalized = dict(value)
        items = normalized.get("items")
        if isinstance(items, Sequence) and not isinstance(items, (bytes, bytearray, str)):
            normalized["items"] = list(items)
        data_filter = normalized.get("filter")
        if isinstance(data_filter, Mapping):
            normalized["filter"] = dict(data_filter)
        return normalized

    @staticmethod
    def _normalize_meta(meta: Mapping[str, Any] | None) -> dict[str, Any]:
        if not isinstance(meta, Mapping):
            return {}
        return dict(meta)

    @staticmethod
    def _extract_block_ids(blocks: Sequence[Any]) -> list[str | None]:
        extracted: list[str | None] = []
        for block in blocks:
            block_id: str | None = None
            if isinstance(block, Mapping):
                candidate = block.get("id")
                if isinstance(candidate, str):
                    candidate = candidate.strip()
                    block_id = candidate or None
            extracted.append(block_id)
        return extracted

    @staticmethod
    def _find_duplicate_ids(block_ids: Sequence[str | None]) -> list[str]:
        counter = Counter(block_ids)
        duplicates = [
            block_id for block_id, count in counter.items() if block_id is not None and count > 1
        ]
        duplicates.sort()
        return duplicates

    @staticmethod
    def _resolve_block_id(block_ids: Sequence[str | None], index: Any) -> str | None:
        if isinstance(index, int):
            if 0 <= index < len(block_ids):
                return block_ids[index]
            return None
        try:
            parsed = int(str(index))
        except (TypeError, ValueError):
            return None
        if 0 <= parsed < len(block_ids):
            return block_ids[parsed]
        return None

    @staticmethod
    def _format_schema_error(error) -> dict[str, Any]:
        path = "/" + "/".join(str(segment) for segment in error.path) if error.path else "/"
        message = error.message
        validator = error.validator
        return {
            "path": path,
            "message": message,
            "validator": validator,
        }


__all__ = ["PageDraftValidator", "ValidatedDraft"]
