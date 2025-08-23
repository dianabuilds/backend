from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class ModelPrice:
    prompt_per_1k: float
    completion_per_1k: float


_DEFAULT_PRICES: Dict[str, ModelPrice] = {
    "gpt-4o-mini": ModelPrice(0.150, 0.600),
    "gpt-4o": ModelPrice(5.000, 15.000),
    "gpt-4.1-mini": ModelPrice(0.300, 1.200),
    "gpt-4.1": ModelPrice(5.000, 15.000),
    "claude-3-haiku-20240307": ModelPrice(0.250, 1.250),
    "claude-3-sonnet-20240229": ModelPrice(3.000, 15.000),
    "claude-3-opus-20240229": ModelPrice(15.000, 75.000),
}


def _load_override() -> Dict[str, ModelPrice]:
    raw = os.getenv("AI_PRICING_JSON")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        out: Dict[str, ModelPrice] = {}
        if isinstance(data, dict):
            for name, cfg in data.items():
                if not isinstance(cfg, dict):
                    continue
                p = float(cfg.get("prompt_per_1k", 0))
                c = float(cfg.get("completion_per_1k", 0))
                if p >= 0 and c >= 0:
                    out[str(name)] = ModelPrice(p, c)
        return out
    except Exception:
        return {}


_PRICES: Dict[str, ModelPrice] = {**_DEFAULT_PRICES, **_load_override()}


def describe_price(model: str) -> Tuple[float, float]:
    mp = _PRICES.get(model)
    if mp:
        return (mp.prompt_per_1k, mp.completion_per_1k)
    key = model.lower().strip()
    for name in _PRICES.keys():
        if key.startswith(name.lower()):
            mp = _PRICES[name]
            return (mp.prompt_per_1k, mp.completion_per_1k)
    return (0.0, 0.0)


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    p, c = describe_price(model)
    return (prompt_tokens / 1000.0) * p + (completion_tokens / 1000.0) * c
