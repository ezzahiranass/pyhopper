"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import maplibregl, { StyleSpecification } from "maplibre-gl";
import { Check, Frame, Grab, Minus, Pencil, Plus, Search, X } from "lucide-react";
import { ProjectParcel } from "@/components/studio/types";
import { Slider } from "@/components/ui/slider";

type Props = {
  value: ProjectParcel | null;
  onChange: (value: ProjectParcel | null) => void;
  editable?: boolean;
  wakeRadiusBoostMeters?: number;
};

type SearchSuggestion = {
  id: string;
  label: string;
  lat: string;
  lon: string;
  boundingbox?: [string, string, string, string];
};

type Mode = "idle" | "drawing" | "editing";

type DragState =
  | { type: "corner"; index: number }
  | { type: "polygon"; lastPoint: [number, number] };

const DEFAULT_CENTER: [number, number] = [-7.5898, 33.5731];
const CLOSE_POINT_THRESHOLD_PX = 18;
const LABEL_MIN_ZOOM = 16;
const COORD_MIN_ZOOM = 17;
const DEFAULT_ANALYSIS_RADIUS_METERS = 1000;
const MIN_ANALYSIS_RADIUS_METERS = 200;
const MAX_ANALYSIS_RADIUS_METERS = 2000;

const SAVED_POLYGON_SOURCE_ID = "parcel-saved-polygon";
const SAVED_CORNERS_SOURCE_ID = "parcel-saved-corners";
const SAVED_AREA_SOURCE_ID = "parcel-saved-area";
const SAVED_COORDS_SOURCE_ID = "parcel-saved-coords";
const ANALYSIS_AREA_SOURCE_ID = "parcel-analysis-area";
const DRAFT_LINE_SOURCE_ID = "parcel-draft-line";
const DRAFT_POINTS_SOURCE_ID = "parcel-draft-points";
const EDIT_POLYGON_SOURCE_ID = "parcel-edit-polygon";
const EDIT_CORNERS_SOURCE_ID = "parcel-edit-corners";

const MAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [
    {
      id: "osm",
      type: "raster",
      source: "osm",
    },
  ],
};

function getParcelPoints(parcel: ProjectParcel | null) {
  return parcel?.coordinates[0]?.slice(0, -1) ?? [];
}

function clampRadius(radius: number) {
  return Math.min(MAX_ANALYSIS_RADIUS_METERS, Math.max(MIN_ANALYSIS_RADIUS_METERS, Math.round(radius)));
}

function getParcelRadius(parcel: ProjectParcel | null) {
  return clampRadius(parcel?.analysisRadiusMeters ?? DEFAULT_ANALYSIS_RADIUS_METERS);
}

function getWakeRadius(parcel: ProjectParcel | null, boostMeters: number) {
  return clampRadius(getParcelRadius(parcel) + boostMeters);
}

function emptyFeatureCollection() {
  return { type: "FeatureCollection" as const, features: [] };
}

function buildPolygon(points: [number, number][]) {
  if (points.length < 3) return null;
  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        geometry: {
          type: "Polygon" as const,
          coordinates: [[...points, points[0]]],
        },
        properties: {},
      },
    ],
  };
}

function buildLine(points: [number, number][], hoverPoint: [number, number] | null) {
  if (points.length === 0) return null;
  const coordinates = hoverPoint ? [...points, hoverPoint] : points;
  if (coordinates.length < 2) return null;

  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        geometry: {
          type: "LineString" as const,
          coordinates,
        },
        properties: {},
      },
    ],
  };
}

function buildPointCollection(
  points: [number, number][],
  formatter?: (point: [number, number], index: number) => Record<string, unknown>,
) {
  return {
    type: "FeatureCollection" as const,
    features: points.map((point, index) => ({
      type: "Feature" as const,
      geometry: {
        type: "Point" as const,
        coordinates: point,
      },
      properties: formatter?.(point, index) ?? { index },
    })),
  };
}

