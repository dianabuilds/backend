# ADR 0003: Settings Platform Consolidation

- Status: Proposed
- Date: 2025-09-22
- Authors: Platform Team
- Tags: settings, profile, billing, notifications, security, frontend, backend

## Context

Admin-панель и пользовательское веб-приложение используют разрозненные настройки: профиль ограничен сменой username, биллинг и уведомления опираются на моковые данные, а безопасность (сессии, mass logout) отсутствует в UI. Код админки планируется переносить в consumer-продукт почти без изменений, поэтому нужны единые API и UX-паттерны, которые покроют текущие MVP-требования: поля профиля (avatar, username, email, bio, role, wallet), поддержку EVM/SiWE, биллинг через существующий шлюз, пользовательские уведомления и управление сессиями.

## Decision

Создаём общую платформу настроек из четырёх разделов (Profile, Billing, Notifications, Security) с общим layout, API-контрактами и политиками, пригодными и для админки, и для публичного сайта. Расширяем существующие домены (`platform.users`, `product.profile`, `platform.billing`, `platform.notifications`, `platform.auth/iam`, `platform.media`) без введения новых таблиц, но с обязательными миграциями и аудитом.

### Scope & Goals

- **Profile / General**: аватар (через `/v1/media`), уникальный редактируемый `username` (rate limit), редактируемый `email` с подтверждением, `bio`, `role` (readonly, если не `user`), один EVM-кошелёк (SiWE).
- **Billing**: отображение активного плана/статуса и привязанного EVM-кошелька; подготовленные placeholders для карт и истории платежей до готовности контрактов.
- **Notifications**: чтение/запись пользовательских предпочтений по типам уведомлений и каналам (in-app готов, email за фичефлагом), интеграция с существующим диспетчером.
- **Security / Sessions**: список активных сессий (OS/браузер, IP, created/last_used), действия `terminate session`, `terminate others` (с подтверждением паролем), смена пароля и in-app уведомления о новых входах и изменениях настроек.

MVP можно расширять, переиспользуя установленные контракты (мульти-кошельки, 2FA, внешние интеграции и т.д.).

## Contracts & Protocols

- Все ответы `GET /v1/settings/*` и дубли `/me/*` возвращают `schema_version` в payload и заголовок `X-Settings-Schema: 1.0.0`. Клиенты логируют расхождения и graceful degrade.
- `PUT/POST` в `/v1/profile/*`, `/v1/notifications/preferences`, `/v1/security/*` используют ETag (`If-Match`) и idempotency ключ (`Idempotency-Key`). На конфликт возвращаем `409 Conflict` + `Retry-After`.
- Для consumer добавляем namespace `/me/*` (например, `/me/profile`, `/me/security/sessions`). Роуты проксируются на те же use-case, subject принудительно текущий пользователь.
- Ошибки выдаём как машинные коды (например, `E_USERNAME_TAKEN`, `E_EMAIL_PENDING`, `E_RATE_LIMITED`, `E_WEBAUTHN_NOT_SUPPORTED`) с user-friendly сообщением.

## Profile Requirements

- **Политика смены идентификаторов**: храним timestamps в таблице `profile_change_limits`. Лимит — одна смена username и одна смена email за 14 дней. При превышении возвращаем `429 Too Many Requests`, указываем время следующей попытки.
- **Аватар**: только presigned upload + серверная обработка (пережатие, strip EXIF, генерация миниатюр). Поддерживаем JPEG/PNG/WebP, запрещаем SVG. Ссылка хранится в `user_profiles.avatar_url` с таймстемпами `created_at`/`updated_at`.
- **Wallet (SiWE)**: сохраняем `chain_id`, `address`, `siwe_nonce`, `signature`, `verified_at`. Один активный кошелёк; оставляем уникальный индекс по `(user_id, chain_id, address)` для будущей многокошельковой поддержки.
- **Audit**: каждое изменение профиля логируется (до/после) и вызывает событие `profile.updated`.

## Security & Sessions

