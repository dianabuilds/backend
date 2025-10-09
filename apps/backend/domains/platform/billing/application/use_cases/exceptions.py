from __future__ import annotations


class BillingUseCaseError(Exception):
    """Доменная ошибка use-case с привязкой к HTTP статусу."""

    def __init__(self, *, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


__all__ = ["BillingUseCaseError"]
