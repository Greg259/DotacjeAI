import asyncio
import json

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.services.document_sync import sync_program_documents


async def run() -> int:
    async with SessionFactory() as session:
        results = await sync_program_documents(session, get_settings())
        await session.commit()
    for result in results:
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    return 1 if any(item.outcome == "failed" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