function buildDraftPoints(points: [number, number][], hoverPoint: [number, number] | null) {
  return {
    type: "FeatureCollection" as const,
    features: [
      ...points.map((point, index) => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: point,
        },
        properties: { index, ghost: false },
      })),
      ...(hoverPoint
        ? [{
            type: "Feature" as const,
            geometry: {
              type: "Point" as const,
              coordinates: hoverPoint,
            },
            properties: { index: points.length, ghost: true },
          }]
        : []),
    ],
  };
}

function getBounds(points: [number, number][]) {
  if (points.length === 0) return null;

  let minLng = points[0][0];
  let minLat = points[0][1];
  let maxLng = points[0][0];
  let maxLat = points[0][1];

  for (const [lng, lat] of points) {
    minLng = Math.min(minLng, lng);
    minLat = Math.min(minLat, lat);
    maxLng = Math.max(maxLng, lng);
    maxLat = Math.max(maxLat, lat);
  }

  return [minLng, minLat, maxLng, maxLat] as [number, number, number, number];
}

function getCenter(points: [number, number][]) {
  if (points.length === 0) return null;

  const sums = points.reduce(
    (acc, [lng, lat]) => [acc[0] + lng, acc[1] + lat] as [number, number],
    [0, 0] as [number, number],
  );

  return [sums[0] / points.length, sums[1] / points.length] as [number, number];
}

function translatePoints(points: [number, number][], deltaLng: number, deltaLat: number) {
  return points.map(([lng, lat]) => [lng + deltaLng, lat + deltaLat] as [number, number]);
}

function formatArea(area: number) {
  if (area >= 1_000_000) return `${(area / 1_000_000).toFixed(2)} km2`;
  if (area >= 10_000) return `${(area / 10_000).toFixed(2)} ha`;
  return `${Math.round(area).toLocaleString()} m2`;
}

function formatCoords(point: [number, number]) {
  return `${point[1].toFixed(5)}, ${point[0].toFixed(5)}`;
}

function formatRadius(radius: number) {
  return radius >= 1000 ? `${(radius / 1000).toFixed(1)} km` : `${radius} m`;
}

function calculateApproxArea(points: [number, number][]) {
  if (points.length < 3) return 0;

  const center = getCenter(points);
  if (!center) return 0;

  const latFactor = 110_540;
  const lngFactor = 111_320 * Math.cos((center[1] * Math.PI) / 180);
  let area = 0;

  for (let index = 0; index < points.length; index += 1) {
    const [lng1, lat1] = points[index];
    const [lng2, lat2] = points[(index + 1) % points.length];
    const x1 = lng1 * lngFactor;
    const y1 = lat1 * latFactor;
    const x2 = lng2 * lngFactor;
    const y2 = lat2 * latFactor;
    area += x1 * y2 - x2 * y1;
  }

  return Math.abs(area / 2);
}

function buildAreaLabel(points: [number, number][]) {
  const center = getCenter(points);
  if (!center || points.length < 3) return emptyFeatureCollection();

  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: center,
        },
        properties: {
          label: formatArea(calculateApproxArea(points)),
        },
      },
    ],
  };
}

function buildCoordinateLabels(points: [number, number][]) {
  return buildPointCollection(points, (point, index) => ({
    index,
    label: formatCoords(point),
  }));
}

function buildAnalysisCircle(points: [number, number][], radiusMeters: number) {
  const center = getCenter(points);
  if (!center || points.length < 3) return emptyFeatureCollection();

  const latRadians = (center[1] * Math.PI) / 180;
  const lngMeters = 111_320 * Math.cos(latRadians);
  const latMeters = 110_540;
  const segments = 64;
  const ring: [number, number][] = [];

  for (let index = 0; index <= segments; index += 1) {
    const angle = (index / segments) * Math.PI * 2;
    const deltaLng = (Math.cos(angle) * radiusMeters) / lngMeters;
    const deltaLat = (Math.sin(angle) * radiusMeters) / latMeters;
    ring.push([center[0] + deltaLng, center[1] + deltaLat]);
  }

  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        geometry: {
          type: "Polygon" as const,
          coordinates: [ring],
        },
        properties: {
          label: formatRadius(radiusMeters),
        },
      },
    ],
  };
}

