# Profile API (product.profile)

Документ фиксирует фактическое поведение публичного и административного контуров профиля
после ввода FastAPI‑роутеров в `domains.product.profile.api`. Материал служит источником
правды для команд, интегрирующихся с `/v1/profile/**` и `/v1/admin/profile/**`.

## Обзор

| Контур | Базовый префикс | Описание |
|--------|-----------------|----------|
| public | `/v1/profile` | Самообслуживание для аутентифицированного пользователя; все операции выполняются от лица `sub` токена. |
| admin  | `/v1/admin/profile` | Административные операции над любым профилем; доступны только после прохождения `require_admin` (JWT с ролью `admin` или заголовок `X-Admin-Key`). |

Обе коллекции используют одну и ту же бизнес-логику (`commands.py`, `queries.py`, `Service`),
что гарантирует единое поведение и одинаковые ошибки.

## Поддерживаемые маршруты

### Public (`/v1/profile/*`)

| Метод и путь | Назначение | Требования |
|--------------|------------|------------|
| `GET /me` | Получить срез профиля текущего пользователя. | JWT + валидная сессия. |
| `PUT /me` | Обновить `username`, `bio`, `avatar_url` c оптимистичной блокировкой. | JWT, CSRF cookie/header, заголовок `If-Match` с прошлым `ETag`. |
| `POST /me/avatar` | Загрузить аватар. | JWT, CSRF; тело — multipart `file`. Ограничения: ≤ 5 МБ, `image/png|jpeg|webp`. |
| `POST /me/email/request-change` | Запросить смену email. | JWT, CSRF, заголовок `Idempotency-Key`. |
| `POST /me/email/confirm` | Подтвердить смену email по токену. | JWT, CSRF. |
| `POST /me/wallet` | Привязать кошелёк. | JWT, CSRF; payload с `address`, опционально `chain_id`, `signature` (обязательно, если включён флаг `Flags.require_wallet_signature`). |
| `DELETE /me/wallet` | Отвязать кошелёк. | JWT, CSRF. |

Ответы всех методов, возвращающих профиль, содержат поле `etag` в заголовках (`ETag`) и
всегда включают поля `wallet`, `limits` с информацией о cooldown.

### Admin (`/v1/admin/profile/*`)

| Метод и путь | Назначение | Требования |
|--------------|------------|------------|
| `GET /{user_id}` | Получить профиль любого пользователя. | `require_admin`. |
| `PUT /{user_id}` | Обновить поля профиля от имени администратора. | `require_admin`, CSRF, `If-Match`. |
| `PUT /{user_id}/username` | Легаси-обновление username от имени администратора/сотрудника поддержки. | `require_admin`, CSRF. |

Все административные операции форсируют `subject={"user_id": <target>, "role": "admin"}` в
командный слой, что обеспечивает корректную авторизацию и аудит.

## Специфика реализации

- **Контейнеры.** API Gateway получает два разных `APIRouter`: `profile_public_router`
  (только публичные ручки) и `profile_admin_router` (только админские). Контурная фильтрация
  (`_prune_routes`) гарантирует отсутствие `/v1/profile/*` в admin/ops и `/v1/admin/profile/*`
  в public/ops.
- **CSRF и аутентификация.** Все state-changing операции используют `csrf_protect`. JWT
  извлекается из cookie `access_token`, fallback на header `Authorization` отсутствует.
- **Idempotency.** Инициирование смены email (`request-change`) требует `Idempotency-Key`,
  что позволяет безопасно ретраить фронтенд-запросы.
- **ETag.** `profile_presenter.profile_etag` вычисляет strong ETag из сериализованного
  payload. Команды сравнивают входящий `If-Match` через `assert_if_match` и выбрасывают
  `ApiError` с кодами `E_ETAG_REQUIRED`/`E_ETAG_CONFLICT`.
- **Rate limits.** Ответы `/v1/me/settings/profile` и `/v1/settings/profile/{user_id}`
  включают `rate_limits`, отражающий только профильные ограничения:
  `username.can_change`, `username.next_change_at`, `email.can_change`, `email.next_change_at`.
- **Аудит.** Админские операции (`PUT /v1/settings/profile/{user_id}` и
  `/v1/admin/profile/**`) фиксируются в платформенном аудите: сохраняются `actor_id`
  (JWT `sub` или маркер `admin-key`), `resource_id` (целевой пользователь), изменённые
  поля и сетевой контекст (IP, User-Agent).
- **События.** Успешные мутации публикуют события (контракты описаны в JSON Schema):
  1. `profile.updated.v1` — `id`, `username`, опционально `bio`.
  2. `profile.email.change.requested.v1` — `id`, `new_email` (нормализованный e-mail).
  3. `profile.email.updated.v1` — `id`, `email` (подтверждённый e-mail).
  4. `profile.wallet.updated.v1` — `id`, `wallet_address`, опционально `wallet_chain_id` (может быть `null`).
  5. `profile.wallet.cleared.v1` — только `id`.
  Тесты `test_event_schema.py` валидируют payload против реестра схем.
- **Wallet подписи.** `Service.set_wallet` нормализует `address`, `chain_id`, очищает
  подпись и при активном флаге `Flags.require_wallet_signature` (вкл. через
  `APP_PROFILE_REQUIRE_WALLET_SIGNATURE=true`) требует валидную подпись (минимальная
  длина, возможность подключения внешнего верификатора). Нарушения транслируются в коды
  `E_WALLET_SIGNATURE_REQUIRED`/`E_WALLET_SIGNATURE_INVALID`.
- **Метрики.** `Service` меряет латентность вызовов `request_email_change`,
  `confirm_email_change`, `set_wallet`, `clear_wallet` и публикует гистограмму
  `profile_settings_operation_latency_seconds` с лейблом `operation`
  (`email_request`, `email_confirm`, `wallet_bind`, `wallet_unbind`).
- **Хранилище файлов.** Загрузка аватара использует фасад `StorageService`, который
  прокидывает файл в адаптер домена media. В интеграционных тестах подменяем gateway,
  чтобы убедиться, что файл сохраняется.

## Тестовое покрытие

- `tests/unit/product/profile/test_commands_queries.py` — unit-тесты сервисов и команд:
  валидация данных, ETag, привязка кошелька, запрос email.
- `tests/integration/test_profile_routes.py` — новые end-to-end тесты маршрутов public и
  admin, включая CSRF/Idempotency/If-Match, публикацию событий и работу storage.
- `tests/app/api_gateway/test_contours.py` — smoke-проверка, что public и admin контуры
  экспонируют корректные маршруты.

## Метрики и SLO

- `profile_settings_operation_latency_seconds{operation="email_request"}` — p95 ≤ 0.2 s.
- `profile_settings_operation_latency_seconds{operation="email_confirm"}` — p95 ≤ 0.2 s.
- `profile_settings_operation_latency_seconds{operation="wallet_bind"}` — p95 ≤ 0.2 s.
- `profile_settings_operation_latency_seconds{operation="wallet_unbind"}` — p95 ≤ 0.2 s.

## Требования по безопасности и ролям

- Публичные ручки доступны только для аутентифицированного пользователя, CSRF обязателен
  для POST/PUT/DELETE.
- Администраторские ручки требуют либо роль `admin` в JWT (audience `admin`), либо
  заголовок `X-Admin-Key` с валидным ключом из настроек.
- IAM вызов `service.update_profile(..., subject=...)` проверяет право `profile.update`.
  В проде необходимо настроить соответствующий Policy в `domains.platform.iam`.

## Планируемые улучшения

- Добавить JSON Schema для событий профиля (см. backlog).
