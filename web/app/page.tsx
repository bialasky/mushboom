"use client";

import { useEffect, useMemo, useState } from "react";
import { PolandMap } from "./components/PolandMap";
import { SpecimenCard } from "./components/SpecimenCard";
import { HEAT_CSS } from "./lib/color";
import type { County, ForecastSnapshot, GeoJSON, ViewMode } from "./lib/types";

const MODES: Array<{ id: ViewMode; label: string }> = [
  { id: "boom", label: "Boom" },
  { id: "timesfm", label: "TimesFM" },
  { id: "grzyby", label: "grzyby.pl" },
  { id: "compare", label: "Compare" },
];

export default function Page() {
  const [geo, setGeo] = useState<GeoJSON | null>(null);
  const [snapshot, setSnapshot] = useState<ForecastSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<ViewMode>("boom");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [dayOffset, setDayOffset] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function loadGeo() {
      const response = await fetch("/api/geo/powiaty");
      if (!response.ok) throw new Error("GeoJSON failed");
      const payload = (await response.json()) as GeoJSON;
      if (!cancelled) setGeo(payload);
    }
    loadGeo().catch((err: Error) => {
      if (!cancelled) setError(err.message);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadForecast() {
      const response = await fetch("/api/forecast", { cache: "no-store" });
      if (!response.ok) throw new Error("Forecast failed");
      const payload = (await response.json()) as ForecastSnapshot;
      if (!cancelled) setSnapshot(payload);
      return payload;
    }
    loadForecast()
      .then((payload) => {
        if (payload.model.timesfm_pending) {
          window.setTimeout(() => {
            if (!cancelled) {
              void loadForecast();
            }
          }, 8000);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const counties = useMemo(() => {
    const map = new Map<number, County>();
    snapshot?.counties.forEach((county) => map.set(county.id, county));
    return map;
  }, [snapshot]);

  const selected = selectedId == null ? null : (counties.get(selectedId) ?? null);
  const hot = snapshot
    ? [...snapshot.counties].sort((a, b) => b.boom_now - a.boom_now)[0]
    : null;
  const calendar = snapshot?.counties[0]?.days ?? [];
  const picked = calendar.find((day) => day.offset === dayOffset) ?? calendar[0];

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          mush<span>boom</span>
        </div>
        <p className="meta">
          {picked
            ? `${picked.offset === 0 ? "Today" : picked.weekday} ${picked.date}`
            : "pick a day"}
          {" · "}
          {snapshot?.counties.length ?? "…"} powiaty
        </p>
      </header>

      <main className="stage">
        <div className="map-wrap">
          <PolandMap
            geo={geo}
            counties={counties}
            mode={mode}
            dayOffset={dayOffset}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          {!snapshot && !error ? <p className="loading">Reading the duff…</p> : null}
          {error ? <p className="loading">{error}. Is the forecast API on :8000?</p> : null}
        </div>
        <div className="side">
          <SpecimenCard
            county={selected ?? hot ?? null}
            mode={mode}
            dayOffset={dayOffset}
            onPickDay={setDayOffset}
          />
        </div>
      </main>

      <footer className="bottombar">
        <div className="daystrip footer-days" role="tablist" aria-label="Forecast day">
          {calendar.map((day) => (
            <button
              key={day.date}
              type="button"
              role="tab"
              className={day.offset === dayOffset ? "is-on" : undefined}
              onClick={() => setDayOffset(day.offset)}
            >
              <span>{day.offset === 0 ? "Today" : day.weekday}</span>
            </button>
          ))}
        </div>
        <div className="modes">
          {MODES.map((item) => (
            <button
              key={item.id}
              className={item.id === mode ? "is-on" : undefined}
              onClick={() => setMode(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="legend">
          {legendFor(mode)}
        </div>
        <p className="note">
          {snapshot?.grzyby.ok
            ? `${snapshot.grzyby.report_total} grzyby.pl reports. Comparison only.`
            : "grzyby.pl overlay pending."}{" "}
          {snapshot?.model.timesfm
            ? `TimesFM ${snapshot.model.timesfm} on ${snapshot.model.timesfm_device}.`
            : snapshot?.model.timesfm_pending
              ? "TimesFM 3.0 still loading."
              : snapshot?.model.timesfm_error && snapshot.model.timesfm_error !== "not loaded"
                ? "TimesFM unavailable — kernel only."
                : ""}
        </p>
      </footer>
    </div>
  );
}

function legendFor(mode: ViewMode) {
  switch (mode) {
    case "compare":
      return (
        <>
          <span className="swatch">
            <i style={{ background: "#C00000" }} />
            both
          </span>
          <span className="swatch">
            <i style={{ background: "#FF7800" }} />
            weather only
          </span>
          <span className="swatch">
            <i style={{ background: "#00D0C8" }} />
            reports only
          </span>
          <span className="swatch">
            <i style={{ background: "#000098" }} />
            quiet
          </span>
        </>
      );
    case "grzyby":
    case "boom":
    case "timesfm":
      return (
        <span className="heatbar">
          0
          <b style={{ background: HEAT_CSS }} />
          100
        </span>
      );
    default: {
      const _never: never = mode;
      return _never;
    }
  }
}
