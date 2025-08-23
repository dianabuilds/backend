import pytest

from app.domains.nodes.service import validate_transition
from app.schemas.node_common import ContentStatus


def test_valid_transitions():
    validate_transition(ContentStatus.draft, ContentStatus.in_review)
    validate_transition(ContentStatus.in_review, ContentStatus.published)


def test_invalid_transition():
    with pytest.raises(ValueError):
        validate_transition(ContentStatus.draft, ContentStatus.published)
