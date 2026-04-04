"use client";

import { useEffect, useRef } from "react";
import maplibregl, { type StyleSpecification } from "maplibre-gl";
import type GeoJSON from "geojson";
import { MapPin } from "lucide-react";
import type { GeolocationMapStyle, WorkspaceGeolocationArtifact } from "@/components/studio/types";
import { useWorkspaceArtifactViewer } from "@/components/workspace/artifacts/artifact-viewer-context";

const MAP_STYLE: StyleSpecification = {
  version: 8,
  glyphs: "https://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
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

const POLYGON_SOURCE_ID = "workspace-artifact-polygon";
const RADIUS_SOURCE_ID = "workspace-artifact-radius";
const CENTER_SOURCE_ID = "workspace-artifact-center";
const OVERLAYS_SOURCE_ID = "workspace-artifact-overlays";

function emptyFeatureCollection() {
  return { type: "FeatureCollection" as const, features: [] };
}

function parseOverlaysGeojson(raw: string | undefined) {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { type?: string; features?: unknown[] };
    if (parsed?.type === "FeatureCollection" && Array.isArray(parsed.features)) {
      return parsed as GeoJSON.FeatureCollection;
    }
    return null;
  } catch {
    return null;
  }
}

// Generic overlay interpreter — knows only primitives (_type, _color, _width, …).
// No knowledge of what the data represents.
function ensureOverlayLayers(map: maplibregl.Map) {
  if (map.getSource(OVERLAYS_SOURCE_ID)) return;

  map.addSource(OVERLAYS_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });

  const S = OVERLAYS_SOURCE_ID;

  // Z-index buckets 1–9: one set of layers per zIndex value, ordered so higher
  // zIndex is added last (drawn on top). Within each bucket: fill → line → circle → label.
  for (let z = 1; z <= 9; z++) {
    const zf: maplibregl.FilterSpecification = ["==", ["get", "_zIndex"], z];

    // fill
    map.addLayer({
      id: `${S}-fill-z${z}`,
      type: "fill",
      source: S,
      filter: ["all", zf, ["==", ["get", "_type"], "fill"]],
      paint: {
        "fill-color": ["get", "_color"],
        "fill-opacity": ["get", "_opacity"],
      },
    });

    // solid lines
    map.addLayer({
      id: `${S}-line-z${z}`,
      type: "line",
      source: S,
      filter: ["all", zf, ["==", ["get", "_type"], "line"], ["!=", ["get", "_dash"], true]],
      paint: {
        "line-color": ["get", "_color"],
        "line-width": ["get", "_width"],
        "line-opacity": ["get", "_opacity"],
      },
    });

    // dashed lines (dasharray can't be data-driven, so we separate them)
    map.addLayer({
      id: `${S}-dash-z${z}`,
      type: "line",
      source: S,
      filter: ["all", zf, ["==", ["get", "_type"], "line"], ["==", ["get", "_dash"], true]],
      paint: {
        "line-color": ["get", "_color"],
        "line-width": ["get", "_width"],
        "line-opacity": ["get", "_opacity"],
        "line-dasharray": [4, 3],
      },
    });

    // circles
    map.addLayer({
      id: `${S}-circle-z${z}`,
      type: "circle",
      source: S,
      filter: ["all", zf, ["==", ["get", "_type"], "circle"]],
      paint: {
        "circle-color": ["get", "_color"],
        "circle-radius": ["get", "_width"],
        "circle-opacity": ["get", "_opacity"],
      },
    });

    // labels — regular weight
    map.addLayer({
      id: `${S}-label-z${z}`,
      type: "symbol",
      source: S,
      filter: ["all", zf, ["==", ["get", "_type"], "label"], ["!=", ["get", "_bold"], true]],
      layout: {
        "text-field": ["get", "_text"],
        "text-size": ["get", "_size"],
        "text-font": ["Open Sans Regular"],
        "text-anchor": "center",
        "text-allow-overlap": true,
        "text-ignore-placement": true,
      },
      paint: {
        "text-color": ["get", "_color"],
        "text-opacity": ["get", "_opacity"],
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.5,
      },
    });

    // labels — bold weight
    map.addLayer({
      id: `${S}-label-bold-z${z}`,
      type: "symbol",
      source: S,
      filter: ["all", zf, ["==", ["get", "_type"], "label"], ["==", ["get", "_bold"], true]],
      layout: {
        "text-field": ["get", "_text"],
        "text-size": ["get", "_size"],
        "text-font": ["Open Sans Bold"],
        "text-anchor": "center",
        "text-allow-overlap": true,
        "text-ignore-placement": true,
      },
      paint: {
        "text-color": ["get", "_color"],
        "text-opacity": ["get", "_opacity"],
        "text-halo-color": "#ffffff",
        "text-halo-width": 2,
      },
    });
  }
}

