# Users vs Profile — границы и взаимодействие

## Роли доменов
- Users: идентичность и безопасность (аутентификация, роли, токены, ограничения, удаление аккаунта, кошельки).
- Profile: публичный профиль и self‑service настройки отображения (username/display name, avatar, bio, язык/локаль, ссылки, preferences) + профильные события.

## Данные и владение
- Таблица `users` (Users): источник правды по идентичности. Profile может читать/изменять строго ограниченные поля: `username`, `avatar_url`, `bio`.
- Таблица `user_profiles` (физически в Users): хранит `locale`, `timezone`, `links`, `preferences`. Логика изменения и публикации событий — в Profile.
- События: `profile.*` — в Profile (outbox), `auth.*` — в Users.

## API
- Profile: `/profile/{user_id}`, `PATCH /profile/{user_id}` (план: `/profile/me`, `/profile/me/settings`).
- Users: `/users/me`, `/users/me/profile`, `/users/me/settings` — исторические, проксируются и депрекейтуются по мере миграции клиентов.

## Политики доступа
- `profile.read` — публично.
- `profile.update` — владелец (subject.user_id == resource.user_id). Модератор/админ — по отдельным админ‑маршрутам (не покрыто текущей публичной схемой).

## Контракты и совместимость
- Профильный ответ `ProfileOut` намеренно узкий (id, userId, username, avatar, bio, lang). Расширения — ап‑совместимо.
- Старые users‑схемы (timezone/links/preferences) поддерживаются через endpoints users до миграции на /profile.

## Точки интеграции
- Репозиторий профиля (infrastructure) обращается к `users`/`user_profiles` напрямую — это допустимо как слой адаптации.
- Profile публикует `event.profile.updated.v1` при успешном изменении.

## Миграционный план (кратко)
1) Добавить `/profile/me`, `/profile/me/settings` (готово; домен `/profile/*` включается фича‑флагом `FF_PROFILE_ENABLED`).
2) Перевести `/users/me/profile` и `/users/me/settings` на сервис Profile (готово); выставить заголовки Deprecation/Sunset.
3) Клиентская миграция: обновить SDK/клиентов на новые маршруты `/profile/*`.
4) После окончания окна (Sunset) — удалить users-прокси.

### Таймлайн (пример)
- Annonce: T0 — объявить и включить Deprecation headers.
- Sunset: T0 + 90 дней — удалить users-прокси.

### Рекомендации клиентам
- Перейти с `/users/me/profile|settings` на `/profile/me|/profile/me/settings`.
- Для публичного профиля — использовать `/profile/{id}`.
