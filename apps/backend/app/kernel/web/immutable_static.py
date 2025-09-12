from __future__ import annotations

from fastapi.staticfiles import StaticFiles


class ImmutableStaticFiles(StaticFiles):
    """StaticFiles that sets long-lived immutable cache headers."""

    def __init__(self, *args, cache_control: str = "public, max-age=31536000, immutable", **kwargs):
        self.cache_control = cache_control
        super().__init__(*args, **kwargs)

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = self.cache_control
        return response


__all__ = ["ImmutableStaticFiles"]

