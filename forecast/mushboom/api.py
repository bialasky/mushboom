from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from mushboom.geography import powiaty_geojson
from mushboom.pipeline import build_snapshot

app = FastAPI(title="mushboom", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/forecast")
async def forecast(refresh: bool = Query(default=False)) -> dict[str, Any]:
    return await build_snapshot(force=refresh)


@app.get("/geo/powiaty")
async def geo_powiaty() -> dict[str, Any]:
    return powiaty_geojson()
