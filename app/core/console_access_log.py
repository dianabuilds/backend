import json
import logging
import sys
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ConsoleAccessLogMiddleware(BaseHTTPMiddleware):
    """
    Пишет в консоль информацию о каждом HTTP-запросе:
    - метод, путь, статус, длительность
    - ограниченный превью тела запроса/ответа (для JSON)
    Заголовок Authorization маскируется.
    """

    def __init__(self, app, max_preview_bytes: int = 1000):
        super().__init__(app)
        self.log = logging.getLogger("app.access")
        # Гарантируем собственный поток в stdout и независимость от глобовой конфигурации
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        # Чтобы не плодить дубли при hot-reload, очищаем старые handler'ы того же типа
        for h in list(self.log.handlers):
            if isinstance(h, logging.StreamHandler):
                self.log.removeHandler(h)
        self.log.addHandler(handler)
        self.log.setLevel(logging.INFO)
        self.log.propagate = False  # не отправляем наверх — печатаем сами
        self.max_preview_bytes = max_preview_bytes

    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        req_preview = await self._safe_request_preview(request)
        try:
            response: Response = await call_next(request)
            dur_ms = (time.perf_counter() - started) * 1000.0
            resp_preview = await self._safe_response_preview(response)
            self.log.info(
                "HTTP %s %s -> %s (%.1f ms) req=%s resp=%s",
                request.method,
                request.url.path,
                response.status_code,
                dur_ms,
                req_preview,
                resp_preview,
            )
            return response
        except Exception as e:
            dur_ms = (time.perf_counter() - started) * 1000.0
            self.log.exception(
                "HTTP %s %s -> 500 (%.1f ms) req=%s error=%s",
                request.method,
                request.url.path,
                dur_ms,
                req_preview,
                repr(e),
            )
            raise

    async def _safe_request_preview(self, request: Request) -> str:
        ct = request.headers.get("content-type", "")
        headers = {
            k: ("***" if k.lower() == "authorization" else v)
            for k, v in request.headers.items()
            if k.lower() in ("content-type", "content-length", "authorization", "x-request-id")
        }
        body_preview: Optional[str] = None
        try:
            # Starlette кеширует request.body() — безопасно читать
            raw = await request.body()
            if raw and "application/json" in ct:
                body_preview = self._truncate_json(raw)
            elif raw:
                body_preview = self._truncate_bytes(raw)
        except Exception:
            body_preview = None
        return json.dumps({"h": headers, "b": body_preview}, ensure_ascii=False)

    async def _safe_response_preview(self, response: Response) -> str:
        try:
            ct = response.headers.get("content-type", "")
            body_preview: Optional[str] = None
            # Для JSONResponse есть .body — читаем только его, не трогаем поток
            raw = getattr(response, "body", None)
            if "application/json" in ct and isinstance(raw, (bytes, bytearray)):
                body_preview = self._truncate_json(raw)
            return json.dumps(
                {"h": {"content-type": ct}, "b": body_preview},
                ensure_ascii=False,
            )
        except Exception:
            return "{}"

    def _truncate_bytes(self, raw: bytes) -> str:
        if len(raw) > self.max_preview_bytes:
            return raw[: self.max_preview_bytes].decode("utf-8", errors="replace") + "...(truncated)"
        return raw.decode("utf-8", errors="replace")

    def _truncate_json(self, raw: bytes) -> str:
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
            text = json.dumps(data, ensure_ascii=False)
        except Exception:
            text = self._truncate_bytes(raw)
        if len(text) > self.max_preview_bytes:
            return text[: self.max_preview_bytes] + "...(truncated)"
        return text
