
from fastapi import APIRouter, Depends, HTTPException
from ..application.services.service import Service
from ..infrastructure.repositories.sql_repo import SQLRepo
from ..infrastructure.outbox import OutboxSQL

router = APIRouter(prefix="/v1/sample", tags=["sample"])

def get_service() -> Service:
    # тут должны приезжать реальные зависимости (session_factory, iam-client и пр.)
    return Service(repo=SQLRepo(session_factory=None), outbox=OutboxSQL(session_factory=None))

@router.get("/{id}")
def get_item(id: str, svc: Service = Depends(get_service)):
    try:
        return svc.get(id=id, subject={"role": "user", "user_id": id})
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")

@router.put("/{id}")
def update_item(id: str, body: dict, svc: Service = Depends(get_service)):
    body = dict(body or {})
    body["id"] = id
    return svc.update(body, subject={"role": "user", "user_id": id})
