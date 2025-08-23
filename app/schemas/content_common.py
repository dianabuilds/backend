import warnings

from .nodes_common import Status, Visibility, Version

__all__ = ["Status", "Visibility", "Version"]

warnings.warn(
    "app.schemas.content_common is deprecated; use app.schemas.nodes_common instead",
    DeprecationWarning,
    stacklevel=2,
)
