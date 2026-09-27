from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    AuditLog,
    Location,
    Program,
    ProgramBeneficiaryType,
    ProgramBusinessSize,
    ProgramDocument,
    ProgramInvestmentCategory,
    ProgramLocation,
    ProgramVersion,
    Source,
    SourceSnapshot,
)
from app.models.enums import DocumentState, DocumentType, LocationType, SourceType
from app.schemas.extraction import ExtractionCandidate

REGIONS = {
    "dolnoslaskie": "Dolnośląskie",
    "kujawsko-pomorskie": "Kujawsko-pomorskie",
    "lubelskie": "Lubelskie",
    "lubuskie": "Lubuskie",
    "lodzkie": "Łódzkie",
    "malopolskie": "Małopolskie",
    "mazowieckie": "Mazowieckie",
    "opolskie": "Opolskie",
    "podkarpackie": "Podkarpackie",
    "podlaskie": "Podlaskie",
    "pomorskie": "Pomorskie",
    "slaskie": "Śląskie",
    "swietokrzyskie": "Świętokrzyskie",
    "warminsko-mazurskie": "Warmińsko-mazurskie",
    "wielkopolskie": "Wielkopolskie",
    "zachodniopomorskie": "Zachodniopomorskie",
}


class MatchingTests(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_field: str
    positive: Any
    negative: Any
    missing: None = None


class CatalogProgram(ExtractionCandidate):
    matching_tests: MatchingTests
    catalog_evidence: dict[str, str]


class BusinessCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["business-catalog-v1"]
    verified_at: datetime
    master_source_url: HttpUrl
    programs: list[CatalogProgram] = Field(min_length=30, max_length=50)


def load_business_catalog(path: Path) -> tuple[BusinessCatalog, bytes]:
    payload = path.read_bytes()
    catalog = BusinessCatalog.model_validate_json(payload)
    slugs = [item.slug for item in catalog.programs]
    if len(set(slugs)) != len(slugs):
        raise ValueError("duplicate_catalog_slug")
    for item in catalog.programs:
        if len(item.eligibility_rules) != 1:
            raise ValueError(f"exactly_one_tested_rule_required:{item.slug}")
        rule = item.eligibility_rules[0]
        if rule.profile_field.value != item.matching_tests.profile_field:
            raise ValueError(f"matching_test_field_mismatch:{item.slug}")
        requirements = item.details.business_requirements
        if requirements is None or requirements.source_url is None:
            raise ValueError(f"business_requirements_evidence_missing:{item.slug}")
    return catalog, payload


async def _location(
    session: AsyncSession, slug: str, *, parent: Location | None = None
) -> Location:
    result = await session.scalar(select(Location).where(Location.slug == slug))
    if result is None:
        result = Location(
            name="Polska" if slug == "polska" else REGIONS[slug],
            slug=slug,
            location_type=LocationType.COUNTRY if slug == "polska" else LocationType.REGION,
            parent_id=parent.id if parent else None,
        )
        session.add(result)
        await session.flush()
    return result


async def import_business_catalog(
    session: AsyncSession, path: Path, *, actor: str = "catalog-import"
) -> dict[str, int]:
    catalog, payload = load_business_catalog(path)
    digest = hashlib.sha256(payload).hexdigest()
    verified_at = catalog.verified_at.astimezone(UTC)
    master_url = str(catalog.master_source_url)
    master = await session.scalar(select(Source).where(Source.url == master_url))
    if master is None:
        master = Source(
            name="Fundusze Europejskie — wykaz naborów wrzesień 2026",
            slug="fundusze-europejskie-katalog-wrzesien-2026",
            url=master_url,
            source_type=SourceType.INDEX,
            active=True,
            crawl_interval_minutes=1440,
        )
        session.add(master)
        await session.flush()
    snapshot = await session.scalar(
        select(SourceSnapshot).where(
            SourceSnapshot.source_id == master.id,
            SourceSnapshot.sha256 == digest,
        )
    )
    if snapshot is None:
        snapshot = SourceSnapshot(
            source_id=master.id,
            fetched_at=verified_at,
            final_url=master_url,
            http_status=200,
            content_type="application/json",
            sha256=digest,
            normalized_sha256=digest,
            size_bytes=len(payload),
            storage_path=f"catalog-data/{path.name}",
            is_changed=True,
        )
        session.add(snapshot)
        await session.flush()

    poland = await _location(session, "polska")
    locations = {"polska": poland}
    for slug in REGIONS:
        locations[slug] = await _location(session, slug, parent=poland)

    created = updated = unchanged = 0
    for entry in catalog.programs:
        official_url = str(entry.official_url)
        source = await session.scalar(select(Source).where(Source.url == official_url))
        if source is None:
            source_slug_hash = hashlib.sha256(official_url.encode()).hexdigest()[:8]
            source = Source(
                name=entry.title[:255],
                slug=f"source-{entry.slug[:143]}-{source_slug_hash}",
                url=official_url,
                source_type=SourceType.HTML,
                active=False,
                crawl_interval_minutes=1440,
            )
            session.add(source)
            await session.flush()

        program = await session.scalar(select(Program).where(Program.slug == entry.slug))
        is_new = program is None
        if program is None:
            program = Program(slug=entry.slug, title=entry.title, organizer=entry.organizer)
            session.add(program)
            await session.flush()

        extracted = entry.model_dump(
            mode="json", exclude={"matching_tests", "catalog_evidence", "evidence"}
        )
        extracted["catalog_evidence"] = entry.catalog_evidence
        extracted["catalog_fingerprint"] = digest
        latest = await session.scalar(
            select(ProgramVersion)
            .where(ProgramVersion.program_id == program.id, ProgramVersion.approved_at.is_not(None))
            .order_by(ProgramVersion.version_number.desc())
        )
        if latest and latest.extracted_data == extracted:
            unchanged += 1
            continue

        program.primary_source_id = source.id
        program.title = entry.title
        program.organizer = entry.organizer
        program.summary = entry.summary
        program.status = entry.status
        program.application_start = entry.application_start
        program.application_end = entry.application_end
        program.max_amount = entry.max_amount
        program.support_percent = entry.support_percent
        program.currency = entry.currency
        program.last_verified_at = verified_at
        program.is_published = True
        program.published_at = program.published_at or verified_at
        program.eligibility_rules = [
            rule.model_dump(mode="json") for rule in entry.eligibility_rules
        ]

        await session.execute(
            delete(ProgramLocation).where(ProgramLocation.program_id == program.id)
        )
        await session.execute(
            delete(ProgramBeneficiaryType).where(ProgramBeneficiaryType.program_id == program.id)
        )
        await session.execute(
            delete(ProgramInvestmentCategory).where(
                ProgramInvestmentCategory.program_id == program.id
            )
        )
        await session.execute(
            delete(ProgramBusinessSize).where(ProgramBusinessSize.program_id == program.id)
        )
        session.add_all(
            [
                ProgramLocation(program_id=program.id, location_id=locations[slug].id)
                for slug in entry.location_slugs
            ]
        )
        session.add_all(
            [
                ProgramBeneficiaryType(program_id=program.id, beneficiary_type=value)
                for value in entry.beneficiary_types
            ]
        )
        session.add_all(
            [
                ProgramInvestmentCategory(program_id=program.id, investment_category=value)
                for value in entry.investment_categories
            ]
        )
        session.add_all(
            [
                ProgramBusinessSize(program_id=program.id, business_size=value)
                for value in entry.business_sizes
            ]
        )

        version_number = (
            await session.scalar(
                select(func.coalesce(func.max(ProgramVersion.version_number), 0)).where(
                    ProgramVersion.program_id == program.id
                )
            )
        ) + 1
        version = ProgramVersion(
            program_id=program.id,
            source_snapshot_id=snapshot.id,
            version_number=version_number,
            extracted_data=extracted,
            evidence={"catalog": entry.catalog_evidence, "manifest_sha256": digest},
            change_summary="Zweryfikowany import katalogu firmowego Sprint 10D",
            approved_at=verified_at,
        )
        session.add(version)
        document = await session.scalar(
            select(ProgramDocument).where(
                ProgramDocument.program_id == program.id,
                ProgramDocument.url == official_url,
            )
        )
        if document is None:
            session.add(
                ProgramDocument(
                    program_id=program.id,
                    title="Oficjalna strona naboru",
                    url=official_url,
                    document_type=DocumentType.ANNOUNCEMENT,
                    state=DocumentState.CURRENT,
                    last_checked_at=verified_at,
                )
            )
        session.add(
            AuditLog(
                actor=actor,
                action="business_catalog.create" if is_new else "business_catalog.update",
                entity_type="program_version",
                entity_id=version.id,
                details={
                    "program_id": str(program.id),
                    "slug": program.slug,
                    "manifest_sha256": digest,
                },
            )
        )
        created += int(is_new)
        updated += int(not is_new)

    await session.flush()
    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "total": len(catalog.programs),
    }
