from __future__ import annotations

import logging
import random
from collections.abc import Iterable
from typing import Any

logger = logging.getLogger(__name__)


def _find_model(models: Iterable[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for m in models:
        if m.get("name") == name:
            return m
    return None


def resolve(bundle: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Resolve an AI model from ``bundle`` using ``context`` preferences.

    Parameters
    ----------
    bundle: dict
        Expected keys:
            ``mode`` (``sequential``, ``weighted`` or ``cheapest``) and
            ``models`` - list of model dictionaries. Each model may contain
            ``name``, ``weight``, ``cost`` and ``health`` fields.
    context: dict
        Optional hints where a model name may come from. Supported keys are
        ``explicit``, ``user``, ``workspace`` and ``global`` in order of
        priority.  If a model from context is healthy, it will be selected
        immediately.

    Returns
    -------
    dict
        The chosen model dictionary. If no healthy model is found an empty
        dictionary is returned.
    """

    models: list[dict[str, Any]] = list(bundle.get("models", []))
    mode = bundle.get("mode", "sequential")

    fallback_chain: list[str] = []
    source = "global"

    def healthy(m: dict[str, Any]) -> bool:
        return m.get("health", True)

    for src in ("explicit", "user", "workspace", "global"):
        name = context.get(src)
        if not name:
            continue
        fallback_chain.append(str(name))
        model = _find_model(models, name)
        if model and healthy(model):
            source = src
            logger.info(
                "Resolved model %s (source=%s, fallback=%s)",
                model.get("name"),
                source,
                "->".join(fallback_chain),
            )
            return model

    selected: dict[str, Any] | None = None

    if mode == "sequential":
        for m in models:
            fallback_chain.append(str(m.get("name")))
            if healthy(m):
                selected = m
                break
    elif mode == "weighted":
        healthy_models = [m for m in models if healthy(m)]
        if healthy_models:
            selected = random.choices(
                healthy_models,
                weights=[m.get("weight", 1) for m in healthy_models],
                k=1,
            )[0]
            fallback_chain.append(str(selected.get("name")))
    elif mode == "cheapest":
        healthy_models = [m for m in models if healthy(m)]
        if healthy_models:
            selected = min(
                healthy_models,
                key=lambda m: m.get("cost", float("inf")),
            )
            fallback_chain.append(str(selected.get("name")))

    if selected:
        logger.info(
            "Resolved model %s (source=%s, fallback=%s)",
            selected.get("name"),
            source,
            "->".join(fallback_chain),
        )
        return selected

    logger.warning("No healthy model resolved (fallback=%s)", "->".join(fallback_chain))
    return {}
