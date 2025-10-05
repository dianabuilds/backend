from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from pydantic import BaseModel


def merge_metadata(
    base: dict[str, Any] | None, updates: dict[str, Any] | None
) -> dict[str, Any]:
    """Merge metadata dictionaries, skipping null values."""
    result: dict[str, Any] = dict(base or {})
    if not updates:
        return result
    for key, value in updates.items():
        if value is not None:
            result[key] = value
    return result


def copy_model(instance: Any, update: dict[str, Any]) -> Any:
    """Return a shallow copy of the instance with updated fields."""
    if not update:
        return instance
    if isinstance(instance, BaseModel):
        return instance.model_copy(update=update)
    copy_method = getattr(instance, "model_copy", None)
    if callable(copy_method):
        return copy_method(update=update)
    if isinstance(instance, dict):
        new_instance = dict(instance)
        new_instance.update(update)
        return new_instance
    # Fallback: rely on __dict__ cloning
    clone = instance.__class__(**vars(instance))
    for key, value in update.items():
        setattr(clone, key, value)
    return clone


def merge_model(
    instance: Any,
    db_info: dict[str, Any] | None,
    *,
    field_map: dict[str, str | tuple[str, Callable[[Any], Any]]] | None = None,
    meta_fields: tuple[str, ...] | None = None,
    history_key: str | None = None,
    history_strategy: Callable[[Any, Any], Any] | None = None,
) -> Any:
    """Merge DB payload into a pydantic model or dict using declarative options."""
    if not db_info:
        return instance

    update: dict[str, Any] = {}
    if field_map:
        for attr, source in field_map.items():
            transform: Callable[[Any], Any] | None = None
            source_key: str
            if isinstance(source, tuple):
                source_key, transform = source
            else:
                source_key = source
            value = db_info.get(source_key)
            if value is not None and transform is not None:
                value = transform(value)
            if value is not None:
                update[attr] = value
    if meta_fields:
        meta_updates = {
            key: db_info.get(key) for key in meta_fields if db_info.get(key) is not None
        }
        if meta_updates:
            current_meta = getattr(instance, "meta", None)
            update["meta"] = merge_metadata(current_meta, meta_updates)
    if history_key and history_key in db_info:
        current_history = getattr(instance, history_key, None)
        db_history = db_info.get(history_key)
        if history_strategy:
            update[history_key] = history_strategy(current_history, db_history)
        elif db_history is not None:
            update[history_key] = db_history
    return copy_model(instance, update)


def merge_history_prepend(existing: Any, new_entry: Any) -> list[Any]:
    """Prepend history entry or list of entries to an existing list."""
    if not new_entry:
        return list(existing or [])
    existing_list = list(existing or [])
    if isinstance(new_entry, list):
        return list(new_entry) + existing_list
    return [new_entry] + existing_list


def build_list_response(
    items: Sequence[Any] | Iterable[Any],
    *,
    next_cursor: str | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a consistent list response payload."""
    payload = {
        "items": list(items),
        "next_cursor": next_cursor,
    }
    if extra:
        payload.update(extra)
    return payload


__all__ = [
    "build_list_response",
    "copy_model",
    "merge_history_prepend",
    "merge_metadata",
    "merge_model",
]
