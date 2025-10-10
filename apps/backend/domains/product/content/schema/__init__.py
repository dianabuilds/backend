from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import resources
from typing import Any


def load_home_config_schema() -> Mapping[str, Any]:
    with resources.files(__package__).joinpath("home_config.schema.json").open(
        "r", encoding="utf-8-sig"
    ) as fp:
        return json.load(fp)


__all__ = ["load_home_config_schema"]
