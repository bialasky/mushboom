"""When the daily forecast snapshot is due.

The snapshot is rebuilt once a day at 06:00 Europe/Warsaw. A visit never
starts that work.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")
REFRESH_HOUR = 6


def _warsaw(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(WARSAW)
    if now.tzinfo is None:
        return now.replace(tzinfo=WARSAW)
    return now.astimezone(WARSAW)


def _at_refresh_hour(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, REFRESH_HOUR, 0, 0, tzinfo=WARSAW)


def last_refresh_at(now: datetime | None = None) -> datetime:
    local = _warsaw(now)
    slot = _at_refresh_hour(local.date())
    if local < slot:
        return _at_refresh_hour(local.date() - timedelta(days=1))
    return slot


def next_refresh_at(now: datetime | None = None) -> datetime:
    local = _warsaw(now)
    slot = _at_refresh_hour(local.date())
    if local >= slot:
        return _at_refresh_hour(local.date() + timedelta(days=1))
    return slot


def seconds_until_next_refresh(now: datetime | None = None) -> float:
    local = _warsaw(now)
    return max(0.0, (next_refresh_at(local) - local).total_seconds())


def snapshot_is_fresh(payload: dict[str, Any] | None, now: datetime | None = None) -> bool:
    if not payload:
        return False
    stamp = payload.get("generated_at")
    if not isinstance(stamp, str) or not stamp:
        return False
    try:
        generated = datetime.fromisoformat(stamp)
    except ValueError:
        return False
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=UTC)
    return generated >= last_refresh_at(now)
