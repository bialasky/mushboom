import type { GeoJSON } from "./types";

const WEST = 14.07;
const EAST = 24.16;
const SOUTH = 48.98;
const NORTH = 54.86;

export function project(lon: number, lat: number, width: number, height: number): [number, number] {
  const x = ((lon - WEST) / (EAST - WEST)) * width;
  const y = ((NORTH - lat) / (NORTH - SOUTH)) * height;
  return [x, y];
}

function ringPath(ring: number[][], width: number, height: number): string {
  return (
    ring
      .map((point, index) => {
        const [x, y] = project(point[0], point[1], width, height);
        return `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(" ") + " Z"
  );
}

export function geometryPath(
  geometry: GeoJSON["features"][number]["geometry"],
  width: number,
  height: number,
): string {
  if (geometry.type === "Polygon") {
    return (geometry.coordinates as number[][][])
      .map((ring) => ringPath(ring, width, height))
      .join(" ");
  }
  return (geometry.coordinates as number[][][][])
    .map((polygon) => polygon.map((ring) => ringPath(ring, width, height)).join(" "))
    .join(" ");
}
