import pytest

from app.domains.nodes.service import validate_transition
from app.schemas.nodes_common import Status


def test_allowed_transitions():
    # These should not raise
    validate_transition(Status.draft, Status.in_review)
    validate_transition(Status.in_review, Status.published)


def test_forbidden_transitions():
    with pytest.raises(ValueError):
        validate_transition(Status.draft, Status.published)
    with pytest.raises(ValueError):
        validate_transition(Status.published, Status.draft)
