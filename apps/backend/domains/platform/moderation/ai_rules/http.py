from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException

from ..api.rbac import require_scopes
from ..application.ai_rules import create_rule as create_rule_use_case
from ..application.ai_rules import delete_rule as delete_rule_use_case
from ..application.ai_rules import get_rule as get_rule_use_case
from ..application.ai_rules import list_rules as list_rules_use_case
from ..application.ai_rules import rules_history as rules_history_use_case
from ..application.ai_rules import test_rule as test_rule_use_case
from ..application.ai_rules import update_rule as update_rule_use_case
from ..dtos import AIRuleDTO

router = APIRouter(prefix="/ai-rules", tags=["moderation-ai-rules"])


@router.get("", dependencies=[Depends(require_scopes("moderation:ai-rules:read"))])
async def list_rules(
    limit: int = 50, cursor: str | None = None, container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    return await list_rules_use_case(svc, limit=limit, cursor=cursor)


@router.post(
    "",
    response_model=AIRuleDTO,
    dependencies=[Depends(require_scopes("moderation:ai-rules:write"))],
)
async def create_rule(
    body: dict[str, Any], container=Depends(get_container)
) -> AIRuleDTO:
    svc = container.platform_moderation.service
    return await create_rule_use_case(svc, body)


@router.get(
    "/{rule_id}",
    response_model=AIRuleDTO,
    dependencies=[Depends(require_scopes("moderation:ai-rules:read"))],
)
async def get_rule(rule_id: str, container=Depends(get_container)) -> AIRuleDTO:
    svc = container.platform_moderation.service
    try:
        return await get_rule_use_case(svc, rule_id)
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
        return await update_rule_use_case(svc, rule_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="rule_not_found") from exc


@router.delete(
    "/{rule_id}",
    dependencies=[Depends(require_scopes("moderation:ai-rules:write"))],
)
async def delete_rule(rule_id: str, container=Depends(get_container)) -> dict[str, Any]:
    svc = container.platform_moderation.service
    deleted = await delete_rule_use_case(svc, rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="rule_not_found")
    return {"deleted": True, "id": rule_id}


@router.post(
    "/test",
    dependencies=[Depends(require_scopes("moderation:ai-rules:read"))],
)
async def test_rule(
    body: dict[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    return await test_rule_use_case(svc, body)


@router.get(
    "/history",
    dependencies=[Depends(require_scopes("moderation:ai-rules:read"))],
)
async def rules_history(
    limit: int = 100, cursor: str | None = None, container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    return await rules_history_use_case(svc, limit=limit, cursor=cursor)


__all__ = ["router"]
