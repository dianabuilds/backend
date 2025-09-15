from __future__ import annotations

from .retry import with_retry
from .policies import rate_limited


@with_retry(attempts=3, backoff=0.2)
@rate_limited(key="<your_domain>", qps=50)
def dispatch(command: dict) -> dict:  # pragma: no cover - template
    # TODO: оркестрация вызовов адаптеров / проверок
    return {"result": "ok", "command": command}
