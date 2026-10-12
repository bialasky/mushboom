"use client";

import type { CSSProperties } from "react";
import { DropIcon, ForestPhoto, NightIcon, RainIcon } from "./art";
import { agreementOf, dayAt, heatFill } from "../lib/color";
import type { County, DayScore, ViewMode } from "../lib/types";

const AGREEMENT_LABEL = {
  confirmed: "conditions + reports",
  predicted: "conditions, quiet reports",
  reported: "reports, weak weather",
  quiet: "quiet",
} as const;

type Props = {
  county: County | null;
  mode: ViewMode;
  dayOffset: number;
  onPickDay: (offset: number) => void;
};

export function SpecimenCard({ county, mode, dayOffset, onPickDay }: Props) {
  if (!county) {
    return (
      <aside className="card">
        <figure className="still-photo">
          <ForestPhoto />
        </figure>
        <p className="empty">Pick a day, then a powiat. Each tile is that weekday’s flush score — not a 7-day blur.</p>
      </aside>
    );
  }

  const day = dayAt(county, dayOffset);
  const agreement = agreementOf(county, dayOffset);
  const headline = headlineFor(mode, county, day);
  const rain = day?.precip_14d ?? county.precip_14d;
  const nights = day?.nights_7d ?? county.nights_7d;
  const humidity = day?.humidity_7d ?? county.humidity_7d;
  const boom = day?.boom ?? county.boom_now;
  const timesfm = day?.timesfm ?? county.timesfm_plus7;

  const words = headline.value.length > 4;

  return (
    <aside className="card" style={{ "--plate": heatFill(boom) } as CSSProperties}>
      <div className="kicker">
        <p className="woj">{county.woj}</p>
        <span className="plate-no">№ {String(county.id).padStart(4, "0")}</span>
      </div>
      <div className="identity">
        <div>
          <h2>{county.name}</h2>
          <div className={words ? "score score-words" : "score"}>
            <b>{headline.value}</b>
            <small>{headline.unit}</small>
          </div>
        </div>
        <figure className="still-photo">
          <ForestPhoto />
        </figure>
      </div>
      <DayStrip county={county} dayOffset={dayOffset} mode={mode} onPickDay={onPickDay} />
      <Spark values={county.history_tail} />
      <dl className="stats">
        <div>
          <dt>
            <RainIcon />
            14-day rain
          </dt>
          <dd>{rain.toFixed(0)} mm</dd>
        </div>
        <div>
          <dt>
            <NightIcon />
            Nights, 7d
          </dt>
          <dd>{nights.toFixed(1)} °C</dd>
        </div>
        <div>
          <dt>
            <DropIcon />
            Humidity, 7d
          </dt>
          <dd>{humidity.toFixed(0)}%</dd>
        </div>
        <div>
          <dt>Boom this day</dt>
          <dd>{boom.toFixed(0)}</dd>
        </div>
        <div>
          <dt>TimesFM this day</dt>
          <dd>{timesfm == null ? "—" : timesfm.toFixed(0)}</dd>
        </div>
        <div>
          <dt>grzyby.pl</dt>
          <dd>
            {county.grzyby_reports} local / {county.grzyby_woj_reports} woj
          </dd>
        </div>
        <div>
          <dt>Compare</dt>
          <dd>{AGREEMENT_LABEL[agreement]}</dd>
        </div>
      </dl>
    </aside>
  );
}

function Spark({ values }: { values: Array<number | null> }) {
  if (values.length === 0) return null;
  return (
    <div className="spark-block">
      <p>21-day flush</p>
      <div className="spark" aria-hidden="true">
        {values.map((value, index) => (
          <b
            key={index}
            style={{
              height: `${Math.max(6, value ?? 0)}%`,
              background: heatFill(value ?? 0),
              opacity: value == null ? 0.25 : 0.9,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function DayStrip({
  county,
  dayOffset,
  mode,
  onPickDay,
}: {
  county: County;
  dayOffset: number;
  mode: ViewMode;
  onPickDay: (offset: number) => void;
}) {
  const days = county.days ?? [];
  if (days.length === 0) return null;
  return (
    <div className="daystrip" role="tablist" aria-label="Forecast day">
      {days.map((day) => {
        const value = mode === "timesfm" ? (day.timesfm ?? day.boom) : day.boom;
        return (
          <button
            key={day.date}
            type="button"
            role="tab"
            className={day.offset === dayOffset ? "is-on" : undefined}
            onClick={() => onPickDay(day.offset)}
            style={{ "--day": heatFill(value) } as CSSProperties}
          >
            <span>{day.offset === 0 ? "Today" : day.weekday}</span>
            <em>{value.toFixed(0)}</em>
          </button>
        );
      })}
    </div>
  );
}

function headlineFor(
  mode: ViewMode,
  county: County,
  day: DayScore | null,
): { value: string; unit: string } {
  const when = day ? (day.offset === 0 ? "today" : day.weekday) : "today";
  switch (mode) {
    case "boom":
      return { value: (day?.boom ?? county.boom_now).toFixed(0), unit: `boom ${when}` };
    case "timesfm":
      return {
        value: (day?.timesfm ?? county.timesfm_plus7 ?? day?.boom ?? county.boom_plus7).toFixed(0),
        unit: `TimesFM ${when}`,
      };
    case "grzyby":
      return { value: String(county.grzyby_woj_reports), unit: "woj reports" };
    case "compare":
      return { value: AGREEMENT_LABEL[agreementOf(county, day?.offset ?? 0)], unit: when };
    default: {
      const _never: never = mode;
      return _never;
    }
  }
}
