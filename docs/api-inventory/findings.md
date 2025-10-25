# Findings & Quick Wins

## Риски
- **Публичные аналитические эндпоинты `/v1/content/*`** — без аутентификации отдают черновики, статистику и списки внутренних материалов (`docs/api-inventory/endpoints.md:143`). Потенциальная утечка данных и вектор для web‑скрейпинга; требуется перевод в админский контур или привязка к JWT/ролям.
- **AI генерация доступна анонимно** — `/v1/ai/generate` допускает вызов без обязательного пользователя (проверка `get_current_user` необязательная), достаточно CSRF‑куки (`docs/api-inventory/endpoints.md:99`). Высокие затраты и риск злоупотребления ботами; нужно требовать авторизацию и лимиты по аккаунту.
- **`/v1/auth/logout` без CSRF‑защиты** — POST запрос не использует `csrf_protect`, что позволяет третьей стороне разлогинить пользователя ссылкой (`docs/api-inventory/endpoints.md:108`). Требуется CSRF или перевод на безопасный метод.
- **OPS и admin маршруты на одном хосте** — `/v1/billing/*` и notifications-admin пока доступны внутри общей схемы (`docs/api-inventory/endpoints.md:134`). При отсутствии сетевого сегментирования компрометация публичного контура откроет доступ к финансовым операциям.

## Quick Wins
- Переключить `/v1/content/*` на `require_admin`/`require_role_db` и обновить фронт админки — 1 спринт, сразу сокращает риск утечки.
- Добавить `csrf_protect` к `/v1/auth/logout` и включить принудительный `get_current_user` для `/v1/ai/generate` — точечные правки без долгой миграции.
- Вынести `/v1/billing/admin/*` на отдельный subdomain/API gateway, даже до полной сегментации — настройка nginx/gateway + IAM, результатом станет явная граница OPS.

## Рекомендации
- Закрепить матрицу ролей по сводке (`docs/api-inventory/endpoints.md`) и скоррелировать с ADR `docs/adr-api-segmentation.md`.
- Сформировать дашборд покрытия: число admin/ops маршрутов, наличие `require_admin`/`csrf_protect`, нарушения выдавать алертом.
- Планировать миграцию: public API → `public.api.domain`, admin → `admin.api.domain`, ops → `ops.api.domain`, с отдельными ключами и rate-limit контурами.

## Проверки
- 2025-10-19: `python -m pytest tests/app/api_gateway/test_contours.py` c `APP_API_CONTOUR` = public/admin/ops — 5 тестов пройдены, предупреждения только о дубликатах Operation ID и устаревших конфигурациях Pydantic.
- 2025-10-20: `py -m pytest tests/app/api_gateway/test_contours.py` — проверены X-Admin-Key/X-Ops-Key; 7 тестов зелёные.
- 2025-10-20: Черновик DevOps тикета INFRA-5 сохранён в `docs/api-inventory/infra-5-devops-ticket.md`; подготовлен `.env.local` шаблон для разработки.
