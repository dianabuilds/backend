from __future__ import annotations

from app.domains.accounts.limits import account_limit as workspace_limit
from app.domains.accounts.limits import consume_account_limit as consume_workspace_limit

__all__: list[str] = ["workspace_limit", "consume_workspace_limit"]