function applyMapStyle(map: maplibregl.Map, style: GeolocationMapStyle) {
  // raster basemap tweaks
  const rasterLayerId = "osm";
  if (map.getLayer(rasterLayerId)) {
    if (style.basemapSaturation !== undefined)
      map.setPaintProperty(rasterLayerId, "raster-saturation", style.basemapSaturation);
    if (style.basemapContrast !== undefined)
      map.setPaintProperty(rasterLayerId, "raster-contrast", style.basemapContrast);
    if (style.basemapBrightnessMin !== undefined)
      map.setPaintProperty(rasterLayerId, "raster-brightness-min", style.basemapBrightnessMin);
    if (style.basemapBrightnessMax !== undefined)
      map.setPaintProperty(rasterLayerId, "raster-brightness-max", style.basemapBrightnessMax);
  }

  // background color
  if (style.backgroundColor !== undefined && map.getLayer("background")) {
    map.setPaintProperty("background", "background-color", style.backgroundColor);
  }

  // hide labels / icons on basemap symbol layers (skip our own overlay layers)
  if (style.showLabels === false || style.showIcons === false) {
    for (const layer of map.getStyle().layers ?? []) {
      if (layer.type !== "symbol") continue;
      if (layer.id.startsWith(OVERLAYS_SOURCE_ID)) continue;
      if (style.showLabels === false)
        map.setLayoutProperty(layer.id, "text-field", "");
      if (style.showIcons === false)
        map.setLayoutProperty(layer.id, "icon-image", "");
    }
  }
}

function buildArtifactInstanceId(subdomainId: string, artifactId: string) {
  return `${subdomainId}:${artifactId}`;
}

function buildPolygonFeature(coordinates: [number, number][][] | null) {
  if (!coordinates || coordinates.length === 0) return emptyFeatureCollection();

  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        geometry: {
          type: "Polygon" as const,
          coordinates,
        },
        properties: {},
      },
    ],
  };
}

function buildPointFeature(center: [number, number] | null) {
  if (!center) return emptyFeatureCollection();

  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: center,
        },
        properties: {},
      },
    ],
  };
}

function buildCircleFeature(center: [number, number] | null, radiusMeters: number | null) {
  if (!center || !radiusMeters || radiusMeters <= 0) return emptyFeatureCollection();

  const [lng, lat] = center;
  const earthRadius = 6_371_000;
  const angularDistance = radiusMeters / earthRadius;
  const latRad = (lat * Math.PI) / 180;
  const lngRad = (lng * Math.PI) / 180;
  const ring: [number, number][] = [];

  for (let step = 0; step <= 64; step += 1) {
    const bearing = (step / 64) * Math.PI * 2;
    const nextLat = Math.asin(
      Math.sin(latRad) * Math.cos(angularDistance) +
      Math.cos(latRad) * Math.sin(angularDistance) * Math.cos(bearing),
    );
    const nextLng = lngRad + Math.atan2(
      Math.sin(bearing) * Math.sin(angularDistance) * Math.cos(latRad),
      Math.cos(angularDistance) - Math.sin(latRad) * Math.sin(nextLat),
    );

    ring.push([
      ((nextLng * 180) / Math.PI + 540) % 360 - 180,
      (nextLat * 180) / Math.PI,
    ]);
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
        properties: {},
      },
    ],
  };
}