- **Связка refresh**: refresh-токены привязываются к `device_id` и отпечатку платформы. Ревокация конкретной сессии инвалидирует только соответствующую пару `device_id + refresh`. Массовый выход итерирует все активные пары.
- **Уведомления безопасности**: отправляем in-app (и email по фичефлагу) при новых входах, смене пароля, привязке/отвязке кошелька.
- **2FA hook**: резервируем эндпоинты `/v1/security/mfa/*` и флаги в профиле. Пока возвращают `501 Not Implemented`, но контракт фиксирован.
- **CSRF/Auth**: для cookie-сессий применяем существующий CSRF-механизм. Для bearer токенов требуем `SameSite=strict` и HTTPS.

## Notifications Requirements

- **Матрица предпочтений**: ключи вида `topic.channel -> opt_in|digest:<period>|quiet_hours`. В БД храним плоскую запись (`user_id`, `topic_key`, `channel`, `opt_in`, `digest`, `quiet_hours`).
- **Test ping**: `POST /v1/notifications/test` (dry run) для проверки доставки и quiet hours; UI показывает статус.
- **Feature flags**: `notifications.email`, `notifications.digest`, `security.session.alerts`. Флаги проходят от конфига до UI, отключение канала не ломает UX.
- **Security alerts**: используют `security.session.alerts` и связывание с audit.

## Billing Requirements

- **API**: `GET /v1/billing/summary` и `GET /v1/billing/history`. До готовности шлюза возвращаем `coming_soon` и пустую историю.
- **События**: генерируем `billing.plan_changed` и `billing.renewal_failed` для in-app уведомлений и аналитики.
- **EVM-only**: summary явно указывает, что пока поддерживаем только EVM (без карт).

## Data Model & Migrations

Большинство сущностей уже присутствует в платформенной схеме, поэтому миграции делаем инкрементально (ALTER вместо пересоздания):

- **user_profiles** (существует): используем поля `avatar_url`, `bio`. При необходимости добавляем `timezone`, `locale` (nullable) через `ALTER TABLE`.
- **users** (существует): сохраняем текущие lower-индексы на email, username, wallet_address. Для кошелька добавляем поля wallet_chain_id (text, nullable) и wallet_verified_at (timestamptz, nullable) вместо вынесения в отдельную таблицу.
- **profile_change_limits** (новая таблица):
  `sql
  create table profile_change_limits (
    user_id uuid primary key references users(id) on delete cascade,
    last_username_change_at timestamptz,
    last_email_change_at timestamptz,
    updated_at timestamptz not null default now()
  );
  `
- **notification_preferences** (новая таблица для матрицы предпочтений):
  `sql
  create table notification_preferences (
    user_id uuid references users(id) on delete cascade,
    topic_key text not null,
    channel text not null, -- 'inapp' | 'email' | 'push'
    opt_in boolean not null default true,
    digest text not null default 'none', -- 'none' | 'daily' | 'weekly'
    quiet_hours jsonb not null default '[]',
    updated_at timestamptz not null default now(),
    primary key (user_id, topic_key, channel)
  );
  create index if not exists ix_notification_preferences_topic on notification_preferences (topic_key, channel);
  `
- **user_sessions** (существует, migration 5d6c7e8f901): расширяем без дропов.
  `sql
  alter table user_sessions add column if not exists device_id uuid null;
  alter table user_sessions add column if not exists platform_fingerprint text null;
  alter table user_sessions add column if not exists terminated_by uuid null;
  alter table user_sessions add column if not exists terminated_reason text null;
  create index if not exists ix_user_sessions_device on user_sessions (user_id, device_id);
  `
  Переиспользуем текущие поля session_token_hash, efresh_token_hash, evoked_at; отдельный evoked boolean добавлять не нужно.
- **audit_logs** (существует, migrations 1b2c3d4e5f6 +  012): структура с esource_type, esource_id, efore, fter, extra, ip, user_agent, workspace_id. Новые требования покрываем ALTER TABLE ... ADD COLUMN IF NOT EXISTS.

Миграции оформляем через Alembic с проверками information_schema, чтобы повторный запуск был идемпотентным.

## Security & Privacy

- Маскируем email и адреса кошельков в логах и метриках.
- Токены подтверждения email живут 24 часа.
- Audit хранится 18 месяцев, записи о сессиях — 90 дней после revoke.
- Сырые ошибки провайдеров наружу не пробрасываем; маппим на error taxonomy.

## Observability & Alerts

