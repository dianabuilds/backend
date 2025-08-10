"""SQLAlchemy models package.

This module exposes the declarative ``Base`` used by all models and ensures
that individual model modules are imported so that ``Base.metadata`` is aware
of them.  The ``Base`` class itself lives in ``app.db.base`` which provides a
custom declarative base with automatic ``__tablename__`` generation.
"""

from app.db.base import Base  # re-export Base from the DB layer

# Import models here to register them with SQLAlchemy's metadata
from .user import User  # noqa: F401
from .node import Node  # noqa: F401
from .moderation import ContentModeration, UserRestriction  # noqa: F401
from .transition import NodeTransition  # noqa: F401
from .echo_trace import EchoTrace  # noqa: F401
from .feedback import Feedback  # noqa: F401
from .notification import Notification  # noqa: F401
# Legacy event quests
from .event_quest import EventQuest, EventQuestCompletion  # noqa: F401

# User authored quests
from .quest import Quest, QuestPurchase, QuestProgress  # noqa: F401
from .tag import Tag, NodeTag  # noqa: F401
from .node_trace import NodeTrace  # noqa: F401
from .achievement import Achievement, UserAchievement  # noqa: F401
from .event_counter import UserEventCounter  # noqa: F401
from .user_token import UserToken, TokenAction  # noqa: F401

# Add future models' imports above

