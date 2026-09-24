import asyncio
import json

from app.db.session import SessionFactory
from app.services.status_refresh import propose_date_status_changes


async def run() -> int:
    async with SessionFactory() as session:
        reviews = await propose_date_status_changes(session)
        await session.commit()
    print(json.dumps({"status_reviews_created": len(reviews)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