function collectBoundsPoints(
  coordinates: [number, number][][] | null,
  center: [number, number] | null,
  radiusMeters: number | null,
) {
  const points = [...(coordinates?.flat() ?? [])];

  if (center) {
    points.push(center);
  }

  if (center && radiusMeters && radiusMeters > 0) {
    const latOffset = radiusMeters / 110_540;
    const cosLat = Math.cos((center[1] * Math.PI) / 180);
    const safeCosLat = Math.abs(cosLat) < 0.000001 ? 0.000001 : cosLat;
    const lngOffset = radiusMeters / (111_320 * safeCosLat);
    points.push(
      [center[0] - lngOffset, center[1]],
      [center[0] + lngOffset, center[1]],
      [center[0], center[1] - latOffset],
      [center[0], center[1] + latOffset],
    );
  }

  return points;
}

function collectOverlayBoundsPoints(raw: string | undefined): [number, number][] {
  const fc = parseOverlaysGeojson(raw);
  if (!fc) return [];
  const pts: [number, number][] = [];
  for (const feature of fc.features) {
    const geom = feature.geometry as { type: string; coordinates: unknown };
    if (geom.type === "LineString") {
      for (const c of geom.coordinates as [number, number][]) pts.push(c);
    } else if (geom.type === "Polygon") {
      for (const ring of geom.coordinates as [number, number][][]) {
        for (const c of ring) pts.push(c);
      }
    }
  }
  return pts;
}

function radiusToMinZoom(radiusMeters: number): number {
  // Clamp min-zoom so the user can't zoom out past ~3× the analysis radius.
  // zoom ≈ log2(40075016 * cos(lat) / (radius * 2)) — simplified at equator.
  // We use a lookup that feels right across typical urban radii:
  //   50 m  → 17,  500 m → 14,  2 km → 12,  10 km → 10,  50 km → 7
  const zoom = Math.log2(20_000_000 / radiusMeters) - 1.5;
  return Math.max(5, Math.min(17, Math.round(zoom)));
}

function boundsToRadiusMeters(
  minLng: number, minLat: number, maxLng: number, maxLat: number,
): number {
  // Half the diagonal of the bounding box in metres (rough equirectangular)
  const dLng = (maxLng - minLng) * 111_320 * Math.cos((((minLat + maxLat) / 2) * Math.PI) / 180);
  const dLat = (maxLat - minLat) * 110_540;
  return Math.sqrt(dLng * dLng + dLat * dLat) / 2;
}

function fitMapToArtifact(
  map: maplibregl.Map,
  value: WorkspaceGeolocationArtifact["value"],
) {
  const points: [number, number][] = [
    ...collectBoundsPoints(value.coordinates, value.center, value.analysisRadiusMeters),
    ...collectOverlayBoundsPoints(value.overlaysGeojson),
  ];
  if (points.length === 0) return;

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

  // Use analysisRadiusMeters when available; fall back to the bounds extent
  const effectiveRadius = (value.analysisRadiusMeters && value.analysisRadiusMeters > 0)
    ? value.analysisRadiusMeters
    : boundsToRadiusMeters(minLng, minLat, maxLng, maxLat);
  const minZoom = radiusToMinZoom(effectiveRadius);

  if (minLng === maxLng && minLat === maxLat) {
    map.jumpTo({ center: [minLng, minLat], zoom: 15 });
    map.setMinZoom(minZoom);
    return;
  }

  map.fitBounds(
    [[minLng, minLat], [maxLng, maxLat]],
    { padding: 28, duration: 0, maxZoom: 17 },
  );
  map.setMinZoom(minZoom);
}

