"""Planner package — TravelEngine, matrix, validate, narrative."""

from src.modules.planner.engine import GreedyTravelEngine, pack_days
from src.modules.planner.matrix import haversine_meters, travel_matrix
from src.modules.planner.narrative import write_narrative
from src.modules.planner.types import Day, Itinerary, Stop, ValidateResult
from src.modules.planner.validate import validate_itinerary

__all__ = [
    "Day",
    "GreedyTravelEngine",
    "Itinerary",
    "Stop",
    "ValidateResult",
    "haversine_meters",
    "pack_days",
    "travel_matrix",
    "validate_itinerary",
    "write_narrative",
]
