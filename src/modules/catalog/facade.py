from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from src.modules.catalog.adapters.overpass import OtmAdapter, OverpassAdapter
from src.modules.catalog.models import PlaceRecord


@dataclass
class FetchResult:
    places: list[PlaceRecord] = field(default_factory=list)
    partial: bool = False
    errors: list[str] = field(default_factory=list)


class PlacesFacade(Protocol):
    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult: ...


def _bboxes_for_scope(scope: dict[str, Any]) -> list[list[float]]:
    """Region/hub polygons only — never invent a country-centroid radius."""
    boxes: list[list[float]] = []
    hubs = scope.get("hubs") or []
    for hub in hubs:
        if isinstance(hub, dict) and hub.get("bbox") and len(hub["bbox"]) == 4:
            boxes.append([float(x) for x in hub["bbox"]])
    bbox = scope.get("bbox")
    if bbox and len(bbox) == 4:
        boxes.append([float(x) for x in bbox])
    # Dedupe identical boxes
    unique: list[list[float]] = []
    seen: set[tuple[float, ...]] = set()
    for b in boxes:
        key = tuple(b)
        if key not in seen:
            seen.add(key)
            unique.append(b)
    return unique


def _dedupe(places: list[PlaceRecord]) -> list[PlaceRecord]:
    by_provider: dict[tuple[str, str], PlaceRecord] = {}
    by_name_coord: dict[tuple[str, int, int], PlaceRecord] = {}
    out: list[PlaceRecord] = []
    for p in places:
        pk = (p.provider, p.provider_id)
        if pk in by_provider:
            continue
        nk = (p.name.lower(), int(p.lon * 1000), int(p.lat * 1000))
        if nk in by_name_coord:
            continue
        by_provider[pk] = p
        by_name_coord[nk] = p
        out.append(p)
    return out


class DefaultPlacesFacade:
    def __init__(
        self,
        overpass: OverpassAdapter | None = None,
        otm: OtmAdapter | None = None,
    ) -> None:
        self._overpass = overpass or OverpassAdapter()
        self._otm = otm or OtmAdapter()

    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        boxes = _bboxes_for_scope(scope)
        if not boxes:
            return FetchResult(places=[], partial=False, errors=["no_bbox"])
        country = scope.get("country_code")
        collected: list[PlaceRecord] = []
        errors: list[str] = []
        overpass_ok = False
        otm_ok = False
        for bbox in boxes:
            try:
                op = self._overpass.fetch_bbox(bbox, country)
                collected.extend(op)
                overpass_ok = True
            except Exception as exc:  # noqa: BLE001 — fail-soft
                errors.append(f"overpass:{exc}")
            try:
                ot = self._otm.fetch_bbox(bbox, country)
                collected.extend(ot)
                otm_ok = True
            except Exception as exc:  # noqa: BLE001
                errors.append(f"otm:{exc}")
        # Adapters already fail-soft to []; treat "both empty with errors" as partial.
        partial = bool(errors) or (overpass_ok and not otm_ok) or (otm_ok and not overpass_ok)
        # If both adapters returned without raising but one is unconfigured empty,
        # still ok — not partial unless one raised.
        if not errors:
            partial = False
        return FetchResult(places=_dedupe(collected), partial=partial, errors=errors)