function isPointInsidePolygon(point: [number, number], polygon: [number, number][]) {
  if (polygon.length < 3) return false;

  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i, i += 1) {
    const xi = polygon[i][0];
    const yi = polygon[i][1];
    const xj = polygon[j][0];
    const yj = polygon[j][1];

    const intersects =
      yi > point[1] !== yj > point[1] &&
      point[0] < ((xj - xi) * (point[1] - yi)) / ((yj - yi) || Number.EPSILON) + xi;

    if (intersects) inside = !inside;
  }

  return inside;
}

function fitMapToAnalysisArea(map: maplibregl.Map | null, points: [number, number][], radiusMeters: number) {
  const center = getCenter(points);
  if (!center || !map) return;

  const latRadians = (center[1] * Math.PI) / 180;
  const lngDelta = radiusMeters / (111_320 * Math.cos(latRadians));
  const latDelta = radiusMeters / 110_540;

  map.fitBounds(
    [
      [center[0] - lngDelta, center[1] - latDelta],
      [center[0] + lngDelta, center[1] + latDelta],
    ],
    { padding: 32, duration: 500 },
  );
}

function getProjectedDistance(map: maplibregl.Map, from: [number, number], to: maplibregl.LngLat) {
  const fromProjected = map.project({ lng: from[0], lat: from[1] });
  const toProjected = map.project(to);
  return Math.hypot(toProjected.x - fromProjected.x, toProjected.y - fromProjected.y);
}

