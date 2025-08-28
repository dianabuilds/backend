import importlib
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure "app" package resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.schemas.node import NodeCreate, NodeUpdate  # noqa: E402


def test_node_create_forbid_quest_data() -> None:
    with pytest.raises(ValidationError) as exc:
        NodeCreate(title="n", content={}, quest_data={})
    assert "quest_data" in str(exc.value)


def test_node_update_forbid_quest_data() -> None:
    with pytest.raises(ValidationError) as exc:
        NodeUpdate(quest_data={})
    assert "quest_data" in str(exc.value)
