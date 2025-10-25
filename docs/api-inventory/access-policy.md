# Политика доступа и модель ролей

- **Статус:** Draft  
- **Дата:** 2025-10-19  
- **Связанные артефакты:** `docs/adr-api-segmentation.md`, `docs/api-inventory/endpoints.md`, `docs/api-inventory/findings.md`

Документ фиксирует единую модель доступа к backend сервисам, опираясь на аудит маршрутов (`docs/api-inventory/endpoints.md`) и план сегментации API. Цель — задать однозначные правила авторизации, требования к токенам и процесс ротации чувствительных секретов до начала рефакторинга контуров.

## 1. Роли и зоны ответственности

| Роль | Назначение | Основные источники данных/эндпоинты |
|------|------------|-------------------------------------|
| `anonymous` | Неаутентифицированные клиенты (витрина, лендинги) | Публичный контент, поиск, геро-блок (`docs/api-inventory/endpoints.md:240`, `docs/api-inventory/endpoints.md:247`) |
| `user` | Все авторизованные пользователи платформы | Профиль, личные узлы, комментарии, уведомления (`docs/api-inventory/endpoints.md:189`, `docs/api-inventory/endpoints.md:197`) |
| `editor` | Контент- и маркетинг-команда (редактирование публичных страниц) | Home admin, dev-blog preview (`docs/api-inventory/endpoints.md:30`, `docs/api-inventory/endpoints.md:188`) |
| `moderator` | Команда модерации/поддержки | `/api/moderation/*`, административные узлы (`docs/api-inventory/endpoints.md:3`, `docs/api-inventory/endpoints.md:36`) |
| `admin` | Core-платформа: управление пользователями, фичфлагами, системными настройками | Admin API, telemetry, flags (`docs/api-inventory/endpoints.md:25`, `docs/api-inventory/endpoints.md:167`) |
| `finance_ops` *(новая)* | Финансовые операции и биллинг | `/v1/billing/admin/*`, отчёты, провайдеры (`docs/api-inventory/endpoints.md:112`) |
| `service` | Сервис-аккаунты, воркеры, внешние webhooks | Billing webhooks, события, интеграции (`docs/api-inventory/endpoints.md:135`) |

> Роли `editor`, `moderator`, `admin` уже используются в коде (`apps/backend/domains/platform/moderation/api/rbac.py:20`, `apps/backend/domains/platform/users/application/service.py:10`). `finance_ops` и специализированные сервисные роли должны быть заведены в IAM и попадать в JWT как отдельный claim.

## 2. Матрица «роль × действие»