export function SiteParcelMap({
  value,
  onChange,
  editable = true,
  wakeRadiusBoostMeters = 0,
}: Props) {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const modeRef = useRef<Mode>("idle");
  const editableRef = useRef(editable);
  const valueRef = useRef(value);
  const wakeRadiusBoostRef = useRef(wakeRadiusBoostMeters);
  const initialParcelRef = useRef<ProjectParcel | null>(value);
  const workingPointsRef = useRef<[number, number][]>(getParcelPoints(value));
  const workingRadiusRef = useRef<number>(getParcelRadius(value));
  const hoverPointRef = useRef<[number, number] | null>(null);
  const finishRef = useRef<(points?: [number, number][]) => void>(() => {});
  const dragStateRef = useRef<DragState | null>(null);
  const syncSourcesRef = useRef<() => void>(() => {});

  const [mode, setMode] = useState<Mode>("idle");
  const [workingPoints, setWorkingPoints] = useState<[number, number][]>(() => getParcelPoints(value));
  const [workingRadius, setWorkingRadius] = useState<number>(getParcelRadius(value));
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState(value?.searchQuery ?? "");
  const [searchError, setSearchError] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);

  const isDrawing = mode === "drawing";
  const isEditing = mode === "editing";
  const savedPoints = getParcelPoints(value);
  const hasSavedParcel = savedPoints.length >= 3;
  const hasWorkingParcel = workingPoints.length >= 3;
  const sliderVisible = editable && (isEditing ? hasWorkingParcel : hasSavedParcel);
  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    editableRef.current = editable;
  }, [editable]);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    wakeRadiusBoostRef.current = wakeRadiusBoostMeters;
  }, [wakeRadiusBoostMeters]);

  useEffect(() => {
    workingPointsRef.current = workingPoints;
  }, [workingPoints]);

  useEffect(() => {
    workingRadiusRef.current = workingRadius;
  }, [workingRadius]);

  useEffect(() => {
    if (mode === "idle") {
      setWorkingPoints(getParcelPoints(value));
      setWorkingRadius(getParcelRadius(value));
      setSearchQuery(value?.searchQuery ?? "");
    }
  }, [mode, value]);

  const syncSources = useCallback(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) return;

    const showSaved = modeRef.current !== "editing";
    const currentPoints = workingPointsRef.current;
    const currentRadius = workingRadiusRef.current;

    const savedPolygonSource = map.getSource(SAVED_POLYGON_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const savedCornersSource = map.getSource(SAVED_CORNERS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const savedAreaSource = map.getSource(SAVED_AREA_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const savedCoordsSource = map.getSource(SAVED_COORDS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const analysisAreaSource = map.getSource(ANALYSIS_AREA_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const draftLineSource = map.getSource(DRAFT_LINE_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const draftPointsSource = map.getSource(DRAFT_POINTS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const editPolygonSource = map.getSource(EDIT_POLYGON_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const editCornersSource = map.getSource(EDIT_CORNERS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

    savedPolygonSource?.setData(showSaved ? buildPolygon(savedPoints) ?? emptyFeatureCollection() : emptyFeatureCollection());
    savedCornersSource?.setData(showSaved ? buildPointCollection(savedPoints) : emptyFeatureCollection());
    savedAreaSource?.setData(showSaved ? buildAreaLabel(savedPoints) : emptyFeatureCollection());
    savedCoordsSource?.setData(showSaved ? buildCoordinateLabels(savedPoints) : emptyFeatureCollection());

    const analysisPoints = modeRef.current === "editing" ? currentPoints : savedPoints;
    const showAnalysis = analysisPoints.length >= 3;
    analysisAreaSource?.setData(
      showAnalysis ? buildAnalysisCircle(analysisPoints, currentRadius) : emptyFeatureCollection(),
    );

    draftLineSource?.setData(
      modeRef.current === "drawing"
        ? buildLine(currentPoints, hoverPointRef.current) ?? emptyFeatureCollection()
        : emptyFeatureCollection(),
    );
    draftPointsSource?.setData(
      modeRef.current === "drawing"
        ? buildDraftPoints(currentPoints, hoverPointRef.current)
        : emptyFeatureCollection(),
    );

    editPolygonSource?.setData(
      modeRef.current === "editing" ? buildPolygon(currentPoints) ?? emptyFeatureCollection() : emptyFeatureCollection(),
    );
    editCornersSource?.setData(
      modeRef.current === "editing" ? buildPointCollection(currentPoints) : emptyFeatureCollection(),
    );
  }, [savedPoints]);

  useEffect(() => {
    syncSourcesRef.current = syncSources;
  }, [syncSources]);

  const flushDraftSources = useCallback(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) return;

    const draftLineSource = map.getSource(DRAFT_LINE_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const draftPointsSource = map.getSource(DRAFT_POINTS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const editPolygonSource = map.getSource(EDIT_POLYGON_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    const editCornersSource = map.getSource(EDIT_CORNERS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

    draftLineSource?.setData(emptyFeatureCollection());
    draftPointsSource?.setData(emptyFeatureCollection());
    editPolygonSource?.setData(emptyFeatureCollection());
    editCornersSource?.setData(emptyFeatureCollection());
  }, []);

  const commitParcel = useCallback((points = workingPointsRef.current) => {
    if (points.length < 3) return;

    setMode("idle");
    hoverPointRef.current = null;
    dragStateRef.current = null;
    mapRef.current?.dragPan.enable();

    const nextParcel: ProjectParcel = {
      type: "Polygon",
      coordinates: [[...points, points[0]]],
      bbox: getBounds(points),
      center: getCenter(points),
      searchQuery: searchQuery.trim(),
      analysisRadiusMeters: workingRadiusRef.current,
    };

    onChange(nextParcel);
    fitMapToAnalysisArea(mapRef.current, points, workingRadiusRef.current);
  }, [onChange, searchQuery]);

  useEffect(() => {
    finishRef.current = commitParcel;
  }, [commitParcel]);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const initialCenter = initialParcelRef.current?.center
      ?? getCenter(getParcelPoints(initialParcelRef.current))
      ?? DEFAULT_CENTER;
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE,
      center: initialCenter,
      zoom: initialParcelRef.current ? 15 : 11,
      attributionControl: false,
    });

    mapRef.current = map;

    map.on("load", () => {
      map.addSource(SAVED_POLYGON_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${SAVED_POLYGON_SOURCE_ID}-fill`,
        type: "fill",
        source: SAVED_POLYGON_SOURCE_ID,
        paint: {
          "fill-color": "#dc2626",
          "fill-opacity": 0.15,
        },
      });
      map.addLayer({
        id: `${SAVED_POLYGON_SOURCE_ID}-line`,
        type: "line",
        source: SAVED_POLYGON_SOURCE_ID,
        paint: {
          "line-color": "#dc2626",
          "line-width": 2.75,
        },
      });

      map.addSource(SAVED_CORNERS_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${SAVED_CORNERS_SOURCE_ID}-circle`,
        type: "circle",
        source: SAVED_CORNERS_SOURCE_ID,
        minzoom: COORD_MIN_ZOOM,
        paint: {
          "circle-radius": 4.5,
          "circle-color": "#ffffff",
          "circle-stroke-width": 2.2,
          "circle-stroke-color": "#dc2626",
        },
      });

      map.addSource(SAVED_AREA_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${SAVED_AREA_SOURCE_ID}-label`,
        type: "symbol",
        source: SAVED_AREA_SOURCE_ID,
        minzoom: LABEL_MIN_ZOOM,
        layout: {
          "text-field": ["get", "label"],
          "text-font": ["Open Sans Semibold"],
          "text-size": 13,
          "text-anchor": "center",
        },
        paint: {
          "text-color": "#7f1d1d",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1.6,
        },
      });

      map.addSource(SAVED_COORDS_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${SAVED_COORDS_SOURCE_ID}-label`,
        type: "symbol",
        source: SAVED_COORDS_SOURCE_ID,
        minzoom: COORD_MIN_ZOOM,
        layout: {
          "text-field": ["get", "label"],
          "text-font": ["Open Sans Regular"],
          "text-size": 11,
          "text-offset": [0, 1.2],
          "text-anchor": "top",
        },
        paint: {
          "text-color": "#1f2937",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1.4,
        },
      });

      map.addSource(ANALYSIS_AREA_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${ANALYSIS_AREA_SOURCE_ID}-fill`,
        type: "fill",
        source: ANALYSIS_AREA_SOURCE_ID,
        paint: {
          "fill-color": "#f59e0b",
          "fill-opacity": 0.08,
        },
      });
      map.addLayer({
        id: `${ANALYSIS_AREA_SOURCE_ID}-line`,
        type: "line",
        source: ANALYSIS_AREA_SOURCE_ID,
        paint: {
          "line-color": "#f59e0b",
          "line-width": 1.8,
          "line-dasharray": [2, 2],
        },
      });

      map.addSource(DRAFT_LINE_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${DRAFT_LINE_SOURCE_ID}-line`,
        type: "line",
        source: DRAFT_LINE_SOURCE_ID,
        paint: {
          "line-color": "#2563eb",
          "line-width": 2.5,
          "line-dasharray": [2, 2],
        },
      });

      map.addSource(DRAFT_POINTS_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${DRAFT_POINTS_SOURCE_ID}-circle`,
        type: "circle",
        source: DRAFT_POINTS_SOURCE_ID,
        paint: {
          "circle-radius": ["case", ["==", ["get", "ghost"], true], 4, 4.75],
          "circle-color": ["case", ["==", ["get", "ghost"], true], "#93c5fd", "#2563eb"],
          "circle-opacity": ["case", ["==", ["get", "ghost"], true], 0.65, 1],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addSource(EDIT_POLYGON_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${EDIT_POLYGON_SOURCE_ID}-fill`,
        type: "fill",
        source: EDIT_POLYGON_SOURCE_ID,
        paint: {
          "fill-color": "#dc2626",
          "fill-opacity": 0.08,
        },
      });
      map.addLayer({
        id: `${EDIT_POLYGON_SOURCE_ID}-line`,
        type: "line",
        source: EDIT_POLYGON_SOURCE_ID,
        paint: {
          "line-color": "#2563eb",
          "line-width": 2.6,
        },
      });

      map.addSource(EDIT_CORNERS_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
      map.addLayer({
        id: `${EDIT_CORNERS_SOURCE_ID}-circle`,
        type: "circle",
        source: EDIT_CORNERS_SOURCE_ID,
        paint: {
          "circle-radius": 5.2,
          "circle-color": "#2563eb",
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      syncSourcesRef.current();

      const currentValue = valueRef.current;
      const currentPoints = getParcelPoints(currentValue);
      if (currentPoints.length >= 3) {
        fitMapToAnalysisArea(map, currentPoints, getWakeRadius(currentValue, wakeRadiusBoostRef.current));
      }
    });

    map.on("click", (event) => {
      if (!editableRef.current || modeRef.current !== "drawing") return;

      setWorkingPoints((current) => {
        if (current.length >= 3 && mapRef.current) {
          const distance = getProjectedDistance(mapRef.current, current[0], event.lngLat);
          if (distance <= CLOSE_POINT_THRESHOLD_PX) {
            window.setTimeout(() => {
              finishRef.current(current);
            }, 0);
            return current;
          }
        }

        return [...current, [event.lngLat.lng, event.lngLat.lat]];
      });
    });

    map.on("mousedown", (event) => {
      if (!editableRef.current || modeRef.current !== "editing") return;

      const points = workingPointsRef.current;
      const nearestCornerIndex = points.findIndex((point) => getProjectedDistance(map, point, event.lngLat) <= CLOSE_POINT_THRESHOLD_PX);
      if (nearestCornerIndex >= 0) {
        dragStateRef.current = { type: "corner", index: nearestCornerIndex };
        map.dragPan.disable();
        return;
      }

      if (isPointInsidePolygon([event.lngLat.lng, event.lngLat.lat], points)) {
        dragStateRef.current = {
          type: "polygon",
          lastPoint: [event.lngLat.lng, event.lngLat.lat],
        };
        map.dragPan.disable();
      }
    });

    map.on("mousemove", (event) => {
      if (editableRef.current && modeRef.current === "drawing") {
        hoverPointRef.current = [event.lngLat.lng, event.lngLat.lat];
        syncSourcesRef.current();
      }

      const dragState = dragStateRef.current;
      if (modeRef.current !== "editing" || !dragState) return;

      setWorkingPoints((current) => {
        if (dragState.type === "corner") {
          return current.map((point, index) =>
            index === dragState.index ? [event.lngLat.lng, event.lngLat.lat] as [number, number] : point,
          );
        }

        const deltaLng = event.lngLat.lng - dragState.lastPoint[0];
        const deltaLat = event.lngLat.lat - dragState.lastPoint[1];
        dragStateRef.current = {
          type: "polygon",
          lastPoint: [event.lngLat.lng, event.lngLat.lat],
        };
        return translatePoints(current, deltaLng, deltaLat);
      });
    });

    map.on("mouseup", () => {
      dragStateRef.current = null;
      map.dragPan.enable();
    });

    map.on("mouseout", () => {
      if (editableRef.current && modeRef.current === "drawing") {
        hoverPointRef.current = null;
        syncSourcesRef.current();
      }
      dragStateRef.current = null;
      map.dragPan.enable();
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    syncSources();
  }, [syncSources, workingPoints, workingRadius, mode]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapContainerRef.current) return;

    const resizeMap = () => {
      map.resize();
      syncSourcesRef.current();
      if (modeRef.current === "idle" && savedPoints.length >= 3) {
        fitMapToAnalysisArea(map, savedPoints, getWakeRadius(value, wakeRadiusBoostMeters));
      }
    };

    resizeMap();

    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      resizeMap();
    });
    observer.observe(mapContainerRef.current);
    return () => observer.disconnect();
  }, [savedPoints, value, wakeRadiusBoostMeters]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    syncSourcesRef.current();
    if (mode === "idle" && savedPoints.length >= 3) {
      fitMapToAnalysisArea(map, savedPoints, getWakeRadius(value, wakeRadiusBoostMeters));
    }
  }, [mode, savedPoints, value, wakeRadiusBoostMeters]);

  useEffect(() => {
    if (!editable || !isDrawing) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== "Enter") return;
      const target = event.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) return;
      event.preventDefault();
      finishRef.current();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [editable, isDrawing]);

  useEffect(() => {
    if (!isSearchOpen) {
      setSuggestions([]);
      return;
    }

    const query = searchQuery.trim();
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=5&q=${encodeURIComponent(query)}`,
          { signal: controller.signal },
        );
        if (!response.ok) throw new Error(`Suggestion request failed with status ${response.status}`);
        const payload = (await response.json()) as Array<{
          place_id?: number | string;
          display_name?: string;
          lat?: string;
          lon?: string;
          boundingbox?: [string, string, string, string];
        }>;
        setSuggestions(
          payload
            .filter((item) => item.display_name && item.lat && item.lon)
            .map((item) => ({
              id: String(item.place_id ?? item.display_name),
              label: item.display_name as string,
              lat: item.lat as string,
              lon: item.lon as string,
              boundingbox: item.boundingbox,
            })),
        );
      } catch (error) {
        if ((error as Error).name !== "AbortError") console.error(error);
      }
    }, 220);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [isSearchOpen, searchQuery]);

  async function runSearch(match?: SearchSuggestion) {
    try {
      setIsSearching(true);
      setSearchError("");

      let nextMatch = match;

      if (!nextMatch) {
        const query = searchQuery.trim();
        if (!query) return;
        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&polygon_geojson=0&q=${encodeURIComponent(query)}`,
        );
        if (!response.ok) throw new Error(`Geocoding failed with status ${response.status}`);
        const payload = (await response.json()) as SearchSuggestion[];
        if (!payload[0]?.lat || !payload[0]?.lon) {
          setSearchError("No matching place found.");
          return;
        }
        nextMatch = payload[0];
      }

      if (!mapRef.current) return;

      const center: [number, number] = [Number(nextMatch.lon), Number(nextMatch.lat)];
      const bbox = Array.isArray(nextMatch.boundingbox) && nextMatch.boundingbox.length === 4
        ? [
            [Number(nextMatch.boundingbox[2]), Number(nextMatch.boundingbox[0])],
            [Number(nextMatch.boundingbox[3]), Number(nextMatch.boundingbox[1])],
          ] as [[number, number], [number, number]]
        : null;

      if (bbox) {
        mapRef.current.fitBounds(bbox, { padding: 32, duration: 800 });
      } else {
        mapRef.current.flyTo({ center, zoom: 16, duration: 800 });
      }

      if (nextMatch.label) setSearchQuery(nextMatch.label);
      setSuggestions([]);
      setIsSearchOpen(false);
    } catch (error) {
      console.error(error);
      setSearchError("Search failed. Check your network access.");
    } finally {
      setIsSearching(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runSearch();
  }

  function handleStartDrawing() {
    flushDraftSources();
    dragStateRef.current = null;
    mapRef.current?.dragPan.enable();
    setWorkingPoints([]);
    hoverPointRef.current = null;
    setMode("drawing");
  }

  function handleStartEditing() {
    if (!value) return;
    flushDraftSources();
    dragStateRef.current = null;
    mapRef.current?.dragPan.enable();
    setWorkingPoints(getParcelPoints(value));
    setWorkingRadius(getParcelRadius(value));
    hoverPointRef.current = null;
    setMode("editing");
  }

  function handleCancelInteractiveMode() {
    flushDraftSources();
    dragStateRef.current = null;
    mapRef.current?.dragPan.enable();
    setWorkingPoints(getParcelPoints(value));
    setWorkingRadius(getParcelRadius(value));
    hoverPointRef.current = null;
    setMode("idle");
  }

  function handleFitToParcel() {
    const points = isEditing ? workingPoints : getParcelPoints(value);
    if (points.length === 0) return;
    const radius = isEditing ? workingRadius : getParcelRadius(value);
    fitMapToAnalysisArea(mapRef.current, points, radius);
  }

  function handleRadiusChange(nextRadius: number) {
    if (!editable) return;

    const clamped = clampRadius(nextRadius);
    setWorkingRadius(clamped);

    if (mode === "idle" && value && hasSavedParcel) {
      onChange({
        ...value,
        analysisRadiusMeters: clamped,
      });
    }
  }

  return (
    <div className="parcel-map">
      <div className="parcel-map__viewer">
        <div ref={mapContainerRef} className="parcel-map__canvas" />

        {searchError ? <p className="parcel-map__error parcel-map__error--overlay">{searchError}</p> : null}

        <div className="parcel-map__fab-group parcel-map__fab-group--top-left">
          {isSearchOpen ? (
            <div className="parcel-map__search-shell">
              <form className="parcel-map__search parcel-map__search--floating" onSubmit={handleSearch}>
                <Search size={16} />
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search address or place"
                  autoFocus
                />
                <button type="submit" disabled={isSearching}>
                  {isSearching ? "..." : "Go"}
                </button>
                <button type="button" onClick={() => setIsSearchOpen(false)} aria-label="Collapse search">
                  <X size={14} />
                </button>
              </form>
              {suggestions.length > 0 ? (
                <div className="parcel-map__suggestions">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion.id}
                      type="button"
                      className="parcel-map__suggestion"
                      onClick={() => {
                        void runSearch(suggestion);
                      }}
                    >
                      {suggestion.label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : (
            <button
              type="button"
              className="parcel-map__fab"
              onClick={() => setIsSearchOpen(true)}
              aria-label="Search location"
            >
              <Search size={16} />
            </button>
          )}
        </div>

        <div className="parcel-map__fab-group parcel-map__fab-group--top-right">
          <button type="button" className="parcel-map__fab parcel-map__fab--zoom" onClick={() => mapRef.current?.zoomIn()} aria-label="Zoom in">
            <Plus size={16} />
          </button>
          <button type="button" className="parcel-map__fab parcel-map__fab--zoom" onClick={() => mapRef.current?.zoomOut()} aria-label="Zoom out">
            <Minus size={16} />
          </button>
          <button
            type="button"
            className="parcel-map__fab parcel-map__fab--zoom"
            onClick={handleFitToParcel}
            aria-label="Fit parcel to view"
            disabled={!(isEditing ? hasWorkingParcel : hasSavedParcel)}
          >
            <Frame size={15} />
          </button>
        </div>

        {editable ? (
          <div className="parcel-map__fab-group parcel-map__fab-group--bottom-right">
            {mode === "drawing" || mode === "editing" ? (
              <>
                <button
                  type="button"
                  className="parcel-map__fab parcel-map__fab--confirm"
                  onClick={() => finishRef.current()}
                  disabled={!hasWorkingParcel}
                  aria-label={isEditing ? "Save parcel edits" : "Save parcel"}
                >
                  <Check size={18} />
                </button>
                <button
                  type="button"
                  className="parcel-map__fab parcel-map__fab--cancel"
                  onClick={handleCancelInteractiveMode}
                  aria-label={isEditing ? "Cancel parcel edits" : "Cancel parcel drawing"}
                >
                  <X size={18} />
                </button>
              </>
            ) : (
              <>
                {value ? (
                  <button
                    type="button"
                    className="parcel-map__fab parcel-map__fab--edit"
                    onClick={handleStartEditing}
                    aria-label="Move parcel"
                  >
                    <Grab size={18} />
                  </button>
                ) : null}
                <button
                  type="button"
                  className="parcel-map__fab parcel-map__fab--draw"
                  onClick={handleStartDrawing}
                  aria-label={hasSavedParcel ? "Redraw parcel" : "Draw parcel"}
                >
                  <Pencil size={18} />
                </button>
              </>
            )}
          </div>
        ) : null}

        {sliderVisible ? (
          <div className="parcel-map__radius-control">
            <Slider
              className="parcel-map__radius-slider"
              min={MIN_ANALYSIS_RADIUS_METERS}
              max={MAX_ANALYSIS_RADIUS_METERS}
              step={50}
              value={[workingRadius]}
              onValueChange={(value) => handleRadiusChange(value[0] ?? DEFAULT_ANALYSIS_RADIUS_METERS)}
            />
            <span className="parcel-map__radius-value">{formatRadius(workingRadius)}</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}