function ensurePreviewLayers(map: maplibregl.Map) {
  if (!map.getSource(RADIUS_SOURCE_ID)) {
    map.addSource(RADIUS_SOURCE_ID, {
      type: "geojson",
      data: emptyFeatureCollection(),
    });
  }

  if (!map.getSource(POLYGON_SOURCE_ID)) {
    map.addSource(POLYGON_SOURCE_ID, {
      type: "geojson",
      data: emptyFeatureCollection(),
    });
  }

  if (!map.getSource(CENTER_SOURCE_ID)) {
    map.addSource(CENTER_SOURCE_ID, {
      type: "geojson",
      data: emptyFeatureCollection(),
    });
  }

  if (!map.getLayer(`${RADIUS_SOURCE_ID}-fill`)) {
    map.addLayer({
      id: `${RADIUS_SOURCE_ID}-fill`,
      type: "fill",
      source: RADIUS_SOURCE_ID,
      paint: {
        "fill-color": "#2563eb",
        "fill-opacity": 0.1,
      },
    });
  }

  if (!map.getLayer(`${RADIUS_SOURCE_ID}-line`)) {
    map.addLayer({
      id: `${RADIUS_SOURCE_ID}-line`,
      type: "line",
      source: RADIUS_SOURCE_ID,
      paint: {
        "line-color": "#2563eb",
        "line-width": 2,
        "line-opacity": 0.5,
      },
    });
  }

  if (!map.getLayer(`${POLYGON_SOURCE_ID}-fill`)) {
    map.addLayer({
      id: `${POLYGON_SOURCE_ID}-fill`,
      type: "fill",
      source: POLYGON_SOURCE_ID,
      paint: {
        "fill-color": "#0f766e",
        "fill-opacity": 0.18,
      },
    });
  }

  if (!map.getLayer(`${POLYGON_SOURCE_ID}-line`)) {
    map.addLayer({
      id: `${POLYGON_SOURCE_ID}-line`,
      type: "line",
      source: POLYGON_SOURCE_ID,
      paint: {
        "line-color": "#0f766e",
        "line-width": 2.2,
      },
    });
  }

  if (!map.getLayer(`${CENTER_SOURCE_ID}-circle`)) {
    map.addLayer({
      id: `${CENTER_SOURCE_ID}-circle`,
      type: "circle",
      source: CENTER_SOURCE_ID,
      paint: {
        "circle-radius": 4.75,
        "circle-color": "#ffffff",
        "circle-stroke-color": "#1d4ed8",
        "circle-stroke-width": 2.25,
      },
    });
  }
}

