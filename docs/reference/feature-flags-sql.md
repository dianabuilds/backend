# Фичфлаги в PostgreSQL: гайд по развёртыванию

Документ описывает целевую схему, процессы и проверки для перехода на хранение фичфлагов в PostgreSQL. Служит постоянным runbook'ом для разработки, поддержки и эксплуатации.

## Ключевые факты

- Основные слаги: `content.nodes`, `content.quests`, `notifications.broadcasts`, `billing.revenue`, `observability.core`, `moderation.guardrails`.
- Админское API возвращает поля `audience` (all/premium/testers/custom/disabled) и `effective` (итоговое состояние) для каждого флага.
- FastAPI использует уровень приложений: `domains.platform.flags.application.commands` — изменения, `domains.platform.flags.application.queries` — чтение; `application.presenter` отвечает только за DTO.
- Источник истины — PostgreSQL (`feature_flags`, `feature_flag_rules`, `feature_flag_audit`). Маршрут `/v1/settings/features` отдаёт развёрнутую карту для веб-клиента.

## Схема БД

- `feature_flags` (`slug PK`, `description`, `status`, `rollout`, `meta`, `created_at`, `updated_at`, `created_by`, `updated_by`)
- `feature_flag_rules` (`flag_slug FK`, `type`, `value`, `rollout`, `priority`, `meta`, `created_at`, `created_by`)
- `feature_flag_audit` — апенд-лог изменений
- Перечисления: `feature_flag_status` (`disabled`, `testers`, `premium`, `all`, `custom`) и `feature_flag_rule_type` (`user`, `segment`, `role`, `percentage`)

## Чек-лист миграции

1. **Применить миграцию** — Alembic-ревизия `0101_feature_flags_sql`.
2. **Импортировать существующие значения** — конвертировать дампы Redis (если были) в SQL (`flag.slug`, `status`, `rollout`, `rules`).
3. **Проверить конфигурацию** — `APP_DATABASE_URL` должен быть задан; Redis более не используется для флагов.
4. **Перезапустить сервисы/UI** — перезагрузить API Gateway и веб-приложение.
5. **Смоук-тест**  
   - `GET /v1/flags` возвращает структурированный ответ (статус, % раскатки, audience, testers, таймстемпы).  
   - `/v1/settings/features` отдаёт объекты с полями `enabled`, `effective`, `status`, `audience`, `meta`.  
   - Управляющий UI показывает колонки статуса/таргетинга и действия kill/enable.

## Семантика вычисления

- Правила обрабатываются по приоритету: `user` → `segment` → `role` → `percentage`.
- Процентные правила используют детерминированные SHA256-бакеты (`user_id` → 0..99).
- `status` выступает запасным планом:  
  - `disabled` — отключено всегда;  
  - `testers` — только явные правила;  
  - `premium` — требует подсказок о тарифе (`plan`, `roles`, `is_premium`);  
  - `all` — всем пользователям, опционально с глобальным процентом;  
  - `custom` — определяется только набором правил.

## Admin API и интерфейс

- `GET /v1/flags` — выдаёт таблицу для управления.
- `POST /v1/flags` — принимает `status`, `rollout`, списки `testers`, `roles`, `segments` или массив `rules[]`.
- `DELETE /v1/flags/{slug}` — удаляет флаг.
- `GET /v1/flags/check/{slug}` — утилита для проверки одного флага.

Страница `apps/web/src/pages/management/Flags.tsx` поддерживает:
- редактирование `status`, `rollout`, таргетингов;
- быстрые действия: отключить/включить 100%;
- просмотр метаданных (автор, дата, правила).

## Интеграция с настройками

Маршрут `/v1/settings/features` возвращает структуру:
`slug`, `status`, `status_label`, `audience`, `enabled`, `effective`, `rollout`, `testers`, `roles`, `segments`, `rules`, `meta`, `created_at`, `updated_at`, `evaluated_at`.

Провайдер настроек нормализует её в `SettingsFeatureState`, а хук `useSettingsFeature` остаётся источником булевых значений для клиентов.

## Runbook

1. Применить миграцию и перезапустить бэкенд.  
2. Засидировать обязательные флаги (kill-switch, каналы уведомлений и пр.).  
3. Проверить ответы `/v1/flags` и `/v1/settings/features`.  
4. Обновить документацию окружений, если выкатываем на новые среды.  
5. Сообщить админам о новых полях UI (аудитория, таргетинг).
