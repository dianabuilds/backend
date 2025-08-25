from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_CFG = BASE_DIR / "alembic.ini"


@pytest.mark.skipif(
    "RUN_DB_TESTS" not in os.environ,
    reason="Database tests require RUN_DB_TESTS=1",
)
def test_migrations_up_to_date(tmp_path: Path) -> None:
    """Apply migrations and ensure models match schema."""
    subprocess.run(
        ["alembic", "-c", str(ALEMBIC_CFG), "upgrade", "head"], check=True
    )
    result = subprocess.run(
        [
            "alembic",
            "-c",
            str(ALEMBIC_CFG),
            "revision",
            "--autogenerate",
            "--sql",
            "-m",
            "migration_check",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "No changes in schema detected" in result.stdout
