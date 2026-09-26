from __future__ import annotations

import re
from dataclasses import asdict, dataclass

_LINK_RE = re.compile(r"^LINK:\s*(.*?)\s*->\s*(https?://\S+)$", re.MULTILINE)
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}|\d{4}-\d{2}-\d{2}|"
    r"(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|"
    r"września|października|listopada|grudnia)\s+\d{4})\b",
    re.IGNORECASE,
)
_AMOUNT_RE = re.compile(
    r"(?:\b\d[\d\s.,]*\s*(?:zł|pln|%)\b|maksymaln\w*\s+kwot\w*|"
    r"poziom\w*\s+dofinansowania|koszt\w*\s+kwalifikowan\w*)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class StructuredChange:
    kinds: list[str]
    added_links: list[str]
    removed_links: list[str]

    def to_dict(self) -> dict[str, list[str]]:
        return asdict(self)


def _links(text: str) -> dict[str, str]:
    return {url: label.strip() for label, url in _LINK_RE.findall(text)}


def classify_source_change(previous: str, current: str) -> StructuredChange:
    """Classify high-value grant changes; the result is a REVIEW hint, never auto-published."""
    old_lines = set(previous.splitlines())
    new_lines = set(current.splitlines())
    removed_lines = old_lines - new_lines
    added_lines = new_lines - old_lines
    changed_text = "\n".join(sorted(removed_lines | added_lines))
    added_text = "\n".join(sorted(added_lines))

    old_links = _links(previous)
    new_links = _links(current)
    added_links = sorted(set(new_links) - set(old_links))
    removed_links = sorted(set(old_links) - set(new_links))
    link_context = " ".join(
        [old_links[url] + " " + url for url in removed_links]
        + [new_links[url] + " " + url for url in added_links]
    )

    kinds: set[str] = set()
    lowered = changed_text.casefold()
    if any(word in lowered for word in ("regulamin", "uchwał", "program priorytetowy")):
        kinds.add("regulation")
    if _DATE_RE.search(changed_text) or any(
        word in lowered for word in ("termin naboru", "nabór od", "nabór do")
    ):
        kinds.add("deadline")
    if _AMOUNT_RE.search(changed_text):
        kinds.add("funding_amount")
    if (added_links or removed_links) and any(
        word in link_context.casefold()
        for word in ("wniosek", "formularz", "załącznik", "gwd", "generator")
    ):
        kinds.add("application_form")
    if any(
        phrase in added_text.casefold()
        for phrase in (
            "nabór zakończony",
            "nabór został zakończony",
            "zamknięcie naboru",
            "wyczerpaniu środków",
            "wstrzymanie naboru",
        )
    ):
        kinds.add("call_closed")
    if not kinds:
        kinds.add("other")
    return StructuredChange(sorted(kinds), added_links, removed_links)
