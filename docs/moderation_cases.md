# Moderation Case System

This module tracks user requests and moderation issues as cases. Each case holds
metadata about the reporter, target object and discussion history.

## Roles
- **Reporter** – submits a case via public endpoint.
- **Moderator** – reviews, comments and resolves cases.
- **Admin** – can reassign, close or escalate cases and manage labels.

## SLA
| Priority | First response | Resolution |
|----------|----------------|-----------|
| P0       | 1 hour         | 4 hours   |
| P1       | 4 hours        | 1 day     |
| P2       | 1 day          | 3 days    |

The service exposes CRUD operations through `CasesService` and REST endpoints
under `/admin/moderation/cases`.
