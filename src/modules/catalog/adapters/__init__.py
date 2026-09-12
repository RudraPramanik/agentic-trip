# Re-export adapters from package path expected by design.
from src.modules.catalog.adapters.overpass import OtmAdapter, OverpassAdapter

__all__ = ["OverpassAdapter", "OtmAdapter"]
