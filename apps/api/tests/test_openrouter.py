import json
from decimal import Decimal

import httpx
import pytest

from app.core.config import Settings
from app.services.openrouter import MissingApiKeyError, OpenRouterError, extract_with_openrouter


def candidate_payload() -> dict:
    return {
        "schema_version": "extraction-v1",
        "slug": "program-testowy",
        "title": "Program testowy",
        "organizer": "Organizator",
        "summary": None,
        "status": "open",
        "application_start": None,
        "application_end": None,
        "max_amount": None,
        "support_percent": None,
        "currency": "PLN",
        "location_slugs": [],
        "beneficiary_types": [],
        "property_types": [],
        "investment_categories": [],
        "official_url": "https://example.org/source",
        "document_urls": [],
        "evidence": [
            {
                "field": "status",
                "quote": "Nabór trwa",
                "locator": "strona 1",
                "method": "llm",
                "confidence": 0.9,
            },
            {
                "field": "official_url",
                "quote": "https://example.org/source",
                "locator": "rekord źródła",
                "method": "rule",
                "confidence": 1,
            },
        ],
        "warnings": [],
    }


async def test_openrouter_parses_structured_response_and_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["response_format"]["type"] == "json_schema"
        assert body["provider"]["require_parameters"] is True
        assert "temperature" not in body
        schema = body["response_format"]["json_schema"]["schema"]
        assert set(schema["required"]) == set(schema["properties"])
        assert all("default" not in value for value in schema["properties"].values())
        return httpx.Response(
            200,
            json={
                "id": "gen-1",
                "model": "test/model",
                "choices": [{"message": {"content": json.dumps(candidate_payload())}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "cost": 0.0012},
            },
            request=request,
        )

    settings = Settings(OPENROUTER_API_KEY="test-key")
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await extract_with_openrouter(
        settings,
        model="test/model",
        deterministic_data=candidate_payload(),
        source_text="Nabór trwa",
        client=client,
    )
    await client.aclose()

    assert result.candidate.slug == "program-testowy"
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.cost_usd == Decimal("0.0012")
    assert len(result.request_sha256) == 64


async def test_openrouter_stops_before_http_without_api_key() -> None:
    with pytest.raises(MissingApiKeyError):
        await extract_with_openrouter(
            Settings(OPENROUTER_API_KEY=""),
            model="test/model",
            deterministic_data=candidate_payload(),
            source_text="test",
        )


async def test_openrouter_exposes_provider_error_without_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": "Schema is not supported"}},
            request=request,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(OpenRouterError, match="Schema is not supported") as error:
        await extract_with_openrouter(
            Settings(OPENROUTER_API_KEY="secret-test-value"),
            model="test/model",
            deterministic_data=candidate_payload(),
            source_text="test",
            client=client,
        )
    await client.aclose()
    assert "secret-test-value" not in str(error.value)
