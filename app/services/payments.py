from __future__ import annotations

import jwt
from app.core.config import settings


class PaymentService:
    """Simple payment verification service.

    In production this should verify payment tokens via an external
    payment gateway or blockchain smart contract.
    For now we expect a JWT token signed with the configured secret
    that contains the paid ``amount``.
    """

    def __init__(self, secret: str, algorithm: str) -> None:
        self._secret = secret
        self._algorithm = algorithm

    async def verify(self, token: str, amount: int) -> bool:
        """Verify the payment token matches the expected amount."""
        try:
            data = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError:
            return False
        return data.get("amount") == amount


payment_service = PaymentService(settings.jwt_secret, settings.jwt_algorithm)
