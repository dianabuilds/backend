from __future__ import annotations
from typing import Optional
from app.models.user import User


class NFTVerifier:
    """
    Абстракция поверх провайдера: сейчас — заглушка.
    В будущем сюда втыкаем реальную проверку по сети/контракту.
    """

    async def has_asset(self, user: Optional[User], requirement: Optional[str]) -> bool:
        if not requirement:        # нет требования — доступ открыт
            return True
        if not user or not user.wallet_address:
            return False
        # TODO: заменить на реальную проверку (chain, contract, token_id)
        # Временная логика: если requirement == "TEST", пускаем всех с любым wallet.
        return requirement == "TEST"


verifier = NFTVerifier()


async def user_has_nft(user: Optional[User], requirement: Optional[str]) -> bool:
    return await verifier.has_asset(user, requirement)
