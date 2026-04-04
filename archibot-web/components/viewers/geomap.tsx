"use client";

import { useEffect, useRef, useState } from "react";
import type GeoJSON from "geojson";
import maplibregl, { type GeoJSONSource, type Map as MapLibreMap, type StyleSpecification } from "maplibre-gl";
import { ChevronDown, Layers3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

const OPENFREEMAP_STYLE_URL = "https://tiles.openfreemap.org/styles/bright";
const OSM_RASTER_TILES = ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"];
const SATELLITE_TILES = [
  "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
];
const CONTOUR_LIBRARY_URL = "https://unpkg.com/maplibre-contour@0.0.5/dist/index.min.js";
const CONTOUR_DEM_URL = "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png";
const BASEMAP_SOURCE_ID = "geomap-basemap-source";
const BASEMAP_LAYER_ID = "geomap-basemap-layer";
const OVERLAY_SOURCE_ID = "geomap-overlay-source";
const OVERLAY_FILL_LAYER_ID = "geomap-overlay-fill";
const OVERLAY_LINE_LAYER_ID = "geomap-overlay-line";
const CONTOUR_SOURCE_ID = "geomap-contour-source";
const CONTOUR_LAYER_ID = "contours";
const INTERNAL_LAYER_IDS = new Set([
  BASEMAP_LAYER_ID,
  OVERLAY_FILL_LAYER_ID,
  OVERLAY_LINE_LAYER_ID,
]);
const DEFAULT_CENTER: [number, number] = [-7.6215, 33.5892];
const DEFAULT_ZOOM = 15.2;

let contourLibraryPromise: Promise<void> | null = null;
let contourProtocolReady = false;
let contourTileUrl: string | null = null;

export type GeoMapBasemap = "none" | "raster" | "satellite";

export type GeoMapProps = {
  basemap?: GeoMapBasemap;
  center?: [number, number];
  className?: string;
  defaultZoom?: number;
  enableContours?: boolean;
  geojson?: GeoJSON.FeatureCollection;
  layerColors?: Record<string, string>;
  layerZoomRanges?: Record<string, { min?: number; max?: number }>;
  maxZoom?: number;
  minZoom?: number;
  showLayerControl?: boolean;
  showZoomHud?: boolean;
};

type LayerEntry = {
  id: string;
  type: string;
  source: string;
  sourceLayer: string;
  visible: boolean;
  color: string | null;
};

type HoverTooltip = {
  x: number;
  y: number;
  title: string;
  detail: string | null;
};

function emptyFeatureCollection(): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: [],
  };
}

function getColorPaintKey(layerType: string) {
  if (layerType === "fill" || layerType === "fill-extrusion" || layerType === "background") {
    return `${layerType}-color`;
  }

  if (layerType === "line") {
    return "line-color";
  }

  if (layerType === "symbol") {
    return "text-color";
  }

  return null;
}

