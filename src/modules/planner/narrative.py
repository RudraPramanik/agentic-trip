"""Narrative enrichment — titles/stories only; never adds place ids."""

from __future__ import annotations

from src.modules.llm.types import LlmUnavailable
from src.modules.planner.types import Itinerary
from src.ports import LlmGateway


async def write_narrative(itinerary: Itinerary, llm: LlmGateway) -> Itinerary:
    """Ask LLM for titles/stories keyed by existing days/stops. Preserve place ids.

    On LLM failure / unavailable: return the validated structure unchanged.
    """
    before = itinerary.stop_place_ids()
    payload = {
        "days": [
            {
                "day_index": d.day_index,
                "stops": [{"place_id": s.place_id, "name": s.name} for s in d.stops],
            }
            for d in itinerary.days
        ]
    }
    try:
        result = await llm.complete(
            role="narrative",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write short day titles and stories for an itinerary. "
                        "Do not add, remove, or rename place_ids. "
                        "Respond with JSON: "
                        '{"days":[{"day_index":1,"title":"...","story":"...",'
                        '"stops":[{"place_id":"...","title":"..."}]}]}'
                    ),
                },
                {"role": "user", "content": str(payload)},
            ],
            schema={"type": "object"},
        )
    except Exception:
        return itinerary

    if isinstance(result, LlmUnavailable) or result is None:
        return itinerary
    if isinstance(result, str):
        return itinerary
    if not isinstance(result, dict):
        return itinerary

    days_data = result.get("days")
    if not isinstance(days_data, list):
        return itinerary

    by_index = {
        int(d.get("day_index")): d
        for d in days_data
        if isinstance(d, dict) and d.get("day_index") is not None
    }
    for day in itinerary.days:
        meta = by_index.get(day.day_index)
        if not meta:
            continue
        if isinstance(meta.get("title"), str):
            day.title = meta["title"]
        if isinstance(meta.get("story"), str):
            day.story = meta["story"]
        stop_meta = {
            str(s.get("place_id")): s
            for s in (meta.get("stops") or [])
            if isinstance(s, dict) and s.get("place_id")
        }
        for stop in day.stops:
            sm = stop_meta.get(stop.place_id)
            if sm and isinstance(sm.get("title"), str):
                stop.title = sm["title"]

    after = itinerary.stop_place_ids()
    if after != before:
        for day in itinerary.days:
            day.stops = [s for s in day.stops if s.place_id in before]
        itinerary.place_ids = [s.place_id for d in itinerary.days for s in d.stops]
    return itinerary
