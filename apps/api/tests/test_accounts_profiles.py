from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password, verify_password
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.domain import Location, PropertyProfile, User
from app.models.enums import LocationType


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password("bardzo-dobre-haslo")
    second = hash_password("bardzo-dobre-haslo")
    assert first != second
    assert verify_password("bardzo-dobre-haslo", first)
    assert not verify_password("inne-bardzo-dobre-haslo", first)


async def test_account_profile_export_and_deletion_flow() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        location = Location(
            name="Nadarzyn", slug="nadarzyn", location_type=LocationType.MUNICIPALITY
        )
        session.add(location)
        await session.commit()
        location_id = str(location.id)

    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
            registration = await client.post(
                "/api/auth/register",
                json={
                    "username": "User1",
                    "password": "bezpieczne-haslo-123",
                    "accept_terms": True,
                    "accept_privacy": True,
                },
            )
            assert registration.status_code == 201
            assert registration.json()["user"]["username"] == "user1"
            assert registration.json()["user"]["role"] == "user"
            assert client.cookies.get("dotacjeai_session")
            csrf = client.cookies.get("dotacjeai_csrf")
            assert csrf

            me = await client.get("/api/auth/me")
            assert me.status_code == 200

            no_csrf = await client.post(
                "/api/profiles",
                json={
                    "name": "Dom",
                    "location_id": location_id,
                    "beneficiary_type": "owner",
                    "property_type": "single_family_house",
                    "building_state": "existing",
                    "current_heat_source": "coal",
                    "year_built": 1998,
                    "heated_area_m2": "145.5",
                    "investment_categories": ["heat_pump", "photovoltaics"],
                },
            )
            assert no_csrf.status_code == 403

            created = await client.post(
                "/api/profiles",
                headers={"x-csrf-token": csrf},
                json={
                    "name": "Dom",
                    "location_id": location_id,
                    "beneficiary_type": "owner",
                    "property_type": "single_family_house",
                    "building_state": "existing",
                    "current_heat_source": "coal",
                    "year_built": 1998,
                    "heated_area_m2": "145.5",
                    "investment_categories": ["heat_pump", "photovoltaics"],
                },
            )
            assert created.status_code == 201
            profile_id = created.json()["id"]
            assert created.json()["location"]["name"] == "Nadarzyn"

            listed = await client.get("/api/profiles")
            assert listed.status_code == 200
            assert len(listed.json()) == 1

            updated = await client.put(
                f"/api/profiles/{profile_id}",
                headers={"x-csrf-token": csrf},
                json={
                    "name": "Dom rodzinny",
                    "location_id": location_id,
                    "beneficiary_type": "co_owner",
                    "property_type": "single_family_house",
                    "building_state": "existing",
                    "current_heat_source": "gas",
                    "year_built": 1998,
                    "heated_area_m2": "145.5",
                    "investment_categories": ["thermal_modernization"],
                },
            )
            assert updated.status_code == 200
            assert updated.json()["name"] == "Dom rodzinny"

            export = await client.get("/api/auth/export")
            assert export.status_code == 200
            assert export.json()["profiles"][0]["name"] == "Dom rodzinny"
            assert "password_hash" not in export.text

            wrong_password = await client.request(
                "DELETE",
                "/api/auth/me",
                headers={"x-csrf-token": csrf},
                json={"password": "zupelnie-zle-haslo"},
            )
            assert wrong_password.status_code == 401

            deleted = await client.request(
                "DELETE",
                "/api/auth/me",
                headers={"x-csrf-token": csrf},
                json={"password": "bezpieczne-haslo-123"},
            )
            assert deleted.status_code == 204
            assert (await client.get("/api/auth/me")).status_code == 401
    finally:
        app.dependency_overrides.clear()

    async with session_factory() as session:
        assert await session.scalar(select(func.count(User.id))) == 0
        assert await session.scalar(select(func.count(PropertyProfile.id))) == 0
    await engine.dispose()
