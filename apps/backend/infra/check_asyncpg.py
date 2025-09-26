import asyncio
import pathlib

import asyncpg

APP_DATABASE_URL = "postgresql+asyncpg://doadmin:AVNS_cRda4qa3Xg21243zqc7@db-postgresql-fra1-60088-do-user-338284-0.i.db.ondigitalocean.com:25060/defaultdb?sslmode=require&sslrootcert=ca-certificate.crt"

dsn = str(APP_DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://", 1)
print("Using DSN:", APP_DATABASE_URL)
print("Asyncpg DSN:", dsn)
print(
    "CA exists:",
    pathlib.Path("E://code//caves//backend//apps//backend//infra//check_asyncpg.py")
    .resolve()
    .exists(),
)


async def main():
    conn = await asyncpg.connect(dsn, ssl="require")
    print("Connected!")
    await conn.close()


asyncio.run(main())
