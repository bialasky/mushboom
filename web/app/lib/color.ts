import type { Agreement, County, DayScore, ViewMode } from "./types";

export function dayAt(county: County, offset: number): DayScore | null {
  const days = county.days ?? [];
  return days.find((day) => day.offset === offset) ?? days[0] ?? null;
}

function mix(a: string, b: string, t: number): string {
  const pa = hex(a);
  const pb = hex(b);
  const u = Math.min(1, Math.max(0, t));
  const ch = (i: number) => Math.round(pa[i] + (pb[i] - pa[i]) * u);
  return `rgb(${ch(0)} ${ch(1)} ${ch(2)})`;
}

function hex(value: string): [number, number, number] {
  const raw = value.replace("#", "");
  return [
    Number.parseInt(raw.slice(0, 2), 16),
    Number.parseInt(raw.slice(2, 4), 16),
    Number.parseInt(raw.slice(4, 6), 16),
  ];
}

const HEAT: Array<[number, string]> = [
  [0, "#000098"],
  [0.16, "#0078F0"],
  [0.32, "#00D0C8"],
  [0.48, "#48E000"],
  [0.64, "#F0F000"],
  [0.8, "#FF7800"],
  [1, "#C00000"],
];

export const HEAT_CSS =
  "linear-gradient(90deg, #000098, #0078F0, #00D0C8, #48E000, #F0F000, #FF7800, #C00000)";

export function heatFill(value: number): string {
  const t = Math.min(1, Math.max(0, value / 100));
  for (let i = 1; i < HEAT.length; i += 1) {
    if (t <= HEAT[i][0]) {
      const [start, from] = HEAT[i - 1];
      const [end, to] = HEAT[i];
      return mix(from, to, (t - start) / (end - start));
    }
  }
  return HEAT[HEAT.length - 1][1];
}

export function boomFill(value: number): string {
  return heatFill(value);
}

export function grzybyFill(value: number): string {
  return heatFill(value);
}

export function agreementOf(county: County, offset = 0): Agreement {
  const boom = (dayAt(county, offset)?.boom ?? county.boom_now) >= 55;
  const reported = county.grzyby_intensity >= 40 || county.grzyby_reports > 0;
  if (boom && reported) return "confirmed";
  if (boom) return "predicted";
  if (reported) return "reported";
  return "quiet";
}

export function agreementFill(kind: Agreement): string {
  switch (kind) {
    case "confirmed":
      return "#C00000";
    case "predicted":
      return "#FF7800";
    case "reported":
      return "#00D0C8";
    case "quiet":
      return "#000098";
    default: {
      const _never: never = kind;
      return _never;
    }
  }
}

export function scoreFor(mode: ViewMode, county: County, offset = 0): number {
  const day = dayAt(county, offset);
  switch (mode) {
    case "boom":
      return day?.boom ?? county.boom_now;
    case "timesfm":
      return day?.timesfm ?? county.timesfm_plus7 ?? day?.boom ?? county.boom_plus7;
    case "grzyby":
      return county.grzyby_intensity;
    case "compare":
      return day?.boom ?? county.boom_now;
    default: {
      const _never: never = mode;
      return _never;
    }
  }
}

export function fillFor(mode: ViewMode, county: County, offset = 0): string {
  switch (mode) {
    case "boom":
      return boomFill(scoreFor(mode, county, offset));
    case "timesfm":
      return boomFill(scoreFor(mode, county, offset));
    case "grzyby":
      return grzybyFill(county.grzyby_intensity);
    case "compare":
      return agreementFill(agreementOf(county, offset));
    default: {
      const _never: never = mode;
      return _never;
    }
  }
}
