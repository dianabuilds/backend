from __future__ import annotations

import sys
import types
from pathlib import Path
from uuid import uuid4

# Ensure backend app package on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

module_name = "app.domains.nodes.application.editorjs_renderer"
sys.modules.setdefault(
    module_name,
    types.SimpleNamespace(
        collect_unknown_blocks=lambda _: [],
        render_html=lambda _: "",
    ),
)

from app.domains.nodes.content_admin_router import _serialize  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem  # noqa: E402
from app.schemas.nodes_common import Status, Visibility  # noqa: E402


def test_serialize_normalizes_content_and_meta() -> None:
    item = NodeItem(
        id=1,
        node_id=1,
        workspace_id=uuid4(),
        type="article",
        slug="n",
        title="N",
        status=Status.draft,
        visibility=Visibility.private,
    )
    node = Node(
        id=1,
        workspace_id=item.workspace_id,
        slug="n",
        title="N",
        author_id=uuid4(),
    )
    node.content = [{"type": "paragraph", "data": {"text": "hi"}}]

    payload = _serialize(item, node)

    assert isinstance(payload["content"], dict)
    assert payload["content"]["blocks"][0]["data"]["text"] == "hi"
    assert "content" not in payload["meta"]
