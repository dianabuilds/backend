from __future__ import annotations

import jwt

from app.kernel.config import settings


class PaymentService:
    """JWT-based payment verification service (simple in-app gateway).

    In production this should verify payment tokens via an external
    payment gateway or blockchain smart contract. For now we expect a
    JWT token signed with the configured secret that contains the paid ``amount``.
    """

    def __init__(self, secret: str | None = None, algorithm: str | None = None) -> None:
        self._secret = secret or (settings.payment.jwt_secret or "")
        self._algorithm = algorithm or settings.jwt.algorithm

    async def verify(self, token: str, amount: int) -> bool:
        """Verify the payment token matches the expected amount."""
        try:
            data = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError:
            return False
        return data.get("amount") == amount


payment_service = PaymentService()

__all__ = ["PaymentService", "payment_service"]
