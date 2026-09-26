"""Build a cached county forecast snapshot."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from mushboom.daily import snapshot_is_fresh
from mushboom.geography import load_counties
from mushboom.grzyby import fetch_grzyby, intensity_for_county
from mushboom.phenology import boom_index, is_city_county, rolling_boom
from mushboom.timesfm_engine import HORIZON, TimesFMEngine, aggregate_series
from mushboom.weather import fetch_county_weather, forecast_horizon_end, window_ending

DAY_HORIZON = 7
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "cache" / "snapshot.json"

_lock = asyncio.Lock()
_engine: TimesFMEngine | None = None
_engine_loaded = False
snapshot_ready = asyncio.Event()
snapshot_failed = asyncio.Event()


def _get_engine(load: bool) -> TimesFMEngine:
    global _engine, _engine_loaded
    if _engine is None:
        _engine = TimesFMEngine()
    if load and not _engine_loaded:
        _engine.load()
        _engine_loaded = True
    return _engine


def read_cached_snapshot() -> dict[str, Any] | None:
    """Return the stored snapshot. An older file is still served."""
    if not CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(CACHE_PATH.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    stamp = payload.get("generated_at")
    if not isinstance(stamp, str) or not stamp:
        return None
    counties = payload.get("counties") or []
    if not counties or "days" not in counties[0]:
        return None
    return payload


def _write_cache(payload: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = CACHE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False))
    temporary.replace(CACHE_PATH)
    snapshot_ready.set()


def _kernel_at(series: dict[str, Any], end: int, urban: bool) -> dict[str, float]:
    precip, humidity, tmin = window_ending(series, end)
    doy = series["dates"][end].timetuple().tm_yday
    return boom_index(precip, humidity, tmin, doy, urban=urban)


def _daily_kernel(series: dict[str, Any], urban: bool) -> list[dict[str, Any]]:
    days: list[dict[str, Any]] = []
    for offset in range(DAY_HORIZON + 1):
        end = forecast_horizon_end(series, offset)
        kernel = _kernel_at(series, end, urban)
        day = series["dates"][end]
        days.append(
            {
                "offset": offset,
                "date": day.isoformat(),
                "weekday": WEEKDAYS[day.weekday()],
                "boom": kernel["index"],
                "timesfm": None,
                "precip_14d": kernel["rain_mm"],
                "nights_7d": kernel["night_c"],
                "humidity_7d": kernel["humidity"],
            }
        )
    return days


def _timesfm_daily(
    precip: np.ndarray,
    humidity: np.ndarray,
    tmin: np.ndarray,
    start: Any,
    forecast_p: np.ndarray,
    forecast_h: np.ndarray,
    forecast_t: np.ndarray,
) -> list[float]:
    full_p = np.concatenate([precip, forecast_p])
    full_h = np.concatenate([humidity, forecast_h])
    full_t = np.concatenate([tmin, forecast_t])
    today_idx = len(precip) - 1
    out: list[float] = []
    for offset in range(DAY_HORIZON + 1):
        end = min(today_idx + offset, len(full_p) - 1)
        day = start + timedelta(days=offset) if isinstance(start, date) else start
        doy = day.timetuple().tm_yday if hasattr(day, "timetuple") else 260
        score = boom_index(
            full_p[max(0, end - 13) : end + 1],
            full_h[max(0, end - 6) : end + 1],
            full_t[max(0, end - 6) : end + 1],
            doy,
            urban=False,
        )
        out.append(score["index"])
    return out


async def build_snapshot() -> dict[str, Any]:
    async with _lock:
        cached = read_cached_snapshot()
        if cached is not None and snapshot_is_fresh(cached):
            snapshot_ready.set()
            return cached

        counties = load_counties()
        weather_task = asyncio.create_task(fetch_county_weather(counties))
        grzyby_task = asyncio.create_task(fetch_grzyby())
        weather_rows, grzyby = await asyncio.gather(weather_task, grzyby_task)

        engine = _get_engine(load=True)
        by_woj: dict[str, list[int]] = defaultdict(list)
        for idx, county in enumerate(counties):
            by_woj[county["woj"]].append(idx)

        timesfm_woj: dict[str, dict[str, Any]] = {}
        if engine.status.available:
            for woj, indexes in by_woj.items():
                history_end = weather_rows[indexes[0]]["history_end"]
                agg = aggregate_series(weather_rows, indexes)
                forecast = engine.forecast_weather(
                    agg["precip"][:history_end],
                    agg["humidity"][:history_end],
                    agg["tmin"][:history_end],
                )
                if forecast is None:
                    continue
                today = weather_rows[indexes[0]]["dates"][max(history_end - 1, 0)]
                tf_days = _timesfm_daily(
                    agg["precip"][:history_end],
                    agg["humidity"][:history_end],
                    agg["tmin"][:history_end],
                    today,
                    forecast["precip"][:HORIZON],
                    forecast["humidity"][:HORIZON],
                    forecast["tmin"][:HORIZON],
                )
                timesfm_woj[woj] = {
                    "days": tf_days,
                    "now": tf_days[0],
                    "plus7": tf_days[min(7, len(tf_days) - 1)],
                }

        kernel_woj_days: dict[str, list[list[float]]] = defaultdict(list)
        drafted: list[dict[str, Any]] = []
        for county, series in zip(counties, weather_rows, strict=True):
            urban = is_city_county(county["name"])
            days = _daily_kernel(series, urban)
            now = days[0]
            plus7 = days[min(7, len(days) - 1)]
            kernel_woj_days[county["woj"]].append([day["boom"] for day in days])
            drafted.append(
                {
                    "county": county,
                    "series": series,
                    "urban": urban,
                    "days": days,
                    "now": now,
                    "plus7": plus7,
                }
            )

        rows: list[dict[str, Any]] = []
        for item in drafted:
            county = item["county"]
            series = item["series"]
            days = item["days"]
            now = item["now"]
            plus7 = item["plus7"]
            urban = item["urban"]
            tf = timesfm_woj.get(county["woj"])
            timesfm_now = timesfm_plus7 = None
            if tf is not None:
                woj_days = np.mean(np.array(kernel_woj_days[county["woj"]], dtype=np.float64), axis=0)
                tf_days = tf["days"]
                for index, day in enumerate(days):
                    woj_mean = float(woj_days[index]) if index < len(woj_days) else 8.0
                    tf_value = tf_days[index] if index < len(tf_days) else tf_days[-1]
                    day["timesfm"] = round(
                        float(np.clip(day["boom"] * (tf_value / max(woj_mean, 8.0)), 0, 100)),
                        1,
                    )
                timesfm_now = days[0]["timesfm"]
                timesfm_plus7 = days[min(7, len(days) - 1)]["timesfm"]
            reports = intensity_for_county(county["name"], county["woj"], grzyby)
            history = rolling_boom(
                series["precip"][: series["history_end"]],
                series["humidity"][: series["history_end"]],
                series["tmin"][: series["history_end"]],
                series["dates"][0],
                urban=urban,
            )
            rows.append(
                {
                    **county,
                    "urban": urban,
                    "boom_now": now["boom"],
                    "boom_plus7": plus7["boom"],
                    "precip_14d": now["precip_14d"],
                    "humidity_7d": now["humidity_7d"],
                    "nights_7d": now["nights_7d"],
                    "days": days,
                    "timesfm_now": timesfm_now,
                    "timesfm_plus7": timesfm_plus7,
                    "grzyby_reports": reports["reports"],
                    "grzyby_woj_reports": reports["woj_reports"],
                    "grzyby_intensity": reports["intensity"],
                    "history_tail": [
                        None if bool(np.isnan(v)) else round(float(v), 1) for v in history[-21:]
                    ],
                }
            )

        payload = {
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "model": {
                "kernel": "phenology-v1",
                "timesfm": "3.0" if engine.status.available else None,
                "timesfm_device": engine.status.device,
                "timesfm_error": engine.status.error,
                "timesfm_scope": "voivodeship weather, county kernel" if engine.status.available else None,
                "timesfm_pending": not engine.status.available and engine.status.error == "not loaded",
                "license": engine.status.license,
            },
            "grzyby": {
                "ok": grzyby.get("ok"),
                "source": grzyby.get("source"),
                "url": grzyby.get("url"),
                "fetched_at": grzyby.get("fetched_at"),
                "by_woj": grzyby.get("by_woj"),
                "report_total": grzyby.get("report_total"),
                "note": grzyby.get("note"),
                "error": grzyby.get("error"),
            },
            "counties": rows,
        }
        _write_cache(payload)
        return payload
