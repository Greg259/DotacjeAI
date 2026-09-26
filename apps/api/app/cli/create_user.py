import argparse
import asyncio
import getpass
import sys
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionFactory
from app.models.domain import User
from app.models.enums import UserRole
from app.schemas.user import Credentials


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Utwórz lub zaktualizuj lokalne konto DotacjeAI.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", choices=[item.value for item in UserRole], default="user")
    parser.add_argument("--password-stdin", action="store_true")
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    password = sys.stdin.readline().rstrip("\r\n") if args.password_stdin else getpass.getpass()
    credentials = Credentials(username=args.username, password=password)
    settings = get_settings()
    now = datetime.now(UTC)
    async with SessionFactory() as session:
        user = await session.scalar(select(User).where(User.username == credentials.username))
        if user:
            user.password_hash = hash_password(credentials.password)
            user.role = UserRole(args.role)
            user.is_active = True
            action = "updated"
        else:
            user = User(
                username=credentials.username,
                password_hash=hash_password(credentials.password),
                role=UserRole(args.role),
                terms_version=settings.terms_version,
                accepted_terms_at=now,
                accepted_privacy_at=now,
            )
            session.add(user)
            action = "created"
        await session.commit()
    print(f"{action}:{credentials.username}:{args.role}")


if __name__ == "__main__":
    asyncio.run(run())
