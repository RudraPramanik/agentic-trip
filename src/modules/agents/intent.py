from __future__ import annotations

import json
import re
from typing import Any

from src.modules.geo.types import INTENT_JSON_SCHEMA, AskClarification, TripIntent
from src.modules.llm.types import LlmUnavailable
from src.ports import LlmGateway

_DURATION_RE = re.compile(
    r"\b(\d+)\s*(?:days?|nights?|d)\b|\b(\d+)\s*-\s*day\b",
    re.IGNORECASE,
)

_VIBE_WORDS = {
    "food": "food",
    "slow": "slow",
    "fast": "fast",
    "nature": "nature",
    "culture": "culture",
    "beach": "beach",
    "adventure": "adventure",
    "relax": "relax",
    "luxury": "luxury",
    "budget": "budget",
}


async def parse_intent(text: str, llm: LlmGateway) -> TripIntent | AskClarification:
    """Parse structured intent via dialogue LLM; heuristic fallback when unavailable."""
    raw = (text or "").strip()
    if not raw:
        return AskClarification(
            question="What trip are you planning? Include a place and how many days.",
            missing=("place", "duration"),
        )

    llm_intent = await _llm_parse(raw, llm)
    intent = llm_intent if isinstance(llm_intent, TripIntent) else _heuristic_parse(raw)

    if not intent.place_query.strip():
        return AskClarification(
            question="Which place, region, or country should we plan for?",
            missing=("place",),
        )
    if intent.duration_days is None or intent.duration_days <= 0:
        return AskClarification(
            question="How many days is the trip? I need a duration before we lock a scope.",
            missing=("duration",),
        )
    return intent


async def _llm_parse(text: str, llm: LlmGateway) -> TripIntent | None:
    messages = [
        {
            "role": "system",
            "content": (
                "Extract trip planning intent as JSON with keys: "
                "place_query (string), duration_days (int|null), vibe (string[]), "
                "constraints (string[]). Do not invent coordinates or venues."
            ),
        },
        {"role": "user", "content": text},
    ]
    try:
        result = await llm.complete("dialogue", messages, schema=INTENT_JSON_SCHEMA)
    except Exception:
        return None
    if isinstance(result, LlmUnavailable):
        return None
    data = _coerce_json(result)
    if data is None:
        return None
    duration = data.get("duration_days")
    try:
        duration_days = int(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration_days = None
    return TripIntent(
        place_query=str(data.get("place_query") or "").strip(),
        duration_days=duration_days,
        vibe=[str(v) for v in (data.get("vibe") or [])],
        constraints=[str(c) for c in (data.get("constraints") or [])],
        raw_text=text,
    )


def _heuristic_parse(text: str) -> TripIntent:
    """Deterministic fallback when LLM keys are missing — never invents hubs/coords."""
    duration_days = None
    match = _DURATION_RE.search(text)
    if match:
        duration_days = int(match.group(1) or match.group(2))

    vibe = [label for word, label in _VIBE_WORDS.items() if re.search(rf"\b{word}\b", text, re.I)]

    place = text
    place = _DURATION_RE.sub(" ", place)
    for word in _VIBE_WORDS:
        place = re.sub(rf"\b{word}\b", " ", place, flags=re.I)
    place = re.sub(r"\b(in|for|a|the|and|,)\b", " ", place, flags=re.I)
    place = re.sub(r"\s+", " ", place).strip(" .,!")

    return TripIntent(
        place_query=place or text.strip(),
        duration_days=duration_days,
        vibe=vibe,
        constraints=[],
        raw_text=text,
    )


def _coerce_json(result: Any) -> dict[str, Any] | None:
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            # Try fenced or trailing prose
            start = result.find("{")
            end = result.rfind("}")
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(result[start : end + 1])
                except json.JSONDecodeError:
                    return None
            else:
                return None
        return parsed if isinstance(parsed, dict) else None
    if hasattr(result, "content"):
        return _coerce_json(result.content)
    return None
