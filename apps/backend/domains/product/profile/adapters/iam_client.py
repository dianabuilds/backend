from __future__ import annotations


class IamClient:
    def allow(
        self, subject: dict, action: str, resource: dict
    ) -> bool:  # pragma: no cover - demo
        return True
