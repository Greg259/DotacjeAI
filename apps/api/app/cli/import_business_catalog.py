import argparse
import asyncio
import json
from pathlib import Path

from app.db.session import SessionFactory
from app.services.business_catalog import import_business_catalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importuj zweryfikowany katalog programów dla firm."
    )
    parser.add_argument(
        "--path", type=Path, default=Path("/app/catalog-data/business-programs-2026-09.json")
    )
    parser.add_argument("--actor", default="deploy")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    async with SessionFactory() as session:
        result = await import_business_catalog(session, args.path, actor=args.actor)
        await session.commit()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(run())
