# Environment and cookies

## Формат переменных `APP_*`
- Все переменные приложения используют префикс `APP_` и оформлены в `SCREAMING_SNAKE_CASE`.
- Значения списков (`APP_CORS_ALLOW_ORIGINS`, `APP_CORS_ALLOW_METHODS`, `APP_CORS_ALLOW_HEADERS`) перечисляются через запятую без пробелов.
- `APP_ENV_MODE` задаёт режим работы: `development`, `staging`, `production` или `test`.
- Для `APP_CORS_ALLOW_ORIGINS` необходимо перечислять только явные origins, без `*`.
- Если нужно отключить CORS, оставьте `APP_CORS_ALLOW_ORIGINS` пустым.
- `APP_CORS_ALLOW_METHODS` и `APP_CORS_ALLOW_HEADERS` дополняют стандартные значения бэкенда.
  По умолчанию разрешены методы `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `PATCH`
  и заголовки `Authorization`, `Content-Type`, `X-CSRF-Token`, `X-CSRFToken`,
  `X-Requested-With`, `X-Workspace-Id`, `Workspace-Id`, `X-Feature-Flags`,
  `X-Preview-Token`, `X-Request-ID`, `X-BlockSketch-Workspace-Id`,
  `X-Client-Platform`, `X-XSRF-Token`, `X-Client-Language`, `X-Client-Version`,
  `X-User-Timezone`.

## Примеры `.env`

### Development
```env
APP_ENV_MODE=development
DEBUG=true
APP_CORS_ALLOW_ORIGINS=http://localhost:5173
COOKIE_DOMAIN=localhost
COOKIE_SECURE=False
COOKIE_SAMESITE=Lax
```

### Staging
```env
APP_ENV_MODE=staging
DEBUG=false
APP_CORS_ALLOW_ORIGINS=https://staging.example.com
COOKIE_DOMAIN=staging.example.com
COOKIE_SECURE=True
COOKIE_SAMESITE=Strict
```

### Production
```env
APP_ENV_MODE=production
DEBUG=false
APP_CORS_ALLOW_ORIGINS=https://example.com,https://app.example.com
COOKIE_DOMAIN=example.com
COOKIE_SECURE=True
COOKIE_SAMESITE=Strict
```

## Правила cookies
- `COOKIE_DOMAIN` должен быть установлен на домен приложения.
- В продакшене всегда используйте `COOKIE_SECURE=True` и `COOKIE_SAMESITE=Strict`.
- Cookies должны быть `HttpOnly` и иметь ограниченный срок жизни.
- CSRF-cookie задаётся через `CSRF_COOKIE_NAME` и должна быть включена в `CSRF_EXEMPT_PATHS` для служебных эндпоинтов.

## Диагностика
- `/health` — проверка живости сервиса.
- `/readyz` — готовность зависимостей (БД, очереди и пр.).
- `/metrics` — метрики Prometheus.
- Для расширенной диагностики используйте логи и интеграцию с Sentry (`SENTRY_DSN`).

## CORS на edge
- CORS управляется сервером через переменные `APP_CORS_*`.
- Edge‑прокси и CDN не должны добавлять `Access-Control-Allow-Origin: *`.
- Разрешены только явно указанные origins; для остальных CORS должен быть запрещён.
