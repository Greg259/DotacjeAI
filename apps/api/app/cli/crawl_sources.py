import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.models.domain import Source
from app.services.crawler import CrawlError, crawl_source

PRIORITY_SOURCES = (
    "wfosigw-warszawa-czyste-powietrze",
    "nadarzyn-wymiana-zrodla-ciepla-2026",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and version official grant sources")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="crawl every active source")
    group.add_argument("--slug", action="append", help="source slug; may be repeated")
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    settings = get_settings()
    requested = tuple(args.slug or PRIORITY_SOURCES)

    async with SessionFactory() as session:
        statement = select(Source).where(Source.active.is_(True)).order_by(Source.slug)
        if not args.all:
            statement = statement.where(Source.slug.in_(requested))
        sources = list((await session.scalars(statement)).all())

        found = {source.slug for source in sources}
        missing = sorted(set(requested) - found) if not args.all else []
        if missing:
            print(json.dumps({"error": "unknown_sources", "slugs": missing}))
            return 2

        failures = 0
        for source in sources:
            source_id = source.id
            source_slug = source.slug
            try:
                result = await crawl_source(session, source, settings)
                await session.commit()
                print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
            except (CrawlError, OSError) as exc:
                await session.rollback()
                failures += 1
                error_message = str(exc)[:4000]
                failed_at = datetime.now(UTC)
                await session.execute(
                    update(Source)
                    .where(Source.id == source_id)
                    .values(
                        last_checked_at=failed_at,
                        last_error_at=failed_at,
                        last_error_message=error_message,
                    )
                )
                await session.commit()
                print(
                    json.dumps(
                        {
                            "source_slug": source_slug,
                            "outcome": "failed",
                            "error": error_message,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                )
        return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
