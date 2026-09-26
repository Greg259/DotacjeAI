import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.domain import Source, SourceSuggestion
from app.models.enums import SourceType
from app.schemas.source_suggestion import SourceSuggestionPayload


def test_source_suggestion_rejects_non_https_and_private_hosts() -> None:
    for url in (
        "http://example.org/dotacje",
        "https://localhost/dotacje",
        "https://127.0.0.1/dotacje",
        "https://10.20.30.40/dotacje",
    ):
        try:
            SourceSuggestionPayload(url=url)
        except ValueError:
            continue
        raise AssertionError(f"Unsafe URL was accepted: {url}")


async def test_user_submission_requires_csrf_and_admin_approval() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
            registration = await client.post(
                "/api/auth/register",
                json={
                    "username": "source-user",
                    "password": "bezpieczne-haslo-123",
                    "accept_terms": True,
                    "accept_privacy": True,
                },
            )
            assert registration.status_code == 201
            csrf = client.cookies.get("dotacjeai_csrf")
            assert csrf

            payload = {
                "title": "Regionalne wsparcie",
                "url": "https://wsparcie.example/dotacje",
                "note": "Programy dla małych firm",
            }
            without_csrf = await client.post("/api/source-suggestions", json=payload)
            assert without_csrf.status_code == 403

            created = await client.post(
                "/api/source-suggestions",
                headers={"x-csrf-token": csrf},
                json=payload,
            )
            assert created.status_code == 201
            suggestion_id = created.json()["id"]
            assert created.json()["status"] == "pending"

            duplicate = await client.post(
                "/api/source-suggestions",
                headers={"x-csrf-token": csrf},
                json=payload,
            )
            assert duplicate.status_code == 409

            listed = await client.get("/api/source-suggestions")
            assert listed.status_code == 200
            assert [item["id"] for item in listed.json()] == [suggestion_id]

            approved = await client.post(f"/admin/source-suggestions/{suggestion_id}/approve")
            assert approved.status_code == 200
            assert approved.json()["status"] == "approved"

        async with session_factory() as session:
            suggestion = await session.get(SourceSuggestion, uuid.UUID(suggestion_id))
            assert suggestion is not None
            assert suggestion.status == "approved"
            assert suggestion.source_id is not None
            source = await session.scalar(select(Source).where(Source.id == suggestion.source_id))
            assert source is not None
            assert source.active is True
            assert source.source_type == SourceType.INDEX
            assert source.slug.startswith("user-suggestion-")
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
