from __future__ import annotations


class SMTPAdapter:  # pragma: no cover - template
    def __init__(self, host: str, port: int = 587):
        self.host, self.port = host, port

    def send(self, to: str, subject: str, body: str) -> None:
        # TODO: implement real SMTP
        _ = (to, subject, body)
