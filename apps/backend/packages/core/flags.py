from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Flags:
    enable_new_flow: bool = False
    require_wallet_signature: bool = False
