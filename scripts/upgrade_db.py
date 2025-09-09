#!/usr/bin/env python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _sync_sqlalchemy_url() -> str:
    # Build sync (psycopg2) DSN from app settings
    from apps.backend.app.core.config import settings  # lazy import

    url = settings.database_url.replace("+asyncpg", "")
    if url.startswith("postgresql://") and "sslmode=" not in url:
        try:
            if settings.database.sslmode == "require":
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}sslmode=require"
        except Exception:
            pass
    return url


BASE_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_CFG = BASE_DIR / "alembic.ini"
NEW_BASELINE = "20250913_squashed_initial"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def main() -> int:
    try:
        print("Upgrading DB to head...")
        res = run(["alembic", "-c", str(ALEMBIC_CFG), "upgrade", "head"])
        print(res.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        stdout = e.stdout or ""
        combined = f"{stdout}\n{stderr}"
        if "Can't locate revision identified by" in combined:
            print(
                "Detected unknown DB revision (likely pre-squash). Stamping to new baseline "
                f"{NEW_BASELINE} and retrying..."
            )
            # First try normal Alembic stamp
            try:
                run(["alembic", "-c", str(ALEMBIC_CFG), "stamp", NEW_BASELINE])
            except subprocess.CalledProcessError:
                # Force-stamp by updating alembic_version table directly
                print("Alembic stamp failed; forcing baseline in alembic_version table...")
                try:
                    from sqlalchemy import create_engine

                    engine = create_engine(_sync_sqlalchemy_url())
                    with engine.begin() as conn:
                        conn.exec_driver_sql(
                            "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"
                        )
                        conn.exec_driver_sql("TRUNCATE alembic_version")
                        conn.exec_driver_sql(
                            f"INSERT INTO alembic_version (version_num) VALUES ('{NEW_BASELINE}')"
                        )
                except Exception as ee:
                    sys.stderr.write(f"Failed to force baseline: {ee}\n")
                    return 1
            res2 = run(["alembic", "-c", str(ALEMBIC_CFG), "upgrade", "head"])
            print(res2.stdout)
            return 0
        else:
            # Unknown error, show full output
            sys.stderr.write(combined)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
