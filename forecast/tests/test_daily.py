"""Daily snapshot schedule. No weather calls."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from mushboom import api, pipeline
from mushboom.daily import (
    WARSAW,
    last_refresh_at,
    next_refresh_at,
    seconds_until_next_refresh,
    snapshot_is_fresh,
)
from mushboom.schedule import daily_refresh_loop

UTC = ZoneInfo("UTC")


def _at(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=WARSAW)


class DailyClockTests(unittest.TestCase):
    def test_before_six_uses_yesterday(self) -> None:
        now = _at(2026, 9, 26, 5, 30)
        self.assertEqual(last_refresh_at(now), _at(2026, 9, 25, 6))
        self.assertEqual(next_refresh_at(now), _at(2026, 9, 26, 6))
        self.assertEqual(seconds_until_next_refresh(now), 30 * 60)

    def test_at_and_after_six_uses_today(self) -> None:
        at_six = _at(2026, 9, 26, 6)
        afternoon = _at(2026, 9, 26, 18)
        self.assertEqual(last_refresh_at(at_six), at_six)
        self.assertEqual(next_refresh_at(at_six), _at(2026, 9, 27, 6))
        self.assertEqual(seconds_until_next_refresh(at_six), 24 * 60 * 60)
        self.assertEqual(last_refresh_at(afternoon), at_six)
        self.assertEqual(seconds_until_next_refresh(afternoon), 12 * 60 * 60)

    def test_six_am_stays_on_the_clock_across_dst(self) -> None:
        before_spring = _at(2026, 3, 28, 7)
        after_spring = next_refresh_at(before_spring)
        self.assertEqual(after_spring.hour, 6)
        self.assertEqual(after_spring.date().isoformat(), "2026-03-29")

        before_fall = _at(2026, 10, 24, 8)
        after_fall = next_refresh_at(before_fall)
        self.assertEqual(after_fall.hour, 6)
        self.assertEqual(after_fall.date().isoformat(), "2026-10-25")
        following = next_refresh_at(after_fall + timedelta(hours=2))
        self.assertEqual(following.hour, 6)
        self.assertEqual(following.date().isoformat(), "2026-10-26")

    def test_morning_snapshot_stays_fresh_until_next_morning(self) -> None:
        payload = {"generated_at": _at(2026, 9, 26, 6, 5).isoformat()}
        self.assertTrue(snapshot_is_fresh(payload, _at(2026, 9, 26, 18)))
        self.assertTrue(snapshot_is_fresh(payload, _at(2026, 9, 27, 5, 59)))
        self.assertFalse(snapshot_is_fresh(payload, _at(2026, 9, 27, 6)))

    def test_snapshot_from_before_six_is_stale_after_six(self) -> None:
        payload = {"generated_at": _at(2026, 9, 26, 5, 50).isoformat()}
        self.assertFalse(snapshot_is_fresh(payload, _at(2026, 9, 26, 6, 1)))


class ForecastReadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._original = pipeline.CACHE_PATH
        pipeline.CACHE_PATH = Path(self._tmpdir.name) / "snapshot.json"
        pipeline.snapshot_ready = asyncio.Event()
        pipeline.snapshot_failed = asyncio.Event()

    def tearDown(self) -> None:
        pipeline.CACHE_PATH = self._original
        pipeline.snapshot_ready.clear()
        pipeline.snapshot_failed.clear()
        self._tmpdir.cleanup()

    def _write(self, generated: datetime) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "generated_at": generated.isoformat(),
            "counties": [{"id": 1, "days": []}],
        }
        pipeline.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        pipeline.CACHE_PATH.write_text(json.dumps(payload))
        return payload

    async def test_forecast_returns_stale_snapshot_without_fetching(self) -> None:
        payload = self._write(datetime(2026, 9, 24, 6, 5, tzinfo=WARSAW))
        now = datetime(2026, 9, 26, 12, tzinfo=WARSAW)
        self.assertFalse(snapshot_is_fresh(payload, now))

        with patch("mushboom.pipeline.fetch_county_weather", new=AsyncMock(side_effect=AssertionError("fetch"))):
            result = await api.forecast()

        self.assertEqual(result["generated_at"], payload["generated_at"])
        self.assertEqual(result["counties"], payload["counties"])

    async def test_fresh_snapshot_skips_weather_fetch(self) -> None:
        payload = self._write(datetime.now(UTC))
        with patch("mushboom.pipeline.fetch_county_weather", new=AsyncMock(side_effect=AssertionError("fetch"))):
            result = await pipeline.build_snapshot()
        self.assertEqual(result["generated_at"], payload["generated_at"])

    async def test_missing_snapshot_returns_503(self) -> None:
        with (
            patch.object(api, "SNAPSHOT_WAIT_SECONDS", 0.05),
            self.assertRaises(HTTPException) as caught,
        ):
            await api.forecast()
        self.assertEqual(caught.exception.status_code, 503)

    async def test_failed_build_returns_503_without_the_full_wait(self) -> None:
        pipeline.snapshot_failed.set()
        started = asyncio.get_running_loop().time()
        with (
            patch.object(api, "SNAPSHOT_WAIT_SECONDS", 30),
            self.assertRaises(HTTPException) as caught,
        ):
            await api.forecast()
        self.assertEqual(caught.exception.status_code, 503)
        self.assertLess(asyncio.get_running_loop().time() - started, 1)

    async def test_loop_sleeps_until_morning_when_snapshot_is_fresh(self) -> None:
        self._write(datetime.now(UTC))

        async def stop_after_schedule(delay: float) -> None:
            self.assertGreater(delay, 0)
            raise asyncio.CancelledError

        with (
            patch("mushboom.pipeline.build_snapshot", new=AsyncMock(side_effect=AssertionError("build"))),
            patch("mushboom.schedule.asyncio.sleep", new=stop_after_schedule),
            self.assertRaises(asyncio.CancelledError),
        ):
            await daily_refresh_loop()


if __name__ == "__main__":
    unittest.main()
