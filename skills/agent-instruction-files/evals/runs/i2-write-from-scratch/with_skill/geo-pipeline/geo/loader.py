"""Load boundary files.

Coordinate order is (lon, lat) everywhere in this codebase, as in GeoJSON.
Two production incidents came from code that assumed (lat, lon). Do not swap.
"""


def load_point(lon: float, lat: float) -> tuple[float, float]:
    return (lon, lat)
