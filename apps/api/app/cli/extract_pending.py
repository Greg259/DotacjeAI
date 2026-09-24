import asyncio
import json

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.services.extraction import process_pending_extractions


async def run() -> int:
    settings = get_settings()
    async with SessionFactory() as session:
        jobs = await process_pending_extractions(session, settings)
        await session.commit()
        for job in jobs:
            print(
                json.dumps(
                    {
                        "extraction_job_id": str(job.id),
                        "review_task_id": str(job.review_task_id),
                        "snapshot_id": str(job.source_snapshot_id),
                        "status": job.status.value,
                        "error": job.error_message,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        return 1 if any(job.status.value == "failed" for job in jobs) else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
