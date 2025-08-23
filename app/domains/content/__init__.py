import warnings

from app.domains.nodes.dao import NodeItemDAO, NodePatchDAO
from app.domains.nodes.models import NodeItem, NodePatch

warnings.warn(
    "app.domains.content is deprecated, use app.domains.nodes instead",
    DeprecationWarning,
    stacklevel=2,
)

ContentItem = NodeItem
ContentPatch = NodePatch
ContentItemDAO = NodeItemDAO
ContentPatchDAO = NodePatchDAO

__all__ = [
    "ContentItem",
    "ContentPatch",
    "ContentItemDAO",
    "ContentPatchDAO",
]
