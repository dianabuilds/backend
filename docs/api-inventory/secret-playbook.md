# Secret Management Playbook (INFRA-5)

Документ описывает, как мы запрашиваем и поддерживаем секреты для сегментации API.

## 1. Список секретов

| Название | Назначение | Окружения | Ответственный |
|----------|------------|-----------|---------------|
| `DATABASE_URL_ADMIN` | Подключение Admin API к базе | dev, staging, prod | DevOps |
| `DATABASE_URL_OPS` | Подключение Ops API к базе | staging, prod | DevOps |
| `ADMIN_API_KEY` | Machine-to-machine доступ к Admin API | dev, staging, prod | Security / DevOps |
| `OPS_API_KEY` | Machine-to-machine доступ к Ops API | staging, prod | Security / DevOps |

Дополнительно при необходимости: `REDIS_URL_<CONTOUR>`, `FEATURE_FLAG_<CONTOUR>`.\n\n> Заголовки: Admin контур использует `X-Admin-Key`, Ops контур — `X-Ops-Key`. JWT секрет (`APP_AUTH_JWT_SECRET`) хранится отдельно и не совпадает с API-ключами.

## 2. Локальная разработка

- Допустима загрузка переменных из `apps/backend/.env` или `apps/backend/.env.local` — в файле содержатся только безопасные заглушки (без production-значений).
- Пример заглушек:

```env
DATABASE_URL_ADMIN=postgresql://postgres:postgres@localhost:5432/app_admin
DATABASE_URL_OPS=postgresql://postgres:postgres@localhost:5432/app_ops
ADMIN_API_KEY=dev-admin-key
APP_OPS_API_KEY=dev-ops-key
```

- Запуск через Makefile/Docker: `dotenv -f apps/backend/.env.local run make run-admin` либо подключение через `direnv` / `python-dotenv`.

## 3. Получение значений из Vault

### Требования
- Доступ к Vault (`VAULT_ADDR`, `VAULT_TOKEN`) с правами read на нужный KV-раздел.
- Установленный `requests` (`pip install requests`).

### Экспорт в `.env`

```powershell
setx VAULT_ADDR "https://vault.example.com"
setx VAULT_TOKEN "<vault-token>"
pip install requests
python scripts/vault_export_env.py secret/data/backend/infra-5 `
  --map DATABASE_URL_ADMIN=DATABASE_URL_ADMIN `
  --map DATABASE_URL_OPS=DATABASE_URL_OPS `
  --map ADMIN_API_KEY=ADMIN_API_KEY `
  --map OPS_API_KEY=OPS_API_KEY `
  --output apps/backend/.env.local
```

Аналог для bash:

```bash
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=<vault-token>
pip install requests
python scripts/vault_export_env.py secret/data/backend/infra-5 \
  --map DATABASE_URL_ADMIN=DATABASE_URL_ADMIN \
  --map DATABASE_URL_OPS=DATABASE_URL_OPS \
  --map ADMIN_API_KEY=ADMIN_API_KEY \
  --map OPS_API_KEY=OPS_API_KEY \
  --output apps/backend/.env.local
```

Если требуется просмотреть все ключи, можно вывести в stdout (`--output -`).

## 4. Запрос в DevOps

1. Составить тикет в DevOps с ссылкой на этот playbook и таблицу секретов (`pre-migration-actions.md#infra-5`) с указанием:
   - Названия секретов и окружений.
   - Требований к правам (кто может читать, кто может писать).
   - Формата значений (DSN, API key, TTL).
2. Приложить контактное лицо со стороны backend для ревью значений.
3. После ответа DevOps свериться, что новые секреты появятся в Vault/Parameter Store и будут синхронизированы в GitHub Secrets.

## 5. Занесение в GitHub Secrets

Используем GitHub CLI:

```powershell
gh secret set DATABASE_URL_ADMIN --app actions --body "<value>"
gh secret set OPS_API_KEY        --app actions --body "<value>"
```

Параметры:
- `--app actions` — секция GitHub Actions.
- Значения хранятся во Vault/1Password; чтение из GitHub Secrets невозможно, поэтому всегда держим оффлайн-копию в защищённом хранилище.

## 6. Обновление CI/deployment

1. В патчах CI (например, `.github/workflows/ci.yml`) убедиться, что переменные читаются из секретов и передаются в контейнеры (`env: DATABASE_URL_ADMIN: ${{ secrets.DATABASE_URL_ADMIN }}`).
2. Для deployment-скриптов обновить Helm/terraform/compose шаблоны: переменные подтягивать из секретов провайдера (Vault, Parameter Store).
3. После обновления провести smoke-тесты на staging.

## 7. Ведение журнала

- Любые изменения фиксируются в `docs/api-inventory/findings.md` (раздел «Обновления инфраструктуры»).
- В тикете DevOps держим ссылку на PR и результаты smoke-тестов.

## 8. Ротация ключей

- Раз в квартал инициируем ротацию API-ключей (Security).
- Процедура: DevOps создаёт новую пару ключей → обновляем GitHub Secrets → выполняем rolling-deploy → подтверждаем, что старые ключи отключены.
