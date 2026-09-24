import argparse
import asyncio
import json
import sys
import uuid

from app.db.session import SessionFactory
from app.services.review import (
    ReviewOperationError,
    approve_review,
    get_review_details,
    list_reviews,
    publish_program,
    reject_review,
    replace_review_candidate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Operate the private REVIEW queue")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    show = commands.add_parser("show")
    show.add_argument("review_id", type=uuid.UUID)
    approve = commands.add_parser("approve")
    approve.add_argument("review_id", type=uuid.UUID)
    reject = commands.add_parser("reject")
    reject.add_argument("review_id", type=uuid.UUID)
    reject.add_argument("--note", required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("program_id", type=uuid.UUID)
    replace = commands.add_parser("replace")
    replace.add_argument("review_id", type=uuid.UUID)
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    try:
        async with SessionFactory() as session:
            if args.command == "list":
                result = await list_reviews(session)
            elif args.command == "show":
                result = await get_review_details(session, args.review_id)
            elif args.command == "approve":
                program = await approve_review(session, args.review_id, actor="deploy")
                result = {"program_id": str(program.id), "status": "approved"}
            elif args.command == "reject":
                await reject_review(session, args.review_id, actor="deploy", note=args.note)
                result = {"review_id": str(args.review_id), "status": "rejected"}
            elif args.command == "replace":
                await replace_review_candidate(
                    session,
                    args.review_id,
                    json.load(sys.stdin),
                    actor="deploy",
                )
                result = {"review_id": str(args.review_id), "status": "candidate_replaced"}
            else:
                program = await publish_program(session, args.program_id, actor="deploy")
                result = {"program_id": str(program.id), "status": "published"}
            await session.commit()
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
            return 0
    except ReviewOperationError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
