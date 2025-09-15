from __future__ import annotations


class WebhookAdapter:  # pragma: no cover - template
    def __init__(self, base_url: str):
        self.base_url = base_url

    def post(self, path: str, json: dict) -> None:  # noqa: A002
        _ = (path, json)
