"""Lagged fruiting kernel.

Rain soaks the duff. Mycelium needs about a week. Nights decide whether
primordia actually push. Humidity keeps them from aborting.

The 14-day window is not a sum. Rain from 14–5 days ago carries the flush.
Yesterday's shower is too late.
"""

from __future__ import annotations

from datetime import date

import numpy as np

# Day 0 is 14 days ago, day 13 is yesterday.
RAIN_LAG = np.array(
    [0.90, 1.00, 1.00, 0.95, 0.85, 0.70, 0.55, 0.40, 0.28, 0.18, 0.12, 0.08, 0.05, 0.03],
    dtype=np.float64,
)
RAIN_LAG = RAIN_LAG / RAIN_LAG.sum()

NIGHT_OPTIMUM_C = 12.5
NIGHT_SIGMA_C = 3.2
RAIN_MID_MM = 22.0
RAIN_SCALE_MM = 7.0
RAIN_FLOOD_MM = 80.0
HUMIDITY_FLOOR = 58.0
HUMIDITY_SPAN = 22.0
AUTUMN_PEAK_DOY = 262
AUTUMN_SIGMA = 38.0
SPRING_PEAK_DOY = 110
SPRING_SIGMA = 18.0
URBAN_FACTOR = 0.55


def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


def season_gate(day_of_year: int) -> float:
    autumn = float(np.exp(-((day_of_year - AUTUMN_PEAK_DOY) ** 2) / (2 * AUTUMN_SIGMA**2)))
    spring = 0.35 * float(np.exp(-((day_of_year - SPRING_PEAK_DOY) ** 2) / (2 * SPRING_SIGMA**2)))
    return float(np.clip(autumn + spring, 0.0, 1.0))


def rain_score(precip_14: np.ndarray) -> tuple[float, float]:
    window = np.asarray(precip_14, dtype=np.float64)[-14:]
    if window.size < 14:
        window = np.pad(window, (14 - window.size, 0))
    effective = float(np.dot(window, RAIN_LAG) * 14.0)
    score = float(_sigmoid((effective - RAIN_MID_MM) / RAIN_SCALE_MM))
    if effective > RAIN_FLOOD_MM:
        score *= float(np.exp(-(effective - RAIN_FLOOD_MM) / 40.0))
    return float(np.clip(score, 0.0, 1.0)), effective


def night_score(tmin_7: np.ndarray) -> tuple[float, float]:
    nights = np.asarray(tmin_7, dtype=np.float64)[-7:]
    mean = float(np.mean(nights)) if nights.size else 0.0
    score = float(np.exp(-((mean - NIGHT_OPTIMUM_C) ** 2) / (2 * NIGHT_SIGMA_C**2)))
    return score, mean


def humidity_score(humidity_7: np.ndarray) -> tuple[float, float]:
    humidity = np.asarray(humidity_7, dtype=np.float64)[-7:]
    mean = float(np.mean(humidity)) if humidity.size else 0.0
    score = float(np.clip((mean - HUMIDITY_FLOOR) / HUMIDITY_SPAN, 0.0, 1.0))
    return score, mean


def boom_index(
    precip: np.ndarray,
    humidity: np.ndarray,
    tmin: np.ndarray,
    day_of_year: int,
    urban: bool = False,
) -> dict[str, float]:
    rain, rain_mm = rain_score(precip)
    nights, night_c = night_score(tmin)
    humid, humid_pct = humidity_score(humidity)
    season = season_gate(day_of_year)
    raw = (
        (rain**1.1)
        * (0.35 + 0.65 * nights)
        * (0.40 + 0.60 * humid)
        * (0.25 + 0.75 * season)
    )
    if urban:
        raw *= URBAN_FACTOR
    index = float(np.clip(raw * 100.0, 0.0, 100.0))
    return {
        "index": round(index, 1),
        "rain_mm": round(rain_mm, 1),
        "night_c": round(night_c, 1),
        "humidity": round(humid_pct, 1),
        "rain_score": round(rain, 3),
        "night_score": round(nights, 3),
        "humidity_score": round(humid, 3),
        "season": round(season, 3),
    }


def rolling_boom(
    precip: np.ndarray,
    humidity: np.ndarray,
    tmin: np.ndarray,
    start: date,
    urban: bool = False,
) -> np.ndarray:
    """Daily boom index for each day that has a 14-day lookback."""
    n = int(min(len(precip), len(humidity), len(tmin)))
    out = np.full(n, np.nan, dtype=np.float64)
    for i in range(13, n):
        doy = (start.toordinal() + i - date(start.year, 1, 1).toordinal()) % 366 + 1
        out[i] = boom_index(
            precip[i - 13 : i + 1],
            humidity[max(0, i - 6) : i + 1],
            tmin[max(0, i - 6) : i + 1],
            doy,
            urban=urban,
        )["index"]
    return out


def is_city_county(name: str) -> bool:
    rest = name.removeprefix("powiat ").strip()
    if not rest:
        return False
    lowered = rest.casefold()
    if lowered.endswith(("ski", "cki", "dzki")):
        return False
    return rest[:1].isupper()
