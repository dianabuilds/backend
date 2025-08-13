from fastapi import FastAPI

app = FastAPI()
# Лимит размера тела запросов
app.add_middleware(BodySizeLimitMiddleware)
# Базовые middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)
# CSRF для мутаций: выключаем в локальной разработке
env = getattr(settings, "environment", "development")
if env not in ("dev", "development", "local"):
    app.add_middleware(CSRFMiddleware)
# Заголовки безопасности и CSP
app.add_middleware(SecurityHeadersMiddleware)
# Усиление Set-Cookie флагов
app.add_middleware(CookiesSecurityMiddleware)
register_exception_handlers(app)
