"""Link existing content_items records to nodes via node_id.

This script sets ``content_items.node_id`` to the value of ``content_items.id``
for rows where ``node_id`` is NULL. Run it after adding the ``node_id`` column
via migration.
"""

import asyncio
from pathlib import Path
import sys

from sqlalchemy import text

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.app.core.db.session import db_session  # noqa: E402


async def main() -> None:
    async with db_session() as session:
        await session.execute(
            text(
                """
                UPDATE content_items SET node_id = id
                WHERE node_id IS NULL
                """
            )
        )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
