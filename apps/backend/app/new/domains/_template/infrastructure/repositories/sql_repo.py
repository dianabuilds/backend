
from typing import Optional, Dict

# Заглушка: вместо реального ORM показываем сигнатуры
class SQLRepo:
    def __init__(self, session_factory):
        self.sf = session_factory

    def get(self, id: str) -> Optional[Dict]:
        # SELECT ... WHERE id = :id
        return {"id": id, "title": "sample", "visibility": "public"}

    def upsert(self, data: Dict) -> Dict:
        # INSERT ... ON CONFLICT UPDATE
        return data