| Действие / Контур | anonymous | user | editor | moderator | admin | finance_ops | service |
|-------------------|-----------|------|--------|-----------|-------|-------------|---------|
| Публичный просмотр, поиск, лендинги | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ограничено |
| Регистрация, логин, refresh (`/v1/auth/*`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ограничено |
| Управление своим профилем, контентом, комментариями | — | ✓ | ✓ | ✓ | ✓ | ограничено | ограничено |
| Редактирование публичных страниц/геро-блоков | — | — | ✓ | ✓ | ✓ | ограничено | ограничено |
| Контент-аналитика и черновики (`/v1/content/*`, `dev-blog/preview`) | — | — | ✓ | ✓ | ✓ | — | — |
| Модерация пользователей, контента, жалоб | — | — | (read-only) | ✓ | ✓ | — | — |
| Администрирование уведомлений и шаблонов | — | — | — | — | ✓ | — | — |
| Управление пользователями, фичфлагами, системными настройками | — | — | — | — | ✓ | — | — |
| Финансовые операции: планы, провайдеры, отчёты | — | — | — | — | ✓¹ | ✓ | частично² |
| Доступ к аудитам, телеметрии, quota | — | — | — | — | ✓ | — | — |
| Webhook-и и интеграции сервисов | — | — | — | — | — | — | ✓ |

¹ На текущий момент все `/v1/billing/admin/*` маршруты требуют `admin` (`docs/api-inventory/endpoints.md:112`). Политика подразумевает создание роли `finance_ops` и делегирование к ней.  
² Сервисные интеграции (webhook-и) используют ограниченные ключи/подписи и не получают широких прав пользователя (`docs/api-inventory/endpoints.md:135`).

## 3. Спецификация токенов и скоупов

- **Формат JWT:** `HS256`, access/refresh пары с claim-ами `sub`, `typ`, `iat`, `exp`, `jti` (`apps/backend/domains/platform/iam/adapters/token_jwt.py:24`).  
- **TTL:** access — 15 минут, refresh — 7 дней (`apps/backend/packages/core/config.py:229`, `apps/backend/packages/core/config.py:230`).  
  - Требование: для `admin`, `moderator`, `finance_ops` сократить `auth_jwt_expires_min` до 10 минут и `auth_jwt_refresh_expires_days` до 1 дня на уровне audience `admin`/`ops`.  
  - Для public клиентов оставить 15/7, но принудительно проверять `aud` и `role` (см. ниже).
- **CSRF токен:** cookie + header, TTL унаследован от access (либо `auth_csrf_ttl_seconds`, `apps/backend/packages/core/config.py:233`). Все state-changing маршруты должны требовать `csrf_protect` (см. риск `/v1/auth/logout`, `docs/api-inventory/findings.md:6`).
- **Claims (обязательно):**
  - `role`: одна из ролей из матрицы (`apps/backend/domains/platform/iam/security.py:199`).
  - `scopes`: массив строк для тонкой проверки (`apps/backend/domains/platform/moderation/api/rbac.py:56`).
  - `aud`: `{public, admin, ops}` — определяет контур, куда может обращаться клиент.
  - `tenant` (опционально) — для будущих партнёрских площадок.
  - `session_id` — идентификатор сессии для отзыва.
- **Service Accounts:** используют OAuth2 Client Credentials / signed JWT без refresh (только `typ=service`, TTL ≤ 5 минут) и отдельный `aud=service`.

## 4. MFA и аутентификация

- Все субъекты с ролью `admin`, `moderator`, `finance_ops` обязаны проходить MFA (TOTP/WebAuthn).  
  - Требуемое изменение: реализовать хранение секретов и проверку MFA в IAM (`apps/backend/domains/platform/iam/README.md:11` отмечает TODO).  
- Вход без MFA допускается только для `anonymous`/`user`.  
- Необходим OPA/Policy-as-code контроль, блокирующий выдачу токена высокого уровня без `mfa_verified=true` claim.
- Ограничить вход по `admin_api_key` только для CI/автоматизации; для людей — только токены с MFA.

## 5. Ротация секретов и ключей

| Секрет/ключ | Где используется | Текущее состояние | Требование |
|-------------|------------------|-------------------|------------|
| `auth_jwt_secret` (`apps/backend/packages/core/config.py:229`) | Подпись JWT | Статический secret из env | Ротация ≤ 90 дней, использование rolling secret (kid в токене, JWKS). |
| `admin_api_key` (`apps/backend/packages/core/config.py:242`) | Байпас админ-доступа (`apps/backend/domains/platform/iam/security.py:206`) | Один ключ, без TTL | Ограничить до CI/automation, ротация ≤ 30 дней, хранение в секрет-менеджере, аудит использования. |
| Service credentials / webhooks | Billing webhooks (`docs/api-inventory/endpoints.md:135`) | Нет центрального реестра | Ввести каталог сервис-аккаунтов, ротация ≤ 60 дней, подпись запросов (HMAC). |
| Redis/DB учетные данные | Rate limiter, сессии | Общие учетные данные | Разделить по контурам (`public`, `admin`, `ops`) перед внедрением сегментации. |

Дополнительно — внедрить централизованный revoke-лист refresh-токенов (упомянуто TODO в IAM README) для немедленного отзыва в случае компрометации.

## 6. Процесс управления доступом

1. **Каталогизация прав:** по каждой роли вести YAML/JSON c разрешёнными маршрутами (см. агрегацию `var/routes_deps.json`).
2. **Профили клиентов:**  
   - `public` UI → audience `public`, роль `user`.  
   - `admin` UI → audience `admin`, роли `editor`/`moderator`/`admin`.  
   - `ops` UI → audience `ops`, роль `finance_ops`.
3. **Выдача прав:** Onboarding через тикет, обязательный approval безопасности, автоматическая запись в аудит.
4. **Отзыв:** при увольнении/инциденте — инвалидировать refresh, удалить MFA, заблокировать доступ в IdP.
5. **Контроль:**  
   - Автотесты на отказ по ролям (`docs/api-inventory/findings.md:12`).  
   - Алерты при попытке доступа с неподходящей `aud`/`role`.

## 7. Следующие шаги

1. Завести роль `finance_ops`, обновить IAM и биллинг-роуты (`docs/api-inventory/endpoints.md:112`).  
2. Покрыть `/v1/auth/logout` и `/v1/ai/generate` обязательной авторизацией и CSRF (см. риски).  
3. Настроить генерацию OpenAPI с актуальной матрицей ролей для публикации в внутренний портал.  
4. Обновить ADR `docs/adr-api-segmentation.md` ссылкой на данную политику и включить требования в roadmap сегментации.

