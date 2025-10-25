#!/usr/bin/env python3
"""
Utility to export secrets from HashiCorp Vault into a .env-style file.

Example:
    VAULT_ADDR=https://vault.local
    VAULT_TOKEN=...
    python scripts/vault_export_env.py secret/data/backend/infra-5 \
        --map DATABASE_URL_ADMIN=DATABASE_URL_ADMIN \
        --map ADMIN_API_KEY=ADMIN_API_KEY \
        --output apps/backend/.env.local
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List

try:
    import requests  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - we just hint the fix
    sys.stderr.write(
        "requests package is required. Install it via 'pip install requests'.\n"
    )
    raise


def parse_map(entry: str) -> Dict[str, str]:
    if "=" not in entry:
        raise argparse.ArgumentTypeError(
            f"mapping '{entry}' must be in form VAULT_KEY=ENV_NAME"
        )
    vault_key, env_name = entry.split("=", 1)
    if not vault_key or not env_name:
        raise argparse.ArgumentTypeError(
            f"mapping '{entry}' must include non-empty VAULT_KEY and ENV_NAME"
        )
    return {vault_key: env_name}


def load_secret(vault_addr: str, token: str, path: str) -> Dict[str, str]:
    url = vault_addr.rstrip("/") + "/v1/" + path.lstrip("/")
    headers = {"X-Vault-Token": token}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(
            f"Vault request failed ({response.status_code}): {response.text}"
        )
    payload = response.json()
    # KV v2 stores data under data.data; fall back to data for v1.
    if isinstance(payload, dict) and "data" in payload:
        inner = payload["data"]
        if isinstance(inner, dict) and "data" in inner:
            inner = inner["data"]
        if isinstance(inner, dict):
            return inner
    raise RuntimeError("Unexpected Vault response format; expected data dict.")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Vault secrets to .env file.")
    parser.add_argument(
        "path",
        help="Vault API path (for KV v2 include 'data/' in the path, e.g. secret/data/foo)",
    )
    parser.add_argument(
        "--map",
        action="append",
        type=parse_map,
        default=[],
        dest="mappings",
        help="Mapping in form VAULT_KEY=ENV_NAME. Repeat for each variable.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Destination file. Use '-' (default) to print to stdout.",
    )
    args = parser.parse_args(argv)

    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    if not vault_addr or not vault_token:
        parser.error("VAULT_ADDR and VAULT_TOKEN environment variables must be set.")

    secret_data = load_secret(vault_addr, vault_token, args.path)

    if not args.mappings:
        lines = [f"{key}={value}" for key, value in secret_data.items()]
    else:
        merged: Dict[str, str] = {}
        for mapping in args.mappings:
            merged.update(mapping)
        missing = [k for k in merged if k not in secret_data]
        if missing:
            msg = ", ".join(missing)
            raise KeyError(f"Vault payload missing keys: {msg}")
        lines = [
            f"{env_name}={secret_data[vault_key]}"
            for vault_key, env_name in merged.items()
        ]

    content = "\n".join(lines) + "\n"

    if args.output == "-" or args.output.lower() == "stdout":
        sys.stdout.write(content)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Wrote {len(lines)} entries to {args.output}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
