"""Powiat centroids and voivodeship membership."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _centroid(geom: dict[str, Any]) -> tuple[float, float]:
    rings: list[list[list[float]]] = []
    if geom["type"] == "Polygon":
        rings.append(geom["coordinates"][0])
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            rings.append(poly[0])
    else:
        return 19.0, 52.0
    xs: list[float] = []
    ys: list[float] = []
    for ring in rings:
        for pt in ring:
            xs.append(float(pt[0]))
            ys.append(float(pt[1]))
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _point_in_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i, pt in enumerate(ring):
        xi, yi = float(pt[0]), float(pt[1])
        xj, yj = float(ring[j][0]), float(ring[j][1])
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-18) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _point_in_geom(x: float, y: float, geom: dict[str, Any]) -> bool:
    if geom["type"] == "Polygon":
        rings = geom["coordinates"]
        if not _point_in_ring(x, y, rings[0]):
            return False
        return not any(_point_in_ring(x, y, hole) for hole in rings[1:])
    if geom["type"] == "MultiPolygon":
        return any(
            _point_in_geom(x, y, {"type": "Polygon", "coordinates": poly})
            for poly in geom["coordinates"]
        )
    return False


@lru_cache(maxsize=1)
def load_voivodeships() -> list[dict[str, Any]]:
    raw = json.loads((DATA_DIR / "wojewodztwa.geojson").read_text())
    return [
        {"name": feat["properties"]["nazwa"], "geometry": feat["geometry"]}
        for feat in raw["features"]
    ]


def assign_voivodeship(lon: float, lat: float) -> str:
    for woj in load_voivodeships():
        if _point_in_geom(lon, lat, woj["geometry"]):
            return str(woj["name"])
    nearest = min(
        load_voivodeships(),
        key=lambda woj: (lon - _centroid(woj["geometry"])[0]) ** 2
        + (lat - _centroid(woj["geometry"])[1]) ** 2,
    )
    return str(nearest["name"])


@lru_cache(maxsize=1)
def load_counties() -> list[dict[str, Any]]:
    raw = json.loads((DATA_DIR / "powiaty.geojson").read_text())
    counties: list[dict[str, Any]] = []
    for feat in raw["features"]:
        name = str(feat["properties"]["nazwa"])
        county_id = int(feat["properties"]["id"])
        lon, lat = _centroid(feat["geometry"])
        counties.append(
            {
                "id": county_id,
                "name": name,
                "lon": round(lon, 4),
                "lat": round(lat, 4),
                "woj": assign_voivodeship(lon, lat),
            }
        )
    return counties


def powiaty_geojson() -> dict[str, Any]:
    return json.loads((DATA_DIR / "powiaty.geojson").read_text())
