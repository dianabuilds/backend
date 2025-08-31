import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.metrics import metrics_storage


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # Не считаем собственные метрики, чтобы не искажать картину
        metrics_path = settings.observability.metrics_path
        if (
            request.url.path.startswith("/admin/metrics")
            or request.url.path == metrics_path
        ):
            return await call_next(request)
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        # Извлекаем шаблон маршрута, если доступен
        route = request.scope.get("route")
        route_path = getattr(route, "path", None) or request.url.path
        method = request.method.upper()
        workspace_id = request.query_params.get("workspace_id")

        metrics_storage.record(
            duration_ms, response.status_code, method, route_path, workspace_id
        )
        return response
