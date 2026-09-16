"""Open-Meteo daily weather for every Polish county."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import httpx
import numpy as np

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY = "precipitation_sum,temperature_2m_min,relative_humidity_2m_mean"
PAST_DAYS = 32
FORECAST_DAYS = 14
BATCH = 8
MAX_RETRIES = 6


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    return [payload]


def _series(block: dict[str, Any]) -> dict[str, Any]:
    daily = block.get("daily") or {}
    times = [date.fromisoformat(t) for t in daily.get("time") or []]
    precip = np.array(daily.get("precipitation_sum") or [], dtype=np.float64)
    tmin = np.array(daily.get("temperature_2m_min") or [], dtype=np.float64)
    humidity = np.array(daily.get("relative_humidity_2m_mean") or [], dtype=np.float64)
    today = date.today()
    split = 0
    for i, day in enumerate(times):
        if day <= today:
            split = i + 1
    return {
        "dates": times,
        "precip": precip,
        "tmin": tmin,
        "humidity": humidity,
        "history_end": split,
        "today": today,
    }


async def _fetch_batch(
    client: httpx.AsyncClient,
    lats: list[float],
    lons: list[float],
) -> list[dict[str, Any]]:
    params = {
        "latitude": ",".join(f"{lat:.4f}" for lat in lats),
        "longitude": ",".join(f"{lon:.4f}" for lon in lons),
        "daily": DAILY,
        "past_days": PAST_DAYS,
        "forecast_days": FORECAST_DAYS,
        "timezone": "Europe/Warsaw",
    }
    delay = 1.0
    last_error: Exception | None = None
    for _attempt in range(MAX_RETRIES):
        response = await client.get(FORECAST_URL, params=params, timeout=60.0)
        if response.status_code == 429:
            last_error = httpx.HTTPStatusError("429", request=response.request, response=response)
            await asyncio.sleep(delay)
            delay = min(delay * 1.8, 20.0)
            continue
        response.raise_for_status()
        return _as_list(response.json())
    if last_error:
        raise last_error
    raise RuntimeError("Open-Meteo request failed")


async def fetch_county_weather(counties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [None] * len(counties)  # type: ignore[list-item]
    async with httpx.AsyncClient(headers={"User-Agent": "mushboom/0.1 (research)"}) as client:
        for start in range(0, len(counties), BATCH):
            chunk = counties[start : start + BATCH]
            rows = await _fetch_batch(
                client,
                [c["lat"] for c in chunk],
                [c["lon"] for c in chunk],
            )
            if len(rows) != len(chunk):
                raise RuntimeError(f"Open-Meteo returned {len(rows)} rows for {len(chunk)} counties")
            for offset, row in enumerate(rows):
                out[start + offset] = _series(row)
            if start + BATCH < len(counties):
                await asyncio.sleep(0.45)
    return out


def window_ending(series: dict[str, Any], end_index: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lo = max(0, end_index - 13)
    precip = series["precip"][lo : end_index + 1]
    humidity = series["humidity"][max(0, end_index - 6) : end_index + 1]
    tmin = series["tmin"][max(0, end_index - 6) : end_index + 1]
    return precip, humidity, tmin


def forecast_horizon_end(series: dict[str, Any], days_ahead: int) -> int:
    last = len(series["dates"]) - 1
    return min(series["history_end"] - 1 + days_ahead, last)
