from datetime import date

from app.models.domain import Source, SourceSnapshot
from app.models.enums import ProgramStatus, SourceType
from app.services.deterministic_extraction import extract_deterministic


def test_nadarzyn_rules_extract_closed_deadline_amount_and_percent() -> None:
    source = Source(
        name="Gmina Nadarzyn",
        slug="nadarzyn-wymiana-zrodla-ciepla-2026",
        url="https://example.org/regulamin.pdf",
        source_type=SourceType.PDF,
    )
    snapshot = SourceSnapshot(
        source_id=source.id,
        final_url=source.url,
        http_status=200,
        sha256="a" * 64,
        normalized_sha256="b" * 64,
        size_bytes=100,
        storage_path="nadarzyn/source.pdf",
        normalized_text=(
            "Wnioski o udzielenie dotacji można składać do dnia 31 lipca 2026 r. "
            "Dofinansowanie wynosi do 100% kosztów. Maksymalna kwota dofinansowania "
            "wynosi 6 000 zł."
        ),
        is_changed=True,
    )

    candidate = extract_deterministic(source, snapshot, today=date(2026, 9, 24))

    assert candidate.application_end == date(2026, 7, 31)
    assert candidate.max_amount == 6000
    assert candidate.support_percent == 100
    assert candidate.status == ProgramStatus.CLOSED
    assert candidate.location_slugs == ["nadarzyn"]
    assert candidate.missing_critical_evidence() == []


def test_rules_keep_unknown_status_when_source_has_no_status_evidence() -> None:
    source = Source(
        name="Źródło testowe",
        slug="zrodlo-testowe",
        url="https://example.org/source",
        source_type=SourceType.HTML,
    )
    snapshot = SourceSnapshot(
        source_id=source.id,
        final_url=source.url,
        http_status=200,
        sha256="a" * 64,
        normalized_sha256="b" * 64,
        size_bytes=20,
        storage_path="test/source.html",
        normalized_text="Informacja ogólna bez terminu.",
        is_changed=True,
    )

    candidate = extract_deterministic(source, snapshot, today=date(2026, 9, 24))

    assert candidate.status == ProgramStatus.UNKNOWN
    assert candidate.missing_critical_evidence() == ["status"]
    assert candidate.warnings[0].code == "status_unknown"
