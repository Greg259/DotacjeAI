from app.services.change_detection import classify_source_change


def test_classifies_deadline_amount_form_and_closure() -> None:
    previous = """Termin naboru do 30.06.2026
Maksymalna kwota 6 000 zł
LINK: Formularz wniosku -> https://example.org/form-v1.pdf"""
    current = """Nabór zakończony po wyczerpaniu środków 31.07.2026
Maksymalna kwota 8 000 zł
LINK: Formularz wniosku -> https://example.org/form-v2.pdf"""

    result = classify_source_change(previous, current)

    assert result.kinds == [
        "application_form",
        "call_closed",
        "deadline",
        "funding_amount",
    ]
    assert result.added_links == ["https://example.org/form-v2.pdf"]
    assert result.removed_links == ["https://example.org/form-v1.pdf"]


def test_classifies_regulation_change() -> None:
    result = classify_source_change("Regulamin z 2025 r.", "Regulamin z 2026 r.")
    assert "regulation" in result.kinds
