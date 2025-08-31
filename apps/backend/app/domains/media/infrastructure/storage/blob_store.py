from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path


def _uploads_root() -> Path:
    root = os.getenv("UPLOADS_DIR", "uploads")
    p = Path(root).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _subdir(prefix: str) -> Path:
    today = datetime.utcnow().strftime("%Y%m%d")
    base = _uploads_root() / prefix / today
    base.mkdir(parents=True, exist_ok=True)
    return base


def put_text(prefix: str, data: str, *, filename_hint: str | None = None) -> str:
    """
    Сохраняет текст в локальное файловое хранилище uploads/<prefix>/<yyyymmdd>/<uuid>[-hint].txt
    Возвращает файловый путь (URL для отдачи зависит от того, как настроена раздача uploads).
    """
    safe_hint = ""
    if filename_hint:
        safe_hint = (
            "-"
            + "".join(c for c in filename_hint if c.isalnum() or c in ("_", "-"))[:40]
        )
    key = f"{uuid.uuid4().hex}{safe_hint}.txt"
    path = _subdir(prefix) / key
    path.write_text(data, encoding="utf-8")
    # Возвращаем относительный путь от корня проекта /uploads/...
    uploads_dir = _uploads_root()
    try:
        rel = path.relative_to(uploads_dir)
        return f"/uploads/{rel.as_posix()}"
    except Exception:
        # Фоллбэк — абсолютный путь
        return str(path)
