# Аудит админки (frontend + backend)

Дата: 2025-09-02
Объект аудита: приложения в apps/admin (React/TS) и связанные бэкенд-роуты в apps/backend (FastAPI/SQLAlchemy).

Суммарный вывод
- Критичных проблем в регистрации админских роутов на бэкенде не выявлено: ключевые эндпоинты публикации и расписания присутствуют и корректно импортируют зависимости.
- Ранее была обнаружена логическая ошибка в слое API публикаций (неверное использование wsApi — попытка деструктурировать { data } при том, что wsApi.get/post возвращают уже распакованные данные). Исправлено в рамках текущего коммита: api/publish.ts возвращает значения напрямую без деструктуризации.
- Реализация превью-симуляции на фронтенде соответствует бекенду (путь /admin/preview/transitions/simulate без workspace в URL), createPreviewLink также корректен.
- Риски XSS в компонентах предпросмотра сведены за счёт использования DOMPurify (sanitizeHtml) перед dangerouslySetInnerHTML.
- Сущеимых дублирований кода по URL-резолвингу нет — логика вынесена в utils/resolveUrl.ts и покрыта тестами.
- Прочие замечания по надёжности, безопасности и поддерживаемости приведены ниже.

1. Бэкенд (статус и замечания)
1.1. admin_nodes_router.py — эндпоинты публикации
Файл: apps/backend/app/domains/nodes/api/admin_nodes_router.py

Наблюдения:
- Эндпоинты
  - POST /admin/workspaces/{workspace_id}/nodes/{id}/publish
  - GET  /admin/workspaces/{workspace_id}/nodes/{id}/publish_info
  - POST /admin/workspaces/{workspace_id}/nodes/{id}/schedule_publish
  - DELETE /admin/workspaces/{workspace_id}/nodes/{id}/schedule_publish
  объявлены на верхнем уровне модуля, с корректными декораторами и зависимостями.
- Необходимые импорты присутствуют: BaseModel (pydantic), HTTPException (fastapi), NodePublishJob (models), _resolve_content_item_id (content_admin_router).

Серьёзность: —
Рекомендации:
- Добавить интеграционные тесты, проверяющие happy-path и ошибки (404 при отсутствии задания публикации, 403 при недостаточных правах и т.п.).

2. Согласованность API между фронтендом и бэкендом

3. Безопасность (кроме HTTPS)
3.1. XSS и dangerouslySetInnerHTML
- Компоненты AdminNodePreview.tsx и EditorJSViewer.tsx используют sanitizeHtml (DOMPurify) перед dangerouslySetInnerHTML, что снижает риск XSS.
Рекомендации:
- Сохранить практику санитизации, добавить Content-Security-Policy (CSP) на фронтенд-хостинге для ограничения inline‑скриптов.

3.2. Загрузка внешних ресурсов
- EditorJSEmbed.tsx и MediaPicker позволяют указывать внешние URL для картинок. Риск SSRF отсутствует (загрузка происходит в браузере), но возможны трекинг/микш контент, приватность.
Рекомендация: по возможности проксировать через медиасервис либо ограничивать список доменов.

3.3. Токены и куки
- client.ts корректно работает с CSRF и access token (cookie/SessionStorage). Убедиться, что сервер выставляет HttpOnly, SameSite, Secure в проде, и что домены/пути куки настроены корректно.

4. Логика и надёжность
4.1. NodeService.get и границы воркспейса
Файл: apps/backend/app/domains/nodes/application/node_service.py
- Метод допускает «мягкое» несоответствие workspace для админских сценариев. Это осознанное, но важное решение.
Рекомендация: при необходимости строгой изоляции — явные проверки и 404/403.

4.2. Publish scheduler — согласованность UI/BE
- Планировщик (publish_scheduler.py) согласован с админскими ручками. Ранее была проблема на стороне фронтенда (см. п.2.2), сейчас исправлено в api/publish.ts.

4.3. Превью‑токен
- client.ts отправляет X-Preview-Token, если он установлен (setPreviewToken). Для админской сессии не критично; для токен‑превью — обеспечить его установку при переходе по превью‑ссылке (если сценарий используется).

5. Неиспользуемый код / дублирование
5.1. URL‑резолвинг
- Общая утилита utils/resolveUrl.ts уже используется из EditorJSViewer/EditorJSEmbed и покрыта тестами (utils/resolveUrl.test.ts). Дублирования нет.

5.2. Алиасы del/delete
- В wsApi предусмотрены оба алиаса для DELETE. Рекомендация: выбрать один стиль в кодовой базе для единообразия.

6. Производительность и кэширование
- apiFetch содержит кэширование ETag для некоторых GET, таймауты и авто‑refresh 401 — реализация качественная. Следить, чтобы /auth/refresh оставался быстрым.

7. Рекомендации к тестам и качеству кода
- Интеграционные тесты на publish_info/schedule_publish/cancel_scheduled_publish, create_preview_link, simulate_transitions.
- Unit‑тесты для api/publish.ts (контракт wsApi) и api/preview.ts.
- Линтер/правила: запрет на несанитизированный dangerouslySetInnerHTML.

8. Приоритетный план действий
1) Проверить UX установки preview‑токена в сценариях превью-ссылок, при необходимости сохранить токен и отправлять его. [Средний]
2) Ввести/проверить CSP на фронтенд‑хостинге. [Высокий]
3) Выбрать единый стиль использования wsApi.delete/del. [Низкий]
4) Дополнить интеграционные/юнит‑тесты по списку выше. [Средний]

Приложение: Конкретные места в коде
- apps/backend/app/domains/nodes/api/admin_nodes_router.py — эндпоинты публикации и расписания (стр. 321–448) — корректная регистрация.
- apps/admin/src/api/preview.ts — simulatePreview и createPreviewLink используют /admin/preview/... без workspace в URL (корректно).
- apps/admin/src/api/publish.ts — исправлено: удалена некорректная деструктуризация { data } из wsApi, добавлены дженерики возвращаемых типов.
- apps/admin/src/features/content/components/AdminNodePreview.tsx — sanitizeHtml используется перед dangerouslySetInnerHTML.
- apps/admin/src/components/EditorJSViewer.tsx — sanitizeHtml используется для HTML блоков, resolveUrl — для картинок.

