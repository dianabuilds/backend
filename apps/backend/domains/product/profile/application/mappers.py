from __future__ import annotations

from domains.product.profile.domain.entities import Profile
from domains.product.profile.domain.results import ProfileView


def to_view(p: Profile) -> ProfileView:
    return ProfileView(id=p.id, username=p.username, bio=p.bio)
