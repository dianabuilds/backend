from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import (
    csrf_protect,
    get_current_user,
    require_admin,
)
from domains.product.moderation.api.http import make_router
from domains.product.moderation.application.interactors.cases import (
    ModerationCaseCreateCommand,
    ModerationCaseFilters,
    ModerationCaseNoteCommand,
    ModerationCaseUpdateCommand,
)


class StubModerationService:
    def __init__(self) -> None:
        self.cases: dict[str, dict[str, object]] = {}
        self.notes: dict[str, list[dict[str, object]]] = {}

    async def list(self, filters: ModerationCaseFilters) -> dict[str, object]:
        return {
            "items": list(self.cases.values()),
            "page": filters.page,
            "size": filters.size,
        }

    async def create(self, command: ModerationCaseCreateCommand) -> dict[str, object]:
        case_id = f"case-{len(self.cases) + 1}"
        case = {
            "id": case_id,
            "title": command.title,
            "description": command.description,
            "status": command.status,
            "queue": command.queue,
            "tags": list(command.tags),
        }
        self.cases[case_id] = case
        self.notes.setdefault(case_id, [])
        return {"id": case_id}

    async def add_note(
        self, command: ModerationCaseNoteCommand
    ) -> dict[str, object] | None:
        if command.case_id not in self.cases:
            return None
        note = {
            "id": f"note-{len(self.notes[command.case_id]) + 1}",
            "text": command.text,
            "pinned": bool(command.pinned),
        }
        self.notes[command.case_id].append(note)
        return note

    async def get(self, case_id: str) -> dict[str, object] | None:
        case = self.cases.get(case_id)
        if not case:
            return None
        return {**case, "notes": list(self.notes.get(case_id, []))}

    async def update(
        self, command: ModerationCaseUpdateCommand
    ) -> dict[str, object] | None:
        case = self.cases.get(command.case_id)
        if not case:
            return None
        if command.status is not None:
            case["status"] = command.status
        if command.queue is not None:
            case["queue"] = command.queue
        if command.tags is not None:
            case["tags"] = list(command.tags)
        return {**case, "notes": list(self.notes.get(command.case_id, []))}


def _build_client(service: StubModerationService, claims: dict[str, str]) -> TestClient:
    app = FastAPI()
    app.include_router(make_router())

    app.dependency_overrides[get_container] = lambda: SimpleNamespace(
        moderation_service=service
    )
    app.dependency_overrides[get_current_user] = lambda: claims

    async def _csrf_override():  # pragma: no cover - test helper
        return None

    app.dependency_overrides[csrf_protect] = _csrf_override
    app.dependency_overrides[require_admin] = _csrf_override

    return TestClient(app)


def _admin_claims() -> dict[str, str]:
    return {"sub": str(uuid4()), "role": "admin"}


def test_moderation_case_crud_flow() -> None:
    service = StubModerationService()
    claims = _admin_claims()
    client = _build_client(service, claims)

    create_response = client.post(
        "/v1/moderation/cases",
        json={
            "title": "integration-case",
            "description": "hot path",
            "type": "general",
            "status": "open",
            "tags": ["integration"],
        },
    )
    assert create_response.status_code == 200, create_response.text
    case_id = create_response.json()["id"]

    detail_response = client.get(f"/v1/moderation/cases/{case_id}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["id"] == case_id

    note_response = client.post(
        f"/v1/moderation/cases/{case_id}/notes",
        json={"text": "integration note", "pinned": True},
    )
    assert note_response.status_code == 200, note_response.text
    note = note_response.json()
    assert note["text"] == "integration note"
    assert note["pinned"] is True

    update_response = client.patch(
        f"/v1/moderation/cases/{case_id}",
        json={"status": "resolved", "queue": "integration"},
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["status"] == "resolved"
    assert updated["queue"] == "integration"


def test_moderation_update_missing_case_returns_404() -> None:
    service = StubModerationService()
    claims = _admin_claims()
    client = _build_client(service, claims)

    missing_id = "case-missing"
    response = client.patch(
        f"/v1/moderation/cases/{missing_id}",
        json={"status": "resolved"},
    )
    assert response.status_code == 404