- Метрики: `settings.write_rate`, `settings.error_rate`, `username_conflicts`, `email_resend_blocked`, `session_revokes`, `siwe_fail_rate`.
- Алерты: всплеск `5xx` по `/settings*`, доля `429` > 10% от базы, `siwe_fail_rate` > 5% p95, задержка доставки in-app > 10 секунд.
- Логи коррелируем по `request_id`, `user_id`, `session_id`.

## Implementation Plan

1. **Backend contracts**: реализовать эндпоинты `/v1/profile`, `/v1/security/sessions`, `/v1/notifications/preferences`, `/v1/billing/summary|history`, `/v1/notifications/test`, `/v1/security/mfa/*`. Добавить ETag/idempotency middleware и error taxonomy.
2. **Data layer**: применить миграции для таблиц выше, индексы и уникальные ограничения (wallet, preferences). Настроить audit событий.
3. **Frontend**: создать `SettingsLayout` (shared admin/consumer) и формы (`FieldText`, `FieldEmailVerified`, `AvatarUpload`, `ChannelMatrix`, `SessionTable`). Storybook кейсы: `loading`, `error`, `read-only`, `rate-limited`, `pending-verification`.
4. **Feature flags**: прокинуть `notifications.email`, `notifications.digest`, `billing.contracts`, `security.session.alerts` до UI.
5. **Notifications**: подключить security-пинги и `billing.*` события, dry-run endpoint.
6. **Observability**: настроить метрики/алерты, дашборд Grafana.
7. **Rollout**: dev -> staging -> internal -> GA. Массовое тестирование SiWE, rate limits, mass logout, email resend. Включение email-канала и advanced filters после валидации UX.

## Acceptance Criteria

- Один и тот же `SettingsLayout` используется в админке и consumer без форков компонентов.
- `PUT /v1/notifications/preferences` с `If-Match` обновляет только изменённые ключи и возвращает новый ETag.
- Массовый выход завершает все сессии, refresh-токены инвалидируются, пользователь получает in-app уведомление.
- Смена email ставит статус `pending_verification`, resend ограничен 10 попытками в сутки, после подтверждения отправляется security-уведомление.
- SiWE-привязка и отвязка логируются в audit и требуют подтверждения (подпись или пароль).
- Storybook покрывает состояния, перечисленные в Implementation Plan.

## Governance (RACI)

- **Domain owner**: Platform Team.
- **API contract**: Platform Backend.
- **UI & accessibility**: Frontend.
- **Email/channels**: Notifications Team.
- **Security review**: IAM/SRE.
- **Rollout & flags**: Platform + PM.
- **Audit/log policy**: SRE.
- **Data retention & compliance**: Data/Legal.

## Risks & Mitigations

- **Разъезд логики admin vs consumer**: единый пакет `settings-kit`, запрет на расхождения.
- **Недоступный email канал**: UI работает с отключённым флагом, показывает статус.
- **Коллизии username**: всегда использовать `user_id` как ключ, username только как алиас.
- **SiWE нестабилен**: метрики `siwe_fail_rate`, fallback уведомлений, чёткое логирование.

## Implementation Playbook (Night Agent)

1. Сгенерировать миграции (таблицы выше + индексы).
2. Поднять скелет эндпоинтов и middleware для ETag/idempotency.
3. Реализовать error taxonomy и маппинг.
4. Прописать фичефлаги и подключить к UI.
5. Добавить Storybook и контрактные тесты для профиля и предпочтений.
6. Настроить Grafana-дешборд.
7. Завести generic-компоненты форм и таблиц.

## Rollout & Compatibility

- Новые эндпоинты разворачиваются рядом со старыми, но обратная совместимость не требуется (этап активной разработки). Главное — стабильность функционала.
- Фичефлаги: `notifications.email`, `notifications.digest`, `billing.contracts`, `security.session.alerts`.
- Consumer-роуты `/me/*` подключаются одновременно с обновлением админ UI, чтобы избежать дрейфа.

## Resolved Questions

- **Advanced notification filters**: система доставки готова, фильтры можно включать сразу; необходимо определить полезные категории и UX.
- **Email resend policy**: ограничиваем подтверждение email десятью попытками в сутки, превышение трактуем как спам.





