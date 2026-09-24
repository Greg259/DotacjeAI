import re
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from app.models.domain import Source, SourceSnapshot
from app.models.enums import (
    BeneficiaryType,
    InvestmentCategory,
    ProgramStatus,
    PropertyType,
)
from app.schemas.extraction import ExtractionCandidate, ExtractionWarning, FieldEvidence
from app.services.status import infer_program_status

POLISH_MONTHS = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "wrzesnia": 9,
    "października": 10,
    "pazdziernika": 10,
    "listopada": 11,
    "grudnia": 12,
}

SOURCE_PROFILES = {
    "nadarzyn-wymiana-zrodla-ciepla-2026": {
        "slug": "nadarzyn-wymiana-zrodla-ciepla-2026",
        "title": "Dofinansowanie do wymiany źródła ciepła w Gminie Nadarzyn",
        "organizer": "Gmina Nadarzyn",
        "location_slugs": ["nadarzyn"],
        "beneficiary_types": [BeneficiaryType.NATURAL_PERSON, BeneficiaryType.OWNER],
        "property_types": [PropertyType.SINGLE_FAMILY_HOUSE, PropertyType.EXISTING_BUILDING],
        "investment_categories": [InvestmentCategory.HEAT_SOURCE_REPLACEMENT],
    },
    "wfosigw-warszawa-czyste-powietrze": {
        "slug": "czyste-powietrze-mazowieckie",
        "title": "Czyste Powietrze — województwo mazowieckie",
        "organizer": "WFOŚiGW w Warszawie",
        "location_slugs": ["mazowieckie"],
        "beneficiary_types": [
            BeneficiaryType.NATURAL_PERSON,
            BeneficiaryType.OWNER,
            BeneficiaryType.CO_OWNER,
        ],
        "property_types": [PropertyType.SINGLE_FAMILY_HOUSE, PropertyType.EXISTING_BUILDING],
        "investment_categories": [
            InvestmentCategory.HEAT_SOURCE_REPLACEMENT,
            InvestmentCategory.THERMAL_MODERNIZATION,
        ],
    },
}


def _quote(text: str, start: int, end: int, radius: int = 100) -> str:
    value = text[max(0, start - radius) : min(len(text), end + radius)]
    return re.sub(r"\s+", " ", value).strip()[:1000]


def _rank_context(quote: str, keywords: tuple[str, ...]) -> int:
    lowered = quote.lower()
    return sum(1 for keyword in keywords if keyword in lowered)


def _extract_end_date(text: str) -> tuple[date | None, FieldEvidence | None]:
    candidates: list[tuple[int, date, str]] = []
    word_pattern = re.compile(
        r"\b([0-3]?\d)\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|"
        r"września|wrzesnia|października|pazdziernika|listopada|grudnia)\s+(20\d{2})\b",
        re.IGNORECASE,
    )
    numeric_pattern = re.compile(r"\b([0-3]?\d)[.\-/]([01]?\d)[.\-/](20\d{2})\b")

    for match in word_pattern.finditer(text):
        day, month_name, year = match.groups()
        try:
            value = date(int(year), POLISH_MONTHS[month_name.lower()], int(day))
        except ValueError:
            continue
        quote = _quote(text, match.start(), match.end())
        score = _rank_context(quote, ("nabór", "nabor", "wniosk", "termin", "do dnia"))
        candidates.append((score, value, quote))

    for match in numeric_pattern.finditer(text):
        day, month, year = match.groups()
        try:
            value = date(int(year), int(month), int(day))
        except ValueError:
            continue
        quote = _quote(text, match.start(), match.end())
        score = _rank_context(quote, ("nabór", "nabor", "wniosk", "termin", "do dnia"))
        candidates.append((score, value, quote))

    if not candidates:
        return None, None
    score, value, quote = max(candidates, key=lambda item: (item[0], item[1]))
    if score == 0:
        return None, None
    return value, FieldEvidence(
        field="application_end",
        quote=quote,
        locator="znormalizowany tekst źródła",
        method="rule",
        confidence=min(0.98, 0.70 + score * 0.08),
    )


