# Changelog

## 2025-10-07

- API Gateway ��������� ������ �������� apps/backend/app/api_gateway, ��������� ������� � ������������.
- ���������� ������� ���������� �� �������/������� � typed presenters � ��������� `UseCaseResult` �������.
- ��������� ��������� stubs � ���������� ������������ mypy (������� ����� ��� notifications/moderation, ���������� ��� `slugify`).
- ��������� SQL/Redis �������� � ������� ������������ �����, ��������� unit � integration �����.
- ��������� ������������ (`apps/backend/ARCHITECTURE.md`, `docs/reference/feature-flags-sql.md`) � ��������� �������� ������ � �������� ���-������.

## 2025-10-28
- �������: ��������� ������� `billing.plan.changed.v1`, ��������� ����������� ������������� � support, ����� �������� � �������.

- ��������� ��������� � ���������������� �������-����� (`/v1/profile/**`, `/v1/admin/profile/**`), ���������� � ��������������� �������� FastAPI.
- ��������� �������������� ����� ������� (`tests/integration/test_profile_routes.py`) � �������� contour-�����.
- ��������� ������������ �� ������� (`docs/features/profile-settings/README.md`, `docs/README.md`), backlog ������� �����������.

