from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def forbid_quest_data(data: Mapping[str, Any] | Any) -> Mapping[str, Any] | Any:
    """Reject payloads containing the deprecated ``quest_data`` field.

    This helper can be used in ``model_validator`` hooks to ensure that the
    ``quest_data`` field is not accepted by input schemas. The field used to
    store quest graph data directly inside node payloads but is now read-only
    and managed via dedicated quest APIs.
    """
    if isinstance(data, Mapping) and "quest_data" in data:
        raise ValueError("quest_data field is read-only; use quest graph APIs")
    return data


__all__ = ["forbid_quest_data"]
