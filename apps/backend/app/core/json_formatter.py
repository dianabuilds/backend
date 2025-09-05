import json
import logging


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "service": getattr(record, "service", "backend"),
            "request_id": getattr(record, "request_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
            "workspace_id": getattr(record, "workspace_id", "-"),
            "msg": record.getMessage(),
        }
        if record.exc_info:
            exc_type = record.exc_info[0]
            if exc_type:
                base["exc_type"] = exc_type.__name__
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)
