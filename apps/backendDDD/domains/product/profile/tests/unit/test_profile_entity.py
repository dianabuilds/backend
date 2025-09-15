from __future__ import annotations

import pytest
from domains.product.profile.domain.entities import Profile


def test_rename_valid():
    p = Profile(id="u1", username="old")
    p.rename("neo")
    assert p.username == "neo"


def test_rename_too_short():
    p = Profile(id="u1", username="old")
    with pytest.raises(ValueError):
        p.rename("x")
