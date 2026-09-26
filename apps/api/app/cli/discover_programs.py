import asyncio
import json

from app.db.session import SessionFactory
from app.services.discovery import discover_from_indexes


async def run() -> int:
    async with SessionFactory() as session:
        created, updated = await discover_from_indexes(session)
        await session.commit()
    print(json.dumps({"created": created, "updated": updated}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
