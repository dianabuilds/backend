from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence
from typing import (
    NotRequired,
    Protocol,
    Self,
    TypedDict,
    TypeVar,
    cast,
    runtime_checkable,
)

from pydantic import BaseModel

JSONValue = object
JSONMapping = Mapping[str, JSONValue]
Transform = Callable[[object], JSONValue]
HistoryStrategy = Callable[[JSONValue | None, JSONValue | None], JSONValue | None]

TInstance = TypeVar("TInstance", bound=object)
TItem = TypeVar("TItem")
TSource = TypeVar("TSource")
TResult = TypeVar("TResult", bound=JSONValue)


class FieldSpec(TypedDict):
    source: str
    transform: NotRequired[Transform]


def field(
    source: str, *, transform: Callable[[TSource], TResult] | None = None
) -> FieldSpec:
    spec: FieldSpec = {"source": source}
    if transform is not None:
        spec["transform"] = cast(Transform, transform)
    return spec


@runtime_checkable
class SupportsModelCopy(Protocol):
    def model_copy(self, *, update: Mapping[str, JSONValue]) -> Self: ...


def merge_metadata(
    base: Mapping[str, JSONValue] | None,
    updates: Mapping[str, JSONValue] | None,
) -> dict[str, JSONValue]:
    result: dict[str, JSONValue] = dict(base) if base is not None else {}
    if not updates:
        return result
    for key, value in updates.items():
        if value is not None:
            result[key] = value
    return result


def copy_model(instance: TInstance, update: Mapping[str, JSONValue]) -> TInstance:
    if not update:
        return instance
    if isinstance(instance, BaseModel):
        return cast(TInstance, instance.model_copy(update=dict(update)))
    if isinstance(instance, SupportsModelCopy):
        return cast(TInstance, instance.model_copy(update=dict(update)))
    if isinstance(instance, MutableMapping):
        new_instance = dict(instance)
        new_instance.update(update)
        return cast(TInstance, new_instance)
    if hasattr(instance, "__dict__"):
        clone = instance.__class__(**vars(instance))
        for key, value in update.items():
            setattr(clone, key, value)
        return cast(TInstance, clone)
    return instance


def merge_model(
    instance: TInstance,
    db_info: Mapping[str, JSONValue] | None,
    *,
    field_map: Mapping[str, FieldSpec] | None = None,
    meta_fields: Sequence[str] | None = None,
    history_key: str | None = None,
    history_strategy: HistoryStrategy | None = None,
) -> TInstance:
    if not db_info:
        return instance

    update: dict[str, JSONValue] = {}

    if field_map:
        for attr, spec in field_map.items():
            source_key = spec["source"]
            value = db_info.get(source_key)
            if value is None:
                continue
            transform = spec.get("transform")
            if transform is not None:
                value = transform(value)
            if value is not None:
                update[attr] = value

    if meta_fields:
        meta_updates = {
            key: db_info[key]
            for key in meta_fields
            if key in db_info and db_info[key] is not None
        }
        if meta_updates:
            current_meta = getattr(instance, "meta", None)
            update["meta"] = merge_metadata(
                cast(Mapping[str, JSONValue] | None, current_meta), meta_updates
            )

    if history_key and history_key in db_info:
        current_history = getattr(instance, history_key, None)
        db_history = db_info.get(history_key)
        if history_strategy is not None:
            update[history_key] = history_strategy(current_history, db_history)
        elif db_history is not None:
            update[history_key] = db_history

    return copy_model(instance, update)


def merge_history_prepend(
    existing: Iterable[TItem] | None,
    new_entry: Iterable[TItem] | TItem | None,
) -> list[TItem]:
    existing_list = list(existing) if existing is not None else []
    if new_entry is None:
        return existing_list
    if isinstance(new_entry, Iterable) and not isinstance(new_entry, (str, bytes)):
        return list(new_entry) + existing_list
    return [cast(TItem, new_entry)] + existing_list


def build_list_response(
    items: Sequence[TItem] | Iterable[TItem],
    *,
    next_cursor: str | None,
    extra: Mapping[str, JSONValue] | None = None,
) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {
        "items": list(items),
        "next_cursor": next_cursor,
    }
    if extra:
        payload.update(extra)
    return payload


__all__ = [
    "build_list_response",
    "copy_model",
    "field",
    "merge_history_prepend",
    "merge_metadata",
    "merge_model",
]