def _extract_money(text: str) -> tuple[Decimal | None, FieldEvidence | None]:
    pattern = re.compile(r"(?<!\d)(\d{1,3}(?:[ .]\d{3})+|\d{3,7})(?:,\d{1,2})?\s*(?:zł|PLN)", re.I)
    candidates: list[tuple[int, Decimal, str]] = []
    for match in pattern.finditer(text):
        raw = re.sub(r"[ .]", "", match.group(1))
        try:
            amount = Decimal(raw.replace(",", "."))
        except InvalidOperation:
            continue
        quote = _quote(text, match.start(), match.end())
        score = _rank_context(quote, ("maksymal", "nie więcej", "do wysokości", "dofinans"))
        candidates.append((score, amount, quote))
    if not candidates:
        return None, None
    score, amount, quote = max(candidates, key=lambda item: (item[0], item[1]))
    if score == 0:
        return None, None
    return amount, FieldEvidence(
        field="max_amount",
        quote=quote,
        locator="znormalizowany tekst źródła",
        method="rule",
        confidence=min(0.96, 0.72 + score * 0.08),
    )


def _extract_percent(text: str) -> tuple[Decimal | None, FieldEvidence | None]:
    pattern = re.compile(r"(?<!\d)(100|[1-9]?\d)(?:[,.](\d{1,2}))?\s*%")
    candidates: list[tuple[int, Decimal, str]] = []
    for match in pattern.finditer(text):
        value = Decimal(f"{match.group(1)}.{match.group(2) or '0'}")
        quote = _quote(text, match.start(), match.end())
        score = _rank_context(quote, ("dofinans", "koszt", "poziom", "maksymal"))
        candidates.append((score, value, quote))
    if not candidates:
        return None, None
    score, value, quote = max(candidates, key=lambda item: (item[0], item[1]))
    if score == 0:
        return None, None
    return value, FieldEvidence(
        field="support_percent",
        quote=quote,
        locator="znormalizowany tekst źródła",
        method="rule",
        confidence=min(0.96, 0.72 + score * 0.08),
    )


def _extract_links(text: str) -> list[str]:
    links = []
    for match in re.finditer(r"^LINK: .+ -> (https?://\S+)$", text, re.MULTILINE):
        url = match.group(1).rstrip(".,;)")
        if urlparse(url).scheme in {"http", "https"}:
            links.append(url)
    return list(dict.fromkeys(links))


def _declared_status(text: str) -> tuple[ProgramStatus | None, str | None]:
    patterns = (
        (ProgramStatus.CLOSED, r"(?:nabór|nabor).{0,80}(?:zakończ|zamknięt)"),
        (ProgramStatus.SUSPENDED, r"(?:nabór|nabor).{0,80}(?:wstrzym|zawiesz)"),
        (ProgramStatus.OPEN, r"(?:nabór|nabor).{0,80}(?:trwa|ciągł|otwart)"),
    )
    for status, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return status, _quote(text, match.start(), match.end())
    return None, None


def extract_deterministic(
    source: Source,
    snapshot: SourceSnapshot,
    *,
    today: date,
) -> ExtractionCandidate:
    text = snapshot.normalized_text or ""
    profile = SOURCE_PROFILES.get(
        source.slug,
        {
            "slug": source.slug,
            "title": source.name,
            "organizer": source.name,
            "location_slugs": [],
            "beneficiary_types": [],
            "property_types": [],
            "investment_categories": [],
        },
    )
    end_date, date_evidence = _extract_end_date(text)
    max_amount, amount_evidence = _extract_money(text)
    support_percent, percent_evidence = _extract_percent(text)
    declared, status_quote = _declared_status(text)
    status = infer_program_status(
        today=today,
        application_start=None,
        application_end=end_date,
        declared_status=declared,
    )

    evidence = [
        FieldEvidence(
            field="official_url",
            quote=source.url,
            locator="rekord źródła",
            method="rule",
            confidence=1,
        )
    ]
    evidence.extend(item for item in (date_evidence, amount_evidence, percent_evidence) if item)
    status_basis = status_quote or (date_evidence.quote if date_evidence else None)
    if status_basis:
        evidence.append(
            FieldEvidence(
                field="status",
                quote=status_basis,
                locator="znormalizowany tekst źródła",
                method="rule",
                confidence=0.98 if end_date and today > end_date else 0.82,
            )
        )

    warnings = []
    if status == ProgramStatus.UNKNOWN:
        warnings.append(
            ExtractionWarning(
                code="status_unknown",
                message="Reguły nie ustaliły jednoznacznego statusu naboru.",
                fields=["status"],
            )
        )

    return ExtractionCandidate(
        slug=profile["slug"],
        title=profile["title"],
        organizer=profile["organizer"],
        status=status,
        application_end=end_date,
        max_amount=max_amount,
        support_percent=support_percent,
        location_slugs=profile["location_slugs"],
        beneficiary_types=profile["beneficiary_types"],
        property_types=profile["property_types"],
        investment_categories=profile["investment_categories"],
        official_url=source.url,
        document_urls=_extract_links(text),
        evidence=evidence,
        warnings=warnings,
    )