function darkenHexColor(color: string, amount = 0.08) {
  const normalized = color.trim();
  const match = normalized.match(/^#([0-9a-f]{6})$/i);
  if (!match) return color;

  const channels = [0, 2, 4].map((index) => Number.parseInt(match[1].slice(index, index + 2), 16));
  const next = channels.map((channel) =>
    Math.max(0, Math.min(255, Math.round(channel * (1 - amount)))),
  );

  return `#${next.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
}

function extractPaintColor(map: MapLibreMap, layerId: string, layerType: string) {
  const paintKey = getColorPaintKey(layerType);
  if (!paintKey) return null;

  const value = map.getPaintProperty(layerId, paintKey);
  return typeof value === "string" ? value : null;
}

function formatLayerLabel(value: string) {
  return value
    .split(/[-_]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function readLayerState(map: MapLibreMap): LayerEntry[] {
  return (map.getStyle().layers ?? [])
    .filter((layer) => !INTERNAL_LAYER_IDS.has(layer.id))
    .map((layer) => ({
      id: layer.id,
      type: layer.type,
      source: "source" in layer && typeof layer.source === "string" ? layer.source : "style",
      sourceLayer:
        "source-layer" in layer && typeof layer["source-layer"] === "string"
          ? layer["source-layer"]
          : "style",
      visible: map.getLayoutProperty(layer.id, "visibility") !== "none",
      color: extractPaintColor(map, layer.id, layer.type),
    }));
}

function getHoverableLayerIds(map: MapLibreMap) {
  return (map.getStyle().layers ?? [])
    .filter(
      (layer) =>
        !INTERNAL_LAYER_IDS.has(layer.id) &&
        (layer.type === "fill" || layer.type === "fill-extrusion") &&
        layer.id !== "background" &&
        map.getLayoutProperty(layer.id, "visibility") !== "none",
    )
    .map((layer) => layer.id);
}

function getHoverDetail(feature: maplibregl.MapGeoJSONFeature) {
  const properties = feature.properties as Record<string, unknown> | null | undefined;
  const featureName = typeof properties?.name === "string" ? properties.name : null;
  const subclass = typeof properties?.subclass === "string" ? properties.subclass : null;
  const featureClass = typeof properties?.class === "string" ? properties.class : null;
  const sourceLayer = typeof feature.sourceLayer === "string" ? feature.sourceLayer : null;

  return {
    title: featureName ?? formatLayerLabel(subclass ?? featureClass ?? feature.layer.id),
    detail: featureName ? formatLayerLabel(subclass ?? featureClass ?? sourceLayer ?? feature.layer.id) : null,
  };
}

async function waitForSizedContainer(
  element: HTMLDivElement,
  isDisposed: () => boolean,
  maxFrames = 60,
) {
  for (let index = 0; index < maxFrames; index += 1) {
    if (isDisposed()) return false;
    if (element.clientWidth > 0 && element.clientHeight > 0) return true;
    await new Promise<void>((resolve) => window.requestAnimationFrame(() => resolve()));
  }

  return element.clientWidth > 0 && element.clientHeight > 0;
}

async function loadOpenFreeMapStyle(signal: AbortSignal) {
  const response = await fetch(OPENFREEMAP_STYLE_URL, { signal });
  if (!response.ok) {
    throw new Error(`OpenFreeMap style request failed with status ${response.status}`);
  }

  const style = await response.json() as StyleSpecification;
  if (!style.projection) {
    style.projection = { type: "mercator" };
  }

  return style;
}

function loadContourLibrary() {
  if (typeof window === "undefined") {
    return Promise.resolve();
  }

  if ((window as Window & { mlcontour?: unknown }).mlcontour) {
    return Promise.resolve();
  }

  if (contourLibraryPromise) {
    return contourLibraryPromise;
  }

  contourLibraryPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${CONTOUR_LIBRARY_URL}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Failed to load maplibre-contour.")), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = CONTOUR_LIBRARY_URL;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load maplibre-contour."));
    document.head.appendChild(script);
  });

  return contourLibraryPromise;
}

async function ensureContourLayer(map: MapLibreMap) {
  await loadContourLibrary();

  const mlcontour = (window as Window & {
    mlcontour?: {
      DemSource: new (options: {
        url: string;
        encoding: "mapbox" | "terrarium";
        maxzoom: number;
        worker: boolean;
      }) => {
        setupMaplibre: (lib: typeof maplibregl) => void;
        contourProtocolUrl: (options: {
          overzoom: number;
          thresholds: Record<number, [number, number]>;
          elevationKey: string;
          levelKey: string;
          contourLayer: string;
        }) => string;
      };
    };
  }).mlcontour;

  if (!mlcontour) {
    throw new Error("maplibre-contour did not initialize correctly.");
  }

  if (!contourProtocolReady) {
    const demSource = new mlcontour.DemSource({
      url: CONTOUR_DEM_URL,
      encoding: "terrarium",
      maxzoom: 12,
      worker: true,
    });

    demSource.setupMaplibre(maplibregl);
    contourProtocolReady = true;
    contourTileUrl = demSource.contourProtocolUrl({
      overzoom: 1,
      thresholds: {
        5: [500, 2000],
        6: [250, 1000],
        7: [100, 500],
        8: [50, 200],
        9: [25, 100],
        10: [20, 100],
        11: [20, 100],
        12: [10, 50],
        13: [10, 50],
        14: [10, 50],
        15: [5, 20],
        16: [5, 20],
      },
      elevationKey: "ele",
      levelKey: "level",
      contourLayer: "contours",
    });
  }

  if (!contourTileUrl) {
    throw new Error("Contour source was not registered.");
  }

  if (!map.getSource(CONTOUR_SOURCE_ID)) {
    map.addSource(CONTOUR_SOURCE_ID, {
      type: "vector",
      tiles: [contourTileUrl],
      minzoom: 5,
      maxzoom: 16,
    });
  }

  if (!map.getLayer(CONTOUR_LAYER_ID)) {
    map.addLayer({
      id: CONTOUR_LAYER_ID,
      type: "line",
      source: CONTOUR_SOURCE_ID,
      "source-layer": "contours",
      minzoom: 5,
      paint: {
        "line-color": "#111111",
        "line-opacity": 0.6,
        "line-width": ["match", ["get", "level"], 1, 1, 0.5],
      },
    });
  }
}

function removeContourLayer(map: MapLibreMap) {
  if (map.getLayer(CONTOUR_LAYER_ID)) {
    map.removeLayer(CONTOUR_LAYER_ID);
  }
  if (map.getSource(CONTOUR_SOURCE_ID)) {
    map.removeSource(CONTOUR_SOURCE_ID);
  }
}

function getBasemapTiles(basemap: GeoMapBasemap) {
  if (basemap === "raster") {
    return OSM_RASTER_TILES;
  }

  if (basemap === "satellite") {
    return SATELLITE_TILES;
  }

  return null;
}

function syncBasemapLayer(map: MapLibreMap, basemap: GeoMapBasemap) {
  const tiles = getBasemapTiles(basemap);
  const hasLayer = Boolean(map.getLayer(BASEMAP_LAYER_ID));
  const hasSource = Boolean(map.getSource(BASEMAP_SOURCE_ID));

  if (!tiles) {
    if (hasLayer) map.removeLayer(BASEMAP_LAYER_ID);
    if (hasSource) map.removeSource(BASEMAP_SOURCE_ID);
    return;
  }

  if (hasLayer) {
    map.removeLayer(BASEMAP_LAYER_ID);
  }
  if (hasSource) {
    map.removeSource(BASEMAP_SOURCE_ID);
  }

  map.addSource(BASEMAP_SOURCE_ID, {
    type: "raster",
    tiles,
    tileSize: 256,
    attribution:
      basemap === "satellite"
        ? "Tiles © Esri"
        : "&copy; OpenStreetMap contributors",
  });

  const beforeId = (map.getStyle().layers ?? []).find(
    (layer) => layer.id !== "background" && !INTERNAL_LAYER_IDS.has(layer.id),
  )?.id;

  map.addLayer(
    {
      id: BASEMAP_LAYER_ID,
      type: "raster",
      source: BASEMAP_SOURCE_ID,
    },
    beforeId,
  );
}

function ensureOverlayLayers(map: MapLibreMap) {
  if (!map.getSource(OVERLAY_SOURCE_ID)) {
    map.addSource(OVERLAY_SOURCE_ID, {
      type: "geojson",
      data: emptyFeatureCollection(),
    });
  }

  if (!map.getLayer(OVERLAY_FILL_LAYER_ID)) {
    map.addLayer({
      id: OVERLAY_FILL_LAYER_ID,
      type: "fill",
      source: OVERLAY_SOURCE_ID,
      paint: {
        "fill-color": ["coalesce", ["get", "_fill"], ["get", "_color"], "#ef4444"],
        "fill-opacity": ["coalesce", ["get", "_opacity"], 0.32],
      },
    });
  }

  if (!map.getLayer(OVERLAY_LINE_LAYER_ID)) {
    map.addLayer({
      id: OVERLAY_LINE_LAYER_ID,
      type: "line",
      source: OVERLAY_SOURCE_ID,
      paint: {
        "line-color": ["coalesce", ["get", "_stroke"], ["get", "_color"], "#b91c1c"],
        "line-width": ["coalesce", ["get", "_width"], 2],
        "line-opacity": ["coalesce", ["get", "_strokeOpacity"], 0.9],
      },
    });
  }
}

function syncOverlayData(map: MapLibreMap, geojson?: GeoJSON.FeatureCollection) {
  ensureOverlayLayers(map);
  const source = map.getSource(OVERLAY_SOURCE_ID) as GeoJSONSource | undefined;
  if (!source) return;
  source.setData(geojson ?? emptyFeatureCollection());
}

function ensureHoverTransitions(map: MapLibreMap) {
  for (const layer of map.getStyle().layers ?? []) {
    if (INTERNAL_LAYER_IDS.has(layer.id)) continue;
    if (layer.type !== "fill" && layer.type !== "fill-extrusion") continue;
    const paintKey = getColorPaintKey(layer.type);
    if (!paintKey) continue;

    map.setPaintProperty(layer.id, `${paintKey}-transition`, {
      duration: 1000,
      delay: 0,
    });
  }
}

function setHoveredLayerColor(
  map: MapLibreMap,
  hoveredLayerId: string | null,
  originalColors: Map<string, string>,
  activeLayerRef: { current: string | null },
) {
  const previousLayerId = activeLayerRef.current;
  if (previousLayerId && previousLayerId !== hoveredLayerId && map.getLayer(previousLayerId)) {
    const previousLayer = map.getStyle().layers?.find((layer) => layer.id === previousLayerId);
    const previousColor = originalColors.get(previousLayerId);
    const previousPaintKey = previousLayer ? getColorPaintKey(previousLayer.type) : null;
    if (previousColor && previousPaintKey) {
      map.setPaintProperty(previousLayerId, previousPaintKey, previousColor);
    }
  }

  if (!hoveredLayerId) {
    activeLayerRef.current = null;
    return;
  }

  if (hoveredLayerId === previousLayerId) {
    return;
  }

  const hoveredLayer = map.getStyle().layers?.find((layer) => layer.id === hoveredLayerId);
  const hoveredColor = originalColors.get(hoveredLayerId);
  const hoveredPaintKey = hoveredLayer ? getColorPaintKey(hoveredLayer.type) : null;
  if (!hoveredLayer || !hoveredColor || !hoveredPaintKey) {
    activeLayerRef.current = null;
    return;
  }

  map.setPaintProperty(hoveredLayerId, hoveredPaintKey, darkenHexColor(hoveredColor));
  activeLayerRef.current = hoveredLayerId;
}

function applyLayerConfiguration(
  map: MapLibreMap,
  layerColors: Record<string, string>,
  layerZoomRanges: Record<string, { min?: number; max?: number }>,
) {
  const allowedLayerIds = new Set(Object.keys(layerColors));

  for (const layer of map.getStyle().layers ?? []) {
    if (INTERNAL_LAYER_IDS.has(layer.id)) continue;
    const paintKey = getColorPaintKey(layer.type);
    const configuredColor = layerColors[layer.id];
    const zoomRange = layerZoomRanges[layer.id];

    if (paintKey && typeof configuredColor === "string" && map.getLayer(layer.id)) {
      map.setPaintProperty(layer.id, paintKey, configuredColor);
    }

    if (zoomRange && map.getLayer(layer.id)) {
      map.setLayerZoomRange(layer.id, zoomRange.min ?? 0, zoomRange.max ?? 24);
    }

    if (map.getLayer(layer.id)) {
      map.setLayoutProperty(
        layer.id,
        "visibility",
        allowedLayerIds.has(layer.id) ? "visible" : "none",
      );
    }
  }
}

export function GeoMap({
  basemap = "raster",
  center = DEFAULT_CENTER,
  className,
  defaultZoom = DEFAULT_ZOOM,
  enableContours = false,
  geojson,
  layerColors = {},
  layerZoomRanges = {},
  maxZoom = 20,
  minZoom = 5,
  showLayerControl = true,
  showZoomHud = true,
}: GeoMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const hoverableLayerIdsRef = useRef<string[]>([]);
  const hoveredLayerIdRef = useRef<string | null>(null);
  const originalLayerColorsRef = useRef(new Map<string, string>());
  const initialConfigRef = useRef({
    basemap,
    center,
    defaultZoom,
    enableContours,
    geojson,
    layerColors,
    layerZoomRanges,
    maxZoom,
    minZoom,
  });
  const [layers, setLayers] = useState<LayerEntry[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [showMoreLayers, setShowMoreLayers] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(defaultZoom);
  const [hoverTooltip, setHoverTooltip] = useState<HoverTooltip | null>(null);

  const configuredLayerIds = Object.keys(layerColors);
  const configuredLayerSet = new Set(configuredLayerIds);

  function syncLayerState(map: MapLibreMap) {
    const nextLayers = readLayerState(map);
    hoverableLayerIdsRef.current = getHoverableLayerIds(map);
    originalLayerColorsRef.current = new Map(
      nextLayers
        .filter((layer): layer is LayerEntry & { color: string } =>
          (layer.type === "fill" || layer.type === "fill-extrusion") && typeof layer.color === "string",
        )
        .map((layer) => [layer.id, layer.color]),
    );
    setLayers(nextLayers);
  }

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    let disposed = false;
    let resizeFrame = 0;
    const resizeTimeouts: number[] = [];
    const styleController = new AbortController();
    const container = mapContainerRef.current;
    let observer: ResizeObserver | null = null;
    let removeWindowListeners = () => {};

    const start = async () => {
      try {
        setMapReady(false);
        const hasSize = await waitForSizedContainer(container, () => disposed);
        if (!hasSize || disposed) return;

        const style = await loadOpenFreeMapStyle(styleController.signal);
        if (disposed) return;
        const initialConfig = initialConfigRef.current;

        const map = new maplibregl.Map({
          container,
          style,
          center: initialConfig.center,
          zoom: initialConfig.defaultZoom,
          minZoom: initialConfig.minZoom,
          maxZoom: initialConfig.maxZoom,
          pitch: 0,
          bearing: 0,
          attributionControl: false,
          hash: false,
        });

        mapRef.current = map;

        const forceResize = () => {
          if (disposed) return;
          map.resize();
        };

        const syncZoom = () => {
          if (disposed) return;
          setZoomLevel(Number(map.getZoom().toFixed(2)));
        };

        const resetHover = () => {
          setHoveredLayerColor(map, null, originalLayerColorsRef.current, hoveredLayerIdRef);
          setHoverTooltip(null);
          map.getCanvas().style.cursor = "";
        };

        const handleMouseMove = (event: maplibregl.MapMouseEvent) => {
          if (disposed) return;

          const visiblePolygonLayers = hoverableLayerIdsRef.current;
          if (visiblePolygonLayers.length === 0) {
            resetHover();
            return;
          }

          const hoveredFeature = map.queryRenderedFeatures(event.point, {
            layers: visiblePolygonLayers,
          }).find((feature) => feature.geometry.type === "Polygon" || feature.geometry.type === "MultiPolygon");

          if (!hoveredFeature) {
            resetHover();
            return;
          }

          setHoveredLayerColor(
            map,
            hoveredFeature.layer.id,
            originalLayerColorsRef.current,
            hoveredLayerIdRef,
          );
          const { title, detail } = getHoverDetail(hoveredFeature);
          setHoverTooltip({
            x: event.point.x,
            y: event.point.y,
            title,
            detail,
          });
          map.getCanvas().style.cursor = "pointer";
        };

        const handleLoad = async () => {
          if (disposed) return;
          setMapError(null);

          try {
            syncBasemapLayer(map, initialConfig.basemap);
            if (initialConfig.enableContours) {
              await ensureContourLayer(map);
            } else {
              removeContourLayer(map);
            }
            syncOverlayData(map, initialConfig.geojson);
            applyLayerConfiguration(map, initialConfig.layerColors, initialConfig.layerZoomRanges);
            ensureHoverTransitions(map);
          } catch (error) {
            if (!disposed) {
              const message =
                error instanceof Error
                  ? error.message
                  : "Failed to initialize map layers.";
              setMapError(message);
            }
          }

          syncLayerState(map);
          syncZoom();

          resizeFrame = window.requestAnimationFrame(() => {
            resizeFrame = window.requestAnimationFrame(() => {
              if (disposed) return;
              forceResize();
              syncLayerState(map);
              syncZoom();
            });
          });

          for (const delay of [0, 80, 200, 400, 800]) {
            const timeoutId = window.setTimeout(() => {
              if (disposed) return;
              forceResize();
              syncLayerState(map);
              syncZoom();
            }, delay);
            resizeTimeouts.push(timeoutId);
          }

          const revealTimeoutId = window.setTimeout(() => {
            if (disposed) return;
            forceResize();
            syncLayerState(map);
            syncZoom();
            setMapReady(true);
          }, 220);
          resizeTimeouts.push(revealTimeoutId);
        };

        const handleError = (event: { error?: unknown }) => {
          if (disposed) return;
          const message =
            event.error instanceof Error
              ? event.error.message
              : "Map style or tiles failed to load.";
          setMapError(message);
        };

        map.on("error", handleError);
        map.on("load", handleLoad);
        map.on("zoom", syncZoom);
        map.on("mousemove", handleMouseMove);
        map.on("mouseleave", resetHover);

        observer = new ResizeObserver(() => {
          forceResize();
        });
        observer.observe(container);

        const onWindowLoad = () => forceResize();
        const onVisibilityChange = () => {
          if (document.visibilityState === "visible") {
            forceResize();
          }
        };

        window.addEventListener("load", onWindowLoad);
        document.addEventListener("visibilitychange", onVisibilityChange);
        removeWindowListeners = () => {
          window.removeEventListener("load", onWindowLoad);
          document.removeEventListener("visibilitychange", onVisibilityChange);
        };
      } catch (error) {
        if (disposed) return;
        const message =
          error instanceof Error
            ? error.message
            : "Map style or tiles failed to load.";
        setMapError(message);
      }
    };

    void start();

    return () => {
      disposed = true;
      styleController.abort();
      if (resizeFrame) {
        window.cancelAnimationFrame(resizeFrame);
      }
      for (const timeoutId of resizeTimeouts) {
        window.clearTimeout(timeoutId);
      }
      observer?.disconnect();
      removeWindowListeners();
      if (mapRef.current) {
        setHoveredLayerColor(mapRef.current, null, originalLayerColorsRef.current, hoveredLayerIdRef);
      }
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.setCenter(center);
    if (minZoom !== undefined) {
      map.setMinZoom(minZoom);
    }
    if (maxZoom !== undefined) {
      map.setMaxZoom(maxZoom);
    }
    map.setZoom(defaultZoom);
    setZoomLevel(Number(map.getZoom().toFixed(2)));
  }, [center, defaultZoom, maxZoom, minZoom]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.loaded()) return;

    const apply = async () => {
      try {
        setHoveredLayerColor(map, null, originalLayerColorsRef.current, hoveredLayerIdRef);
        setHoverTooltip(null);
        syncBasemapLayer(map, basemap);
        if (enableContours) {
          await ensureContourLayer(map);
        } else {
          removeContourLayer(map);
        }
        syncOverlayData(map, geojson);
        applyLayerConfiguration(map, layerColors, layerZoomRanges);
        ensureHoverTransitions(map);
        syncLayerState(map);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to update map layers.";
        setMapError(message);
      }
    };

    void apply();
  }, [basemap, enableContours, geojson, layerColors, layerZoomRanges]);

  function setLayerVisibility(layerId: string, visible: boolean) {
    const map = mapRef.current;
    if (!map?.getLayer(layerId)) return;

    setHoveredLayerColor(map, null, originalLayerColorsRef.current, hoveredLayerIdRef);
    setHoverTooltip(null);
    map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
    setLayers((current) =>
      current.map((layer) => (layer.id === layerId ? { ...layer, visible } : layer)),
    );
    hoverableLayerIdsRef.current = getHoverableLayerIds(map);
  }

  function setAllLayersVisibility(visible: boolean) {
    const map = mapRef.current;
    if (!map) return;

    setHoveredLayerColor(map, null, originalLayerColorsRef.current, hoveredLayerIdRef);
    setHoverTooltip(null);
    setLayers((current) =>
      current.map((layer) => {
        if (map.getLayer(layer.id)) {
          map.setLayoutProperty(layer.id, "visibility", visible ? "visible" : "none");
        }

        return { ...layer, visible };
      }),
    );
    hoverableLayerIdsRef.current = getHoverableLayerIds(map);
  }

  const preferredLayers = configuredLayerIds
    .map((layerId) => layers.find((layer) => layer.id === layerId))
    .filter((layer): layer is LayerEntry => Boolean(layer));
  const extraLayers = layers.filter((layer) => !configuredLayerSet.has(layer.id));

  return (
    <section className={`absolute inset-0 overflow-hidden ${className ?? ""}`}>
      <div
        ref={mapContainerRef}
        className={`absolute inset-0 transition-opacity duration-200 ${mapReady ? "opacity-100" : "opacity-0"}`}
      />

      {!mapReady && !mapError ? (
        <div className="pointer-events-none absolute inset-0 z-10 bg-white" />
      ) : null}

      {mapError ? (
        <div className="pointer-events-none absolute inset-x-0 top-4 z-10 flex justify-center px-4">
          <div className="max-w-xl rounded-2xl border border-rose-200 bg-white/95 px-4 py-3 text-sm text-rose-700 shadow-xl">
            {mapError}
          </div>
        </div>
      ) : null}

      {hoverTooltip ? (
        <div
          className="pointer-events-none absolute z-10"
          style={{
            left: hoverTooltip.x + 14,
            top: hoverTooltip.y + 14,
          }}
        >
          <div className="max-w-56 rounded-xl border border-white/70 bg-white/95 px-3 py-2 shadow-lg shadow-slate-900/10 backdrop-blur-md">
            <p className="text-sm font-medium text-slate-950">{hoverTooltip.title}</p>
            {hoverTooltip.detail ? (
              <p className="text-xs text-slate-500">{hoverTooltip.detail}</p>
            ) : null}
          </div>
        </div>
      ) : null}

      {showZoomHud ? (
        <div className="pointer-events-none absolute bottom-5 left-5 z-10">
          <div className="rounded-full border border-white/60 bg-white/90 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-lg shadow-slate-900/10 backdrop-blur-md">
            Zoom {zoomLevel}
          </div>
        </div>
      ) : null}

      {showLayerControl ? (
        <div className="pointer-events-none absolute inset-0 z-10">
          <div className="pointer-events-auto absolute bottom-5 right-5 z-10">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  size="icon"
                  variant="outline"
                  className="h-12 w-12 rounded-full border-white/60 bg-white/90 shadow-xl shadow-slate-900/15 backdrop-blur-md"
                  aria-label="Toggle map layers"
                >
                  <Layers3 className="h-5 w-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end" className="w-80 overflow-hidden p-0">
                <div className="border-b px-4 py-3">
                  <p className="text-sm font-semibold text-slate-950">Layers</p>
                  <p className="text-xs text-slate-500">Toggle live map style layers.</p>
                </div>
                <div className="flex items-center gap-2 border-b px-4 py-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 rounded-full px-3"
                    onClick={() => setAllLayersVisibility(true)}
                  >
                    Show all
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 rounded-full px-3"
                    onClick={() => setAllLayersVisibility(false)}
                  >
                    Hide all
                  </Button>
                </div>
                <div className="max-h-[60vh] min-h-56 overflow-y-auto p-2">
                  {layers.length === 0 ? (
                    <div className="flex min-h-52 items-center justify-center px-4 text-center text-sm text-slate-500">
                      Waiting for map layers to load.
                    </div>
                  ) : (
                    <>
                      {preferredLayers.map((layer) => (
                        <div
                          key={layer.id}
                          role="button"
                          tabIndex={0}
                          onClick={() => setLayerVisibility(layer.id, !layer.visible)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              setLayerVisibility(layer.id, !layer.visible);
                            }
                          }}
                          className="flex w-full items-start gap-3 rounded-2xl px-3 py-2 text-left transition hover:bg-slate-100"
                        >
                          <Checkbox
                            className="mt-0.5"
                            checked={layer.visible}
                            onCheckedChange={(checked) => setLayerVisibility(layer.id, checked === true)}
                            aria-label={`Toggle ${layer.id}`}
                          />
                          <span
                            className="mt-0.5 h-3.5 w-3.5 shrink-0 rounded-[3px] border border-slate-300"
                            style={{ backgroundColor: layer.color ?? "#ffffff" }}
                            aria-hidden="true"
                          />
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-sm font-medium text-slate-950">{layer.id}</span>
                            <span className="block text-xs text-slate-500">
                              {layer.type} layer from {layer.source}
                            </span>
                          </span>
                        </div>
                      ))}

                      {extraLayers.length > 0 ? (
                        <div className="pt-2">
                          <button
                            type="button"
                            className="flex w-full items-center justify-between border-t px-3 py-3 text-left"
                            onClick={() => setShowMoreLayers((current) => !current)}
                          >
                            <span className="text-sm font-medium text-slate-950">More Layers</span>
                            <ChevronDown
                              className={`h-4 w-4 text-slate-500 transition-transform${showMoreLayers ? " rotate-180" : ""}`}
                            />
                          </button>

                          {showMoreLayers ? (
                            <div>
                              {extraLayers.map((layer) => (
                                <div
                                  key={layer.id}
                                  role="button"
                                  tabIndex={0}
                                  onClick={() => setLayerVisibility(layer.id, !layer.visible)}
                                  onKeyDown={(event) => {
                                    if (event.key === "Enter" || event.key === " ") {
                                      event.preventDefault();
                                      setLayerVisibility(layer.id, !layer.visible);
                                    }
                                  }}
                                  className="flex w-full items-start gap-3 rounded-2xl px-3 py-2 text-left transition hover:bg-slate-100"
                                >
                                  <Checkbox
                                    className="mt-0.5"
                                    checked={layer.visible}
                                    onCheckedChange={(checked) => setLayerVisibility(layer.id, checked === true)}
                                    aria-label={`Toggle ${layer.id}`}
                                  />
                                  <span
                                    className="mt-0.5 h-3.5 w-3.5 shrink-0 rounded-[3px] border border-slate-300"
                                    style={{ backgroundColor: layer.color ?? "#ffffff" }}
                                    aria-hidden="true"
                                  />
                                  <span className="min-w-0 flex-1">
                                    <span className="block truncate text-sm font-medium text-slate-950">{layer.id}</span>
                                    <span className="block text-xs text-slate-500">
                                      {layer.type} layer from {layer.source}
                                    </span>
                                  </span>
                                </div>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      ) : null}
    </section>
  );
}
