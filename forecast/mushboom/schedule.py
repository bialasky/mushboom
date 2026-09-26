"""Background loop that rebuilds the forecast snapshot every morning."""

from __future__ import annotations

import asyncio
import logging

from mushboom import pipeline
from mushboom.daily import seconds_until_next_refresh, snapshot_is_fresh

RETRY_SECONDS = 15 * 60

logger = logging.getLogger("mushboom")


def _configure_logging() -> None:
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


async def daily_refresh_loop() -> None:
    _configure_logging()
    while True:
        try:
            cached = pipeline.read_cached_snapshot()
            if snapshot_is_fresh(cached):
                delay = seconds_until_next_refresh()
                logger.info("forecast snapshot is current; next refresh in %.0f min", delay / 60)
                await asyncio.sleep(delay)
                continue
            logger.info("building daily forecast snapshot")
            pipeline.snapshot_failed.clear()
            await pipeline.build_snapshot()
            logger.info("daily forecast snapshot ready")
        except asyncio.CancelledError:
            raise
        except Exception:
            pipeline.snapshot_failed.set()
            logger.exception("daily forecast refresh failed; retrying in %s min", RETRY_SECONDS // 60)
            await asyncio.sleep(RETRY_SECONDS)
