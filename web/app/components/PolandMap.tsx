"use client";

import { geometryPath } from "../lib/geo";
import { fillFor } from "../lib/color";
import type { County, GeoJSON, ViewMode } from "../lib/types";

const WIDTH = 900;
const HEIGHT = 860;

type Props = {
  geo: GeoJSON | null;
  counties: Map<number, County>;
  mode: ViewMode;
  dayOffset: number;
  selectedId: number | null;
  onSelect: (id: number) => void;
};

export function PolandMap({ geo, counties, mode, dayOffset, selectedId, onSelect }: Props) {
  if (!geo) {
    return <div className="map-svg" />;
  }

  return (
    <svg
      className="map-svg"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="Mapa powiatów Polski"
    >
      {geo.features.map((feature) => {
        const county = counties.get(feature.properties.id);
        const fill = county ? fillFor(mode, county, dayOffset) : "#000098";
        return (
          <path
            key={feature.properties.id}
            className={feature.properties.id === selectedId ? "county is-on" : "county"}
            d={geometryPath(feature.geometry, WIDTH, HEIGHT)}
            fill={fill}
            onClick={() => onSelect(feature.properties.id)}
          >
            <title>{feature.properties.nazwa}</title>
          </path>
        );
      })}
    </svg>
  );
}
