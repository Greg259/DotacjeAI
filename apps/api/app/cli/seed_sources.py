import asyncio

from sqlalchemy import select

from app.db.session import SessionFactory
from app.models.domain import Location, Source
from app.models.enums import LocationType, SourceType

SOURCES = (
    {
        "name": "WFOŚiGW Warszawa — Czyste Powietrze",
        "slug": "wfosigw-warszawa-czyste-powietrze",
        "url": "https://wfosigw.pl/czyste-powietrze/ogloszenie-o-naborze/",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Gmina Nadarzyn — regulamin wymiany źródła ciepła 2026",
        "slug": "nadarzyn-wymiana-zrodla-ciepla-2026",
        "url": (
            "https://www.nadarzyn.pl/plik%2C23325%2Cregulamin-zalacznik-nr-1-do-"
            "uchwaly-nr-xxv-564-2026-pdf.pdf"
        ),
        "source_type": SourceType.PDF,
    },
    {
        "name": "NFOŚiGW — harmonogram naborów",
        "slug": "nfosigw-harmonogram-naborow",
        "url": "https://www.gov.pl/web/nfosigw/harmonogram-naborow",
        "source_type": SourceType.INDEX,
    },
    {
        "name": "Moje Ciepło",
        "slug": "moje-cieplo",
        "url": "https://mojecieplo.gov.pl/o-programie/",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Przydomowe Magazyny Energii",
        "slug": "przydomowe-magazyny-energii",
        "url": "https://przydomowemagazyny.gov.pl/",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Moja Elektrownia Wiatrowa",
        "slug": "moja-elektrownia-wiatrowa",
        "url": "https://mojaelektrowniawiatrowa.gov.pl/o-programie/",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Ciepłe Mieszkanie",
        "slug": "cieple-mieszkanie",
        "url": "https://czystepowietrze.gov.pl/inne-programy/cieple-mieszkanie",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Miasto Pruszków — gminna dotacja na wymianę pieca 2026",
        "slug": "pruszkow-wymiana-pieca-2026",
        "url": "https://bip.um.pruszkow.pl/artykul/486/6496",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Miasto Pruszków — Ciepłe Mieszkanie",
        "slug": "pruszkow-cieple-mieszkanie",
        "url": "https://www.pruszkow.pl/srodowisko/dofinansowanie/program-cieple-mieszkanie-mozliwosc-wymiany-pieca-weglowego-w-budynku-wielorodzinnym/",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Gmina Brwinów — gminne dofinansowanie do wymiany pieca",
        "slug": "brwinow-wymiana-pieca-2026",
        "url": "https://www.brwinow.pl/aktualnosci/1600-gminne-dotacje-na-zmiane-systemu-ogrzewania-3.html",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Gmina Michałowice — Lokalny Program Piecowy 2026",
        "slug": "michalowice-lokalny-program-piecowy-2026",
        "url": "https://www.michalowice.pl/czystepowietrze1/dla-rolnikow/24-lokalny-program-piecowy-na-terenie-gminy-michal",
        "source_type": SourceType.HTML,
    },
    {
        "name": "Gmina Raszyn — Program Ograniczania Niskiej Emisji 2026",
        "slug": "raszyn-ograniczanie-niskiej-emisji-2026",
        "url": "https://raszyn.pl/aktualnosci/program-ograniczania-niskiej-emisji-nabor-wnioskow-o-przyznanie-dotacji-celowej-do-1",
        "source_type": SourceType.HTML,
    },
)


async def upsert_location(session, *, name, slug, location_type, parent=None):
    location = await session.scalar(
        select(Location).where(
            Location.slug == slug,
            Location.location_type == location_type,
            Location.parent_id == (parent.id if parent else None),
        )
    )
    if location is None:
        location = Location(
            name=name,
            slug=slug,
            location_type=location_type,
            parent_id=parent.id if parent else None,
        )
        session.add(location)
        await session.flush()
    return location


async def seed() -> None:
    async with SessionFactory() as session:
        for source_data in SOURCES:
            source = await session.scalar(select(Source).where(Source.slug == source_data["slug"]))
            if source is None:
                session.add(Source(**source_data))
            else:
                source.name = source_data["name"]
                source.url = source_data["url"]
                source.source_type = source_data["source_type"]

        poland = await upsert_location(
            session,
            name="Polska",
            slug="polska",
            location_type=LocationType.COUNTRY,
        )
        mazowieckie = await upsert_location(
            session,
            name="Mazowieckie",
            slug="mazowieckie",
            location_type=LocationType.REGION,
            parent=poland,
        )
        pruszkowski = await upsert_location(
            session,
            name="Powiat pruszkowski",
            slug="pruszkowski",
            location_type=LocationType.COUNTY,
            parent=mazowieckie,
        )
        for name, slug in (
            ("Nadarzyn", "nadarzyn"),
            ("Pruszków", "pruszkow"),
            ("Brwinów", "brwinow"),
            ("Michałowice", "michalowice"),
            ("Piastów", "piastow"),
            ("Raszyn", "raszyn"),
        ):
            await upsert_location(
                session,
                name=name,
                slug=slug,
                location_type=LocationType.MUNICIPALITY,
                parent=pruszkowski,
            )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
