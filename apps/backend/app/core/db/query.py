from __future__ import annotations

"""
Compatibility layer for query services.

Note: The long-term plan is to split this into domain-specific repositories.
For now, we re-export domain services and a compatible transition query module
to enable imports from core.db.query without relying on legacy service paths.
"""

from app.domains.nodes.application.node_query_service import (  # noqa: F401
    NodeQueryService,
)
from app.domains.nodes.application.query_models import (  # noqa: F401
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.core.db.transition_query import (  # noqa: F401
    TransitionQueryService,
    TransitionFilterSpec,
)

__all__ = [
    "NodeQueryService",
    "TransitionQueryService",
    "NodeFilterSpec",
    "TransitionFilterSpec",
    "PageRequest",
    "QueryContext",
]
