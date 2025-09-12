
from domains.domain_product_template.application.services.service import Service

class RepoFake:
    def __init__(self): self.last = None
    def get(self, id): return {"id": id, "title": "x", "visibility": "public"}
    def upsert(self, data): self.last = data; return data

class OutboxFake:
    def __init__(self): self.events = []
    def publish(self, topic, payload, key=None): self.events.append((topic, key))

def test_update_publishes_event():
    svc = Service(RepoFake(), OutboxFake())
    res = svc.update({"id": "u1", "title": "t"}, subject={"user_id": "u1"})
    assert res["id"] == "u1"
