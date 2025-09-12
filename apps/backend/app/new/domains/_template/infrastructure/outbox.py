
from typing import Dict, Optional

class OutboxSQL:
    def __init__(self, session_factory):
        self.sf = session_factory

    def publish(self, topic: str, payload: Dict, key: Optional[str] = None) -> None:
        # В проде: вставка в таблицу outbox в транзакции
        # Здесь: заглушка
        _ = (topic, payload, key)
        return
