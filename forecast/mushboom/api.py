from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from mushboom import pipeline
from mushboom.geography import powiaty_geojson
from mushboom.schedule import daily_refresh_loop

SNAPSHOT_WAIT_SECONDS = 90


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(daily_refresh_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="mushboom", version="0.1.0", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://mushboom.bialasky.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/forecast")
async def forecast() -> dict[str, Any]:
    cached = pipeline.read_cached_snapshot()
    if cached is not None:
        return cached
    ready = asyncio.create_task(pipeline.snapshot_ready.wait())
    failed = asyncio.create_task(pipeline.snapshot_failed.wait())
    try:
        await asyncio.wait(
            {ready, failed},
            timeout=SNAPSHOT_WAIT_SECONDS,
            return_when=asyncio.FIRST_COMPLETED,
        )
    finally:
        ready.cancel()
        failed.cancel()
        with suppress(asyncio.CancelledError):
            await ready
        with suppress(asyncio.CancelledError):
            await failed
    cached = pipeline.read_cached_snapshot()
    if cached is None:
        raise HTTPException(status_code=503, detail="Forecast is still building")
    return cached


@app.get("/geo/powiaty")
async def geo_powiaty() -> dict[str, Any]:
    return powiaty_geojson()
