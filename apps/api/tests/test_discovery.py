from app.services.discovery import discover_links


def test_discovery_keeps_relevant_official_links_and_tags() -> None:
    text = """
LINK: Ścieżka SMART — nabór dla MŚP -> https://www.parp.gov.pl/component/grants/grants/sciezka-smart?utm_source=test
LINK: Start-up z inwestorem venture capital -> https://funduszeeuropejskie.gov.pl/program-startup/#sekcja
LINK: Facebook -> https://facebook.com/parp
LINK: Kontakt -> https://www.parp.gov.pl/kontakt
LINK: Fundusze Europejskie -> https://funduszeeuropejskie.gov.pl/
"""
    items = discover_links(text)
    assert len(items) == 2
    assert items[0][1] == "https://www.parp.gov.pl/component/grants/grants/sciezka-smart"
    assert "sme" in items[0][2]
    assert {"startup", "vc"}.issubset(items[1][2])


def test_discovery_accepts_relevant_links_from_admin_approved_host() -> None:
    text = """
LINK: Nabór na dotacje dla przedsiębiorstw -> https://wsparcie.example/program/dotacje-2026
LINK: Kontakt -> https://wsparcie.example/kontakt
LINK: Dotacje z obcej domeny -> https://untrusted.example/dotacje
"""
    items = discover_links(text, allowed_hosts={"wsparcie.example"})
    assert items == [
        (
            "Nabór na dotacje dla przedsiębiorstw",
            "https://wsparcie.example/program/dotacje-2026",
            ["call", "enterprise", "grant", "program"],
        )
    ]
