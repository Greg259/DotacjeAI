import argparse
import asyncio
import json
import sys

from pydantic import ValidationError

from app.db.session import SessionFactory
from app.schemas.content import ProgramDetails
from app.services.program_content import ProgramContentError, update_program_content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update reviewed public program content")
    parser.add_argument("slug")
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    try:
        details = ProgramDetails.model_validate(json.load(sys.stdin))
        async with SessionFactory() as session:
            version = await update_program_content(session, args.slug, details, actor="deploy")
            await session.commit()
        print(
            json.dumps(
                {
                    "program_id": str(version.program_id),
                    "program_version_id": str(version.id),
                    "version_number": version.version_number,
                    "status": "updated",
                },
                sort_keys=True,
            )
        )
        return 0
    except (ProgramContentError, ValidationError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