function syncPreviewSources(
  map: maplibregl.Map,
  value: WorkspaceGeolocationArtifact["value"],
) {
  const polygonSource = map.getSource(POLYGON_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
  const radiusSource = map.getSource(RADIUS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
  const centerSource = map.getSource(CENTER_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

  polygonSource?.setData(buildPolygonFeature(value.coordinates));
  radiusSource?.setData(buildCircleFeature(value.center, value.analysisRadiusMeters));
  centerSource?.setData(buildPointFeature(value.center));

  const overlaysSource = map.getSource(OVERLAYS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
  const overlays = parseOverlaysGeojson(value.overlaysGeojson);
  overlaysSource?.setData(overlays ?? emptyFeatureCollection());

  fitMapToArtifact(map, value);
}

function formatCoordinates(point: [number, number] | null) {
  if (!point) return "Not set";
  return `${point[1].toFixed(5)}, ${point[0].toFixed(5)}`;
}

export function WorkspaceGeolocationArtifactView({
  artifactId,
  subdomainId,
  artifact,
}: {
  artifactId: string;
  subdomainId: string;
  artifact: WorkspaceGeolocationArtifact;
}) {
  const instanceId = buildArtifactInstanceId(subdomainId, artifactId);
  const { isViewerActive, optimizeEmbeds, setActiveInstanceId } = useWorkspaceArtifactViewer();
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const artifactValueRef = useRef(artifact.value);
  const isActive = isViewerActive(instanceId);
  const ringCount = artifact.value.coordinates?.length ?? 0;
  const pointCount = artifact.value.coordinates?.reduce((sum, ring) => sum + ring.length, 0) ?? 0;
  const radiusText = artifact.value.analysisRadiusMeters != null
    ? `${artifact.value.analysisRadiusMeters} m`
    : "Not set";
  const hasGeometry = pointCount > 0 || Boolean(artifact.value.center);

  useEffect(() => {
    artifactValueRef.current = artifact.value;
  }, [artifact.value]);

  useEffect(() => {
    if (!isActive || !mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE,
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    const syncMap = () => {
      ensurePreviewLayers(map);
      ensureOverlayLayers(map);
      syncPreviewSources(map, artifactValueRef.current);
      if (artifactValueRef.current.mapStyle) applyMapStyle(map, artifactValueRef.current.mapStyle);
      map.resize();
    };

    map.on("load", syncMap);

    return () => {
      map.off("load", syncMap);
      map.remove();
      mapRef.current = null;
    };
  }, [isActive]);

  useEffect(() => {
    const map = mapRef.current;
    if (!isActive || !map || !map.isStyleLoaded()) return;

    ensurePreviewLayers(map);
    ensureOverlayLayers(map);
    syncPreviewSources(map, artifact.value);
    if (artifact.value.mapStyle) applyMapStyle(map, artifact.value.mapStyle);
  }, [artifact.value, isActive]);

  useEffect(() => {
    if (!isActive || !mapContainerRef.current) return;

    const observer = new ResizeObserver(() => {
      const map = mapRef.current;
      if (!map) return;
      map.resize();
      if (map.isStyleLoaded()) {
        fitMapToArtifact(map, artifactValueRef.current);
      }
    });

    observer.observe(mapContainerRef.current);
    return () => observer.disconnect();
  }, [isActive]);

  useEffect(() => {
    if (!isActive || !mapContainerRef.current) return;

    const el = mapContainerRef.current;
    const stopWheel = (event: WheelEvent) => event.stopPropagation();
    el.addEventListener("wheel", stopWheel, { passive: true });
    return () => el.removeEventListener("wheel", stopWheel);
  }, [isActive]);

  return (
    <section className={`workspace-artifact workspace-artifact--geolocation${isActive ? " is-active" : ""}`}>
      <span className="workspace-artifact__label">{artifact.label}</span>
      {isActive ? (
        <div
          className="workspace-artifact__geo-preview workspace-artifact__geo-preview--active workspace-artifact__interactive"
          onPointerDown={(event) => event.stopPropagation()}
        >
          <div className="workspace-artifact__geo-map-shell">
            <div ref={mapContainerRef} className="workspace-artifact__geo-map" />
          </div>
        </div>
      ) : (
        <button
          type="button"
          className="workspace-artifact__geo-toggle workspace-artifact__interactive"
          onClick={() => setActiveInstanceId(instanceId)}
          onPointerDown={(event) => event.stopPropagation()}
          aria-expanded={!optimizeEmbeds ? true : false}
          disabled={!hasGeometry}
        >
          <div className="workspace-artifact__geo-preview">
            <div className="workspace-artifact__geo-icon-shell" aria-hidden="true">
              <span className="workspace-artifact__geo-icon">
                <MapPin size={18} />
              </span>
            </div>
            <span className="workspace-artifact__geo-action">
              {hasGeometry ? "Open parcel preview" : "Parcel data unavailable"}
            </span>
            <span className="sr-only">
              {`Center ${formatCoordinates(artifact.value.center)}, radius ${radiusText}, ${ringCount} rings, ${pointCount} points`}
            </span>
          </div>
        </button>
      )}
    </section>
  );
}
