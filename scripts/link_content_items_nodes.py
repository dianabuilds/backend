"""Link existing content_items records to nodes via node_id.

This script sets ``content_items.node_id`` to the value of ``content_items.id``
for rows where ``node_id`` is NULL. Run it after adding the ``node_id`` column
via migration.
"""

import asyncio

from apps.backend.app.providers.db.session import db_session
from sqlalchemy import text


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
