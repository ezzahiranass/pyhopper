"use client";

import type GeoJSON from "geojson";
import { GeoMap } from "@/components/viewers/geomap";

const PLAYGROUND_CENTER: [number, number] = [-7.6215, 33.5892];

const PLAYGROUND_LAYER_COLORS: Record<string, string> = {
  background: "#ffffff",
  building: "#4b5563",
  contours: "#111111",
  water: "#b8c8d8",
  "highway-minor": "#eceae7",
  "highway-primary": "#e7e5e4",
  "highway-secondary-tertiary": "#f1efec",
  park: "#ececec",
  "landuse-residential": "#f3efe9",
  "landuse-suburb": "#f1eee8",
  "landuse-commercial": "#f4ecef",
  "landuse-industrial": "#f2efe6",
  "landuse-cemetery": "#edf1eb",
  "landuse-hospital": "#f6edef",
  "landuse-school": "#efeff6",
  "landuse-railway": "#ece9e6",
  "landcover-wood": "#e6ebe4",
  "landcover-grass": "#e8e8e8",
  "landcover-grass-park": "#e5e9e3",
};

const PLAYGROUND_LAYER_ZOOM_RANGES = {
  building: { min: 11, max: 24 },
  "building-top": { min: 11, max: 24 },
};

const PLAYGROUND_OVERLAY: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        _fill: "#f59e0b",
        _stroke: "#b45309",
        _opacity: 0.28,
        _width: 2,
      },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-7.6282, 33.5914],
          [-7.6255, 33.5916],
          [-7.6253, 33.5891],
          [-7.6278, 33.5889],
          [-7.6282, 33.5914],
        ]],
      },
    },
    {
      type: "Feature",
      properties: {
        _fill: "#60a5fa",
        _stroke: "#2563eb",
        _opacity: 0.24,
        _width: 2,
      },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-7.6218, 33.5924],
          [-7.6186, 33.5922],
          [-7.6188, 33.5897],
          [-7.6215, 33.5899],
          [-7.6218, 33.5924],
        ]],
      },
    },
    {
      type: "Feature",
      properties: {
        _fill: "#f472b6",
        _stroke: "#db2777",
        _opacity: 0.24,
        _width: 2,
      },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-7.6249, 33.5867],
          [-7.6214, 33.5869],
          [-7.6217, 33.5847],
          [-7.6247, 33.5845],
          [-7.6249, 33.5867],
        ]],
      },
    },
  ],
};

export function StudioPlayground() {
  return (
    <GeoMap
      basemap="none"
      center={PLAYGROUND_CENTER}
      defaultZoom={15.2}
      minZoom={5}
      maxZoom={18.45}
      enableContours
      geojson={PLAYGROUND_OVERLAY}
      layerColors={PLAYGROUND_LAYER_COLORS}
      layerZoomRanges={PLAYGROUND_LAYER_ZOOM_RANGES}
    />
  );
}
