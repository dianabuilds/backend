# Ticket Draft: INFRA-5 — Secrets & Infrastructure Configuration

## Summary
Задача: подготовить секреты и инфраструктурные настройки для развёртывания сегментации API (контуры `public`, `admin`, `ops`). Требуется настроить Vault/Parameter Store, передать значения в GitHub Secrets, обновить CI/deployment и зафиксировать изменения в документации.

## Definition of Ready
- ADR `docs/adr-api-segmentation.md` и `docs/api-inventory/pre-migration-actions.md#infra-5` согласованы.
- Перечень секретов подтверждён: `DATABASE_URL_ADMIN`, `DATABASE_URL_OPS`, `ADMIN_API_KEY`, `APP_OPS_API_KEY`, `APP_AUTH_JWT_SECRET`.
- Доступ к хранилищу (Vault/Parameter Store) и к репозиторию GitHub Actions имеется.
- Локальный шаблон `.env.local` (`apps/backend/.env.local`) создан, описан в playbook.

## Definition of Done
- Секреты заведены в Vault/Parameter Store с ограниченными правами и аудитом.
- GitHub Secrets обновлены (`gh secret set …`), CI и deployment конфигурации читают новые переменные.
- Локальные `.env` не содержат production-значений; обновлён playbook `docs/api-inventory/secret-playbook.md`.
- Smoke-тест `py -m pytest tests/app/api_gateway/test_contours.py` зелёный на новых ключах.
- Результаты занесены в `docs/api-inventory/findings.md`, тикет закрыт ссылками на PR/логи.

## Acceptance Criteria
1. Admin и Ops контуры используют разные DSN/учётки, проброшенные через `DATABASE_URL_ADMIN` и `DATABASE_URL_OPS`.
2. Заголовки `X-Admin-Key` и `X-Ops-Key` проверяются middleware; ключи хранятся отдельно от JWT-секрета.
3. GitHub Actions и deployment манифесты получают значения из секретов (без хардкода).
4. Vault экспортируется в локальный `.env.local` через `scripts/vault_export_env.py`; процедура описана в playbook.

## Steps
1. **Vault**  
   - Создать запись `secret/data/backend/infra-5` (или аналог) с ключами:  
     `DATABASE_URL_ADMIN`, `DATABASE_URL_OPS`, `ADMIN_API_KEY`, `APP_OPS_API_KEY`, `APP_AUTH_JWT_SECRET`.  
   - Выдать read-права только DevOps/CI.  
   - Проверка:  
     ```bash
     export VAULT_ADDR=https://vault.example.com
     export VAULT_TOKEN=<token>
     python scripts/vault_export_env.py secret/data/backend/infra-5 \
       --map DATABASE_URL_ADMIN=DATABASE_URL_ADMIN \
       --map DATABASE_URL_OPS=DATABASE_URL_OPS \
       --map ADMIN_API_KEY=ADMIN_API_KEY \
       --map APP_OPS_API_KEY=APP_OPS_API_KEY \
       --map APP_AUTH_JWT_SECRET=APP_AUTH_JWT_SECRET \
       --output apps/backend/.env.local
     ```
2. **GitHub Secrets**  
   ```powershell
   gh secret set DATABASE_URL_ADMIN --app actions --body "$env:DATABASE_URL_ADMIN"
   gh secret set DATABASE_URL_OPS   --app actions --body "$env:DATABASE_URL_OPS"
   gh secret set ADMIN_API_KEY      --app actions --body "$env:ADMIN_API_KEY"
   gh secret set APP_OPS_API_KEY    --app actions --body "$env:APP_OPS_API_KEY"
   gh secret set APP_AUTH_JWT_SECRET --app actions --body "$env:APP_AUTH_JWT_SECRET"
   ```
   - При необходимости продублировать для environments (`--env staging`, `--env prod`).
3. **CI / Deployment**  
   - Обновить `.github/workflows/ci.yml` и deployment шаблоны: убедиться, что переменные берутся из secrets.  
   - Проверить, что `apps/backend/app/api_gateway/wires.py` и смежные сервисы считывают новые env.
4. **Smoke & Документация**  
   - `py -m pytest tests/app/api_gateway/test_contours.py` (результат — в `docs/api-inventory/findings.md`).  
   - Обновить playbook (если есть замечания), приложить ссылку на этот тикет в `pre-migration-actions.md`.  
   - Закрыть задачу, приложив лог выполнения.
