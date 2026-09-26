import re
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import ProgramDiscovery, Source, SourceSnapshot
from app.models.enums import SourceType

LINK_RE = re.compile(r"^LINK:\s*(?P<title>.+?)\s*->\s*(?P<url>https?://\S+)$")
KEYWORDS = {
    "dotac": "grant",
    "dofinans": "grant",
    "nabór": "call",
    "nabor": "call",
    "konkurs": "call",
    "program": "program",
    "startup": "startup",
    "start-up": "startup",
    "venture": "vc",
    "fundusz": "funding",
    "innowac": "innovation",
    "badani": "research",
    "b+r": "research",
    "mśp": "sme",
    "msp": "sme",
    "przedsiębior": "enterprise",
    "przedsiebior": "enterprise",
}
OFFICIAL_SUFFIXES = (
    "parp.gov.pl",
    "ncbr.gov.pl",
    "funduszeeuropejskie.gov.pl",
    "nowoczesnagospodarka.gov.pl",
    "gov.pl",
)
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}


def _normalize_url(value: str) -> str | None:
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not any(
        hostname == suffix or hostname.endswith("." + suffix) for suffix in OFFICIAL_SUFFIXES
    ):
        return None
    query = urlencode(
        [(key, item) for key, item in parse_qsl(parsed.query) if key.lower() not in TRACKING_PARAMS]
    )
    return urlunparse(
        ("https", parsed.netloc.lower(), parsed.path.rstrip("/") or "/", "", query, "")
    )


def discover_links(text: str) -> list[tuple[str, str, list[str]]]:
    discovered = []
    seen = set()
    for line in text.splitlines():
        match = LINK_RE.match(line.strip())
        if not match:
            continue
        title = match.group("title").strip()[:500]
        url = _normalize_url(match.group("url"))
        searchable = f"{title} {url or ''}".casefold()
        tags = sorted({tag for keyword, tag in KEYWORDS.items() if keyword in searchable})
        if not url or not tags or url in seen:
            continue
        seen.add(url)
        discovered.append((title, url, tags))
    return discovered


async def discover_from_indexes(session: AsyncSession) -> tuple[int, int]:
    sources = list(
        (
            await session.scalars(
                select(Source).where(
                    Source.active.is_(True), Source.source_type == SourceType.INDEX
                )
            )
        ).all()
    )
    created = 0
    updated = 0
    now = datetime.now(UTC)
    for source in sources:
        snapshot = await session.scalar(
            select(SourceSnapshot)
            .where(
                SourceSnapshot.source_id == source.id, SourceSnapshot.http_status.in_([200, 304])
            )
            .order_by(SourceSnapshot.fetched_at.desc(), SourceSnapshot.id.desc())
            .limit(1)
        )
        if not snapshot:
            continue
        for title, url, tags in discover_links(snapshot.normalized_text or ""):
            item = await session.scalar(select(ProgramDiscovery).where(ProgramDiscovery.url == url))
            if item is None:
                session.add(
                    ProgramDiscovery(
                        index_source_id=source.id,
                        title=title,
                        url=url,
                        audience_tags=tags,
                        status="new",
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                )
                created += 1
            else:
                item.title = title
                item.audience_tags = tags
                item.last_seen_at = now
                updated += 1
    await session.flush()
    return created, updated
