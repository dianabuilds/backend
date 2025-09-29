"""Squashed base migration.

Revision ID: 0100_squashed_base
Revises: None
Create Date: 2025-09-29
"""

from __future__ import annotations

import pkgutil
from collections import defaultdict, deque
from collections.abc import Iterator
from importlib import import_module
from pathlib import Path

# Alembic identifiers
revision = "0100_squashed_base"
down_revision = None
branch_labels = None
depends_on = None

LEGACY_PACKAGE = "apps.backend.migrations.legacy"
LEGACY_PATH = Path(__file__).resolve().parent.parent / "legacy"


def _iter_legacy_modules() -> Iterator[object]:
    """Import legacy migration modules and yield them."""
    if not LEGACY_PATH.exists():  # pragma: no cover - defensive
        return iter(())
    for module_info in pkgutil.iter_modules([str(LEGACY_PATH)]):
        module = import_module(f"{LEGACY_PACKAGE}.{module_info.name}")
        if getattr(module, "upgrade", None) is None:
            continue
        if getattr(module, "revision", None) is None:
            continue
        yield module


def _topological_modules() -> list[object]:
    modules = list(_iter_legacy_modules())
    by_revision: dict[str, object] = {
        str(module.revision): module for module in modules if getattr(module, "revision", None)
    }
    indegree: dict[str, int] = defaultdict(int)
    adjacency: dict[str, list[str]] = defaultdict(list)

    for module in modules:
        rev = str(module.revision)
        down = getattr(module, "down_revision", None)
        if down is None:
            indegree.setdefault(rev, 0)
            continue
        if isinstance(down, (tuple, list, set)):
            downs = [str(item) for item in down if item]
        else:
            downs = [str(down)]
        if not downs:
            indegree.setdefault(rev, 0)
            continue
        for parent in downs:
            adjacency[parent].append(rev)
            indegree[rev] += 1
            indegree.setdefault(parent, 0)

    queue = deque(sorted(key for key, value in indegree.items() if value == 0))
    ordered: list[str] = []
    seen = set()
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        if current in by_revision:
            ordered.append(current)
        for child in sorted(adjacency.get(current, [])):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    # Append any modules that might not have been reached (defensive)
    for rev in sorted(by_revision):
        if rev not in ordered:
            ordered.append(rev)

    return [by_revision[rev] for rev in ordered]


def upgrade() -> None:
    """Run all legacy upgrades sequentially to build the schema."""
    for module in _topological_modules():
        module.upgrade()


def downgrade() -> None:  # pragma: no cover - destructive path intentionally disabled
    raise NotImplementedError("Downgrades are not supported for the squashed base migration.")
