from __future__ import annotations

import argparse
import asyncio
import json
import time
from decimal import Decimal
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings
from app.models.enums import ProgramStatus

DEFAULT_MODELS = (
    "openai/gpt-oss-20b",
    "deepseek/deepseek-v4-flash",
    "openai/gpt-5-nano",
    "openai/gpt-6-luna",
)


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ProgramStatus | None
    application_end: str | None
    max_amount: Decimal | None
    support_percent: Decimal | None


def _schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {
                "anyOf": [
                    {"type": "string", "enum": [item.value for item in ProgramStatus]},
                    {"type": "null"},
                ]
            },
            "application_end": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "max_amount": {"anyOf": [{"type": "number"}, {"type": "null"}]},
            "support_percent": {"anyOf": [{"type": "number"}, {"type": "null"}]},
        },
        "required": ["status", "application_end", "max_amount", "support_percent"],
    }


def _normalize(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, ProgramStatus):
        return value.value
    return value


async def _run_case(client, settings, model: str, case: dict) -> dict:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Wyodrębnij wyłącznie jawne fakty o naborze dotacji. "
                    "Nie zgaduj; brak danych zwróć jako null. Status ustal względem "
                    "daty 2026-09-26. Kwoty zwróć w PLN jako liczby."
                ),
            },
            {"role": "user", "content": case["text"]},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "grant_benchmark", "strict": True, "schema": _schema()},
        },
        "provider": {"require_parameters": True},
        "usage": {"include": True},
        "stream": False,
    }
    started = time.perf_counter()
    response = await client.post(
        f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://dotacjeai.eu",
            "X-Title": "DotacjeAI benchmark",
        },
        json=payload,
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    response.raise_for_status()
    body = response.json()
    parsed = BenchmarkResult.model_validate_json(body["choices"][0]["message"]["content"])
    actual = {name: _normalize(getattr(parsed, name)) for name in case["expected"]}
    expected = {
        name: str(value) if value is not None else None for name, value in case["expected"].items()
    }
    matches = {name: str(actual[name]) == value for name, value in expected.items()}
    usage = body.get("usage") or {}
    return {
        "case_id": case["id"],
        "url": case["url"],
        "matches": matches,
        "score": sum(matches.values()),
        "possible": len(matches),
        "cost_usd": usage.get("cost"),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "latency_ms": latency_ms,
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--dataset", default="benchmarks/regulations.json")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.openrouter_api_key.get_secret_value():
        raise SystemExit("OPENROUTER_API_KEY is not configured")
    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    report = {"dataset_version": dataset["version"], "models": []}
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        for model in args.models:
            results = []
            for case in dataset["cases"]:
                try:
                    results.append(await _run_case(client, settings, model, case))
                except Exception as exc:  # report failures instead of losing the benchmark
                    results.append(
                        {
                            "case_id": case["id"],
                            "error": str(exc)[:500],
                            "score": 0,
                            "possible": len(case["expected"]),
                            "cost_usd": None,
                        }
                    )
            score = sum(item["score"] for item in results)
            possible = sum(item["possible"] for item in results)
            cost = sum(Decimal(str(item["cost_usd"] or 0)) for item in results)
            report["models"].append(
                {
                    "model": model,
                    "accuracy_percent": round(score * 100 / possible, 2),
                    "score": score,
                    "possible": possible,
                    "cost_usd": str(cost),
                    "failures": sum("error" in item for item in results),
                    "results": results,
                }
            )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
