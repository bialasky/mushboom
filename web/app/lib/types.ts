export type ViewMode = "boom" | "timesfm" | "grzyby" | "compare";

export type DayScore = {
  offset: number;
  date: string;
  weekday: string;
  boom: number;
  timesfm: number | null;
  precip_14d: number;
  nights_7d: number;
  humidity_7d: number;
};

export type County = {
  id: number;
  name: string;
  woj: string;
  lat: number;
  lon: number;
  urban: boolean;
  boom_now: number;
  boom_plus7: number;
  precip_14d: number;
  humidity_7d: number;
  nights_7d: number;
  days: DayScore[];
  timesfm_now: number | null;
  timesfm_plus7: number | null;
  grzyby_reports: number;
  grzyby_woj_reports: number;
  grzyby_intensity: number;
  history_tail: Array<number | null>;
};

export type ForecastSnapshot = {
  generated_at: string;
  model: {
    kernel: string;
    timesfm: string | null;
    timesfm_device: string;
    timesfm_error: string | null;
    timesfm_scope: string | null;
    timesfm_pending?: boolean;
    license: string;
  };
  grzyby: {
    ok: boolean;
    source: string;
    url: string;
    fetched_at: string;
    by_woj: Record<string, number>;
    period?: string | null;
    unknown_location?: number;
    report_total: number;
    note: string;
    error?: string;
  };
  counties: County[];
};

export type GeoJSON = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: { id: number; nazwa: string };
    geometry: {
      type: "Polygon" | "MultiPolygon";
      coordinates: number[][][] | number[][][][];
    };
  }>;
};

export type Agreement = "confirmed" | "predicted" | "reported" | "quiet";
