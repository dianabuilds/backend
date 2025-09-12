
from typing import Protocol, Optional, Dict
from .. import policies

class Repo(Protocol):
    def get(self, id: str) -> Optional[Dict]: ...
    def upsert(self, data: Dict) -> Dict: ...

class Outbox(Protocol):
    def publish(self, topic: str, payload: Dict, key: str | None = None) -> None: ...

class Service:
    def __init__(self, repo: Repo, outbox: Outbox):
        self.repo = repo
        self.outbox = outbox

    def get(self, id: str, subject: dict) -> dict:
        # ABAC через IAM-клиент должен жить в policies.check_read
        policies.check_read(subject=subject, resource_id=id)
        item = self.repo.get(id)
        if not item:
            raise KeyError("not_found")
        return item

    def update(self, data: Dict, subject: dict) -> Dict:
        policies.check_update(subject=subject, resource=data)
        stored = self.repo.upsert(data)
        # Публикуем событие из сервиса, не из HTTP-слоя
        self.outbox.publish("domain.sample.updated.v1", {"data": stored}, key=str(stored.get("id")))
        return stored
