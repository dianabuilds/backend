from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException

from ..dtos import AIRuleDTO
from ..rbac import require_scopes

router = APIRouter(prefix="/ai-rules", tags=["moderation-ai-rules"])


@router.get("", dependencies=[Depends(require_scopes("moderation:ai-rules:read"))])
async def list_rules(
    limit: int = 50, cursor: str | None = None, container=Depends(get_container)
) -> dict[str, Any]:
    # No persistent storage wired; show empty list instead of demo data
    return {"items": [], "next_cursor": None}


@router.post(
    "",
    response_model=AIRuleDTO,
    dependencies=[Depends(require_scopes("moderation:ai-rules:write"))],
)
async def create_rule(body: dict[str, Any], container=Depends(get_container)) -> AIRuleDTO:
    svc = container.platform_moderation.service
    return await svc.create_rule(body)


@router.get(
    "/{rule_id}",
    response_model=AIRuleDTO,
    dependencies=[Depends(require_scopes("moderation:ai-rules:read"))],
)
async def get_rule(rule_id: str, container=Depends(get_container)) -> AIRuleDTO:
    svc = container.platform_moderation.service
    try:
        return await svc.get_rule(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="rule_not_found") from exc


@router.patch(
    "/{rule_id}",
    response_model=AIRuleDTO,
    dependencies=[Depends(require_scopes("moderation:ai-rules:write"))],
)
async def update_rule(
    rule_id: str, body: dict[str, Any], container=Depends(get_container)
) -> AIRuleDTO:
    svc = container.platform_moderation.service
    try:
        return await svc.update_rule(rule_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="rule_not_found") from exc


@router.delete(
    "/{rule_id}",
    dependencies=[Depends(require_scopes("moderation:ai-rules:write"))],
)
async def delete_rule(rule_id: str, container=Depends(get_container)) -> dict[str, Any]:
    svc = container.platform_moderation.service
    deleted = await svc.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="rule_not_found")
    return {"deleted": True, "id": rule_id}


@router.post(
    "/test",
    dependencies=[Depends(require_scopes("moderation:ai-rules:read"))],
)
async def test_rule(body: dict[str, Any], container=Depends(get_container)) -> dict[str, Any]:
    svc = container.platform_moderation.service
    return await svc.test_rule(body)


@router.get(
    "/history",
    dependencies=[Depends(require_scopes("moderation:ai-rules:read"))],
)
async def rules_history(
    limit: int = 100, cursor: str | None = None, container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    return await svc.rules_history(limit=limit, cursor=cursor)


__all__ = ["router"]
