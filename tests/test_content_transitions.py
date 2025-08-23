import pytest

from app.domains.nodes.service import validate_transition
from app.schemas.nodes_common import Status


def test_valid_transitions():
    validate_transition(Status.draft, Status.in_review)
    validate_transition(Status.in_review, Status.published)


def test_invalid_transition():
    with pytest.raises(ValueError):
        validate_transition(Status.draft, Status.published)
