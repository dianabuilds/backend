"""Backfill quest step content from legacy node references.

This one-off script copies content linked via the old
``quest_step_content_refs`` table into the ``quest_steps.content``
JSON field.  After running it successfully the
``quest_step_content_refs`` table can be dropped safely.
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent

# Ensure ``app`` package is importable when running as a standalone script.
sys.path.insert(0, str(project_root / "apps/backend"))
sys.path.insert(0, str(project_root))

from apps.backend.app.core.db.session import db_session  # noqa: E402


async def main() -> None:
    async with db_session() as session:
        # Determine which column on nodes contains the content data.
        res = await session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='nodes'"
            )
        )
        columns = {row[0] for row in res}
        node_content_col = "content" if "content" in columns else "meta"

        # Aggregate node content into quest_steps.content
        query = text(
            f"""
            SELECT qscr.step_id, jsonb_agg(n.{node_content_col} ORDER BY qscr.position) AS content
            FROM quest_step_content_refs qscr
            JOIN nodes n ON n.alt_id = qscr.content_id
            GROUP BY qscr.step_id
            """
        )
        result = await session.execute(query)
        rows = result.fetchall()

        for step_id, content in rows:
            await session.execute(
                text("UPDATE quest_steps SET content = :content WHERE id = :step_id"),
                {"content": content, "step_id": step_id},
            )

        # Verify that every quest step now has content.
        verify = await session.execute(
            text(
                "SELECT id FROM quest_steps WHERE content IS NULL OR jsonb_array_length(content) = 0"
            )
        )
        missing = [row[0] for row in verify.fetchall()]
        if missing:
            raise RuntimeError(f"Quest steps missing content: {missing}")

        await session.commit()
        print(f"Backfilled content for {len(rows)} quest steps.")


if __name__ == "__main__":
    asyncio.run(main())
