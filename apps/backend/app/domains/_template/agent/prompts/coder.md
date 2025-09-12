- Меняешь код только в `app/domains/{{domain}}/*` и обновляешь `schema/openapi.yaml` при изменении API.
- Любая правка схем тянет миграцию в корневой Alembic (описать дизайн в `schema/sql/`).
- Перед PR проходишь unit/contract/e2e тесты домена.
- Коммиты: `feat(domain-{{domain}}): <change>`.

