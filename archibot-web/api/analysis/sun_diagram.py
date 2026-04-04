"""Sun path diagram — GeoJSON computation.

Produces a stereographic sun-path FeatureCollection in WGS84 for rendering
in MapLibre.  All geometry is computed in an AEQD (azimuthal equidistant)
projection centred on the site so that distances are true metres, then
projected back to WGS84 [lng, lat].

Stereographic convention
  - azimuth  = angle from North, clockwise
  - radius   = compass_r × (1 − altitude / 90°)
  → horizon (alt 0°) sits on the outer compass ring
  → zenith   (alt 90°) sits at the origin

Primitive rendering properties on every feature (read by the generic
MapLibre interpreter in the frontend — no semantic knowledge needed):

  _type    : "line" | "circle" | "label"
  _color   : hex string
  _opacity : 0.0–1.0
  _width   : line-width (lines) or circle-radius (circles)
  _dash    : true | false  (lines only)
  _text    : string (labels only)
  _size    : font size in px (labels only)
  _bold    : true | false (labels only)
  _zIndex  : integer 1–9 (higher = drawn on top)
"""

from __future__ import annotations

import math

try:
    import pyproj as _pyproj
    _GEO_AVAILABLE = True
except ImportError:
    _GEO_AVAILABLE = False

# ── solar geometry ──────────────────────────────────────────────────────────


def _sun_arc_aeqd_points(
    lat_deg: float,
    declination_deg: float,
    compass_r: float,
    n: int = 300,
) -> list[tuple[float, float]] | None:
    """Stereographic arc in AEQD metre-space.  Returns None for polar night."""
    lat = math.radians(lat_deg)
    dec = math.radians(declination_deg)
    cos_ha_sr = -math.tan(lat) * math.tan(dec)
    if cos_ha_sr > 1.0:
        return None
    ha_sr = math.acos(max(-1.0, min(1.0, cos_ha_sr)))
    pts: list[tuple[float, float]] = []
    for i in range(n):
        ha = ha_sr * (2 * i / (n - 1) - 1)
        sin_alt = (math.sin(lat) * math.sin(dec)
                   + math.cos(lat) * math.cos(dec) * math.cos(ha))
        alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
        if alt < 0:
            continue
        cos_az = ((math.sin(dec) - math.sin(lat) * math.sin(math.radians(alt)))
                  / (math.cos(lat) * math.cos(math.radians(alt)) + 1e-12))
        az = math.degrees(math.acos(max(-1.0, min(1.0, cos_az))))
        if ha > 0:
            az = 360.0 - az
        r = compass_r * (1.0 - alt / 90.0)
        ar = math.radians(az)
        pts.append((r * math.sin(ar), r * math.cos(ar)))
    return pts if pts else None


# ── compass geometry helpers ────────────────────────────────────────────────

# 16 directions: (azimuth_deg, label, is_cardinal)
_DIRECTIONS_16 = [
    (0,     "N",   True),
    (22.5,  "NNE", False),
    (45,    "NE",  False),
    (67.5,  "ENE", False),
    (90,    "E",   True),
    (112.5, "ESE", False),
    (135,   "SE",  False),
    (157.5, "SSE", False),
    (180,   "S",   True),
    (202.5, "SSW", False),
    (225,   "SW",  False),
    (247.5, "WSW", False),
    (270,   "W",   True),
    (292.5, "WNW", False),
    (315,   "NW",  False),
    (337.5, "NNW", False),
]

# tick every 2°; cardinal at 45° multiples, intercardinal at 22.5°, major at 10°
def _tick_kind(a: float) -> str:
    if a % 45 == 0:
        return "cardinal"
    if a % 22 == 0 or a % 23 == 0:   # ~22.5° intercardinals
        return "intercardinal"
    if a % 10 == 0:
        return "major"
    return "minor"


# ── primitive style presets ─────────────────────────────────────────────────

def _line(color: str, width: float, opacity: float = 1.0,
          dash: bool = False, z: int = 5) -> dict:
    return {"_type": "line", "_color": color, "_width": width,
            "_opacity": opacity, "_dash": dash, "_zIndex": z}

def _circle(color: str, radius: float, opacity: float = 1.0,
            z: int = 5) -> dict:
    return {"_type": "circle", "_color": color, "_width": radius,
            "_opacity": opacity, "_zIndex": z}

def _label(text: str, color: str, size: float,
           bold: bool = False, opacity: float = 1.0, z: int = 5) -> dict:
    return {"_type": "label", "_text": text, "_color": color,
            "_size": size, "_bold": bold, "_opacity": opacity, "_zIndex": z}


# ── main public function ────────────────────────────────────────────────────

def compute_sun_path_geojson(
    site_coordinates,
    site_center,
) -> dict | None:
    """Return a GeoJSON FeatureCollection or None on failure."""
    if not _GEO_AVAILABLE:
        return None
    if not isinstance(site_center, (list, tuple)) or len(site_center) < 2:
        return None

    lng, lat = float(site_center[0]), float(site_center[1])

    aeqd_crs = _pyproj.CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat} +lon_0={lng} +datum=WGS84 +units=m")
    wgs84 = _pyproj.CRS("EPSG:4326")
    to_aeqd = _pyproj.Transformer.from_crs(wgs84, aeqd_crs, always_xy=True)
    to_wgs84 = _pyproj.Transformer.from_crs(aeqd_crs, wgs84, always_xy=True)

    def w(x_m: float, y_m: float) -> list[float]:
        lo, la = to_wgs84.transform(x_m, y_m)
        return [lo, la]

    def feat(props: dict, geometry: dict) -> dict:
        return {"type": "Feature", "properties": props, "geometry": geometry}

    def line_geom(coords: list) -> dict:
        return {"type": "LineString", "coordinates": coords}

    def polygon_geom(rings: list) -> dict:
        return {"type": "Polygon", "coordinates": rings}

    def point_geom(coord: list) -> dict:
        return {"type": "Point", "coordinates": coord}

    # ── parcel → compass_r ────────────────────────────────────────────────
    parcel_rings: list[list[tuple[float, float]]] = []
    all_pts: list[tuple[float, float]] = []
    if isinstance(site_coordinates, list):
        for ring in site_coordinates:
            if not isinstance(ring, list) or len(ring) < 3:
                continue
            ring_pts: list[tuple[float, float]] = []
            for pt in ring:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    p = to_aeqd.transform(float(pt[0]), float(pt[1]))
                elif isinstance(pt, dict):
                    p = to_aeqd.transform(float(pt.get("lng", 0)), float(pt.get("lat", 0)))
                else:
                    continue
                ring_pts.append(p)
                all_pts.append(p)
            if len(ring_pts) >= 3:
                parcel_rings.append(ring_pts)

    max_extent = max((math.hypot(x, y) for x, y in all_pts), default=80.0)
    compass_r = max(max_extent * 1.30, 50.0)
    label_r   = compass_r * 1.18
    ann_r     = compass_r * 1.07

    features: list[dict] = []

    # ── parcel — transparent fill, black border ───────────────────────────
    for ring_pts in parcel_rings:
        coords = [w(x, y) for x, y in ring_pts]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        # fill (invisible — just to register the polygon shape)
        features.append(feat(
            {**_line("#000000", 0, 0), "_type": "fill", "_zIndex": 2},
            polygon_geom([coords]),
        ))
        # outline
        features.append(feat(
            _line("#000000", 1.5, 1.0, z=3),
            line_geom(coords),
        ))

    # ── altitude rings (10°…80°) — thin dashed grey ───────────────────────
    for alt_deg in range(10, 90, 10):
        r = compass_r * (1.0 - alt_deg / 90.0)
        n_alt = 128
        alt_coords = [
            w(r * math.sin(math.radians(a)), r * math.cos(math.radians(a)))
            for a in [i * 360 / n_alt for i in range(n_alt + 1)]
        ]
        features.append(feat(
            _line("#94a3b8", 0.6, 0.7, dash=True, z=2),
            line_geom(alt_coords),
        ))

    # ── compass outer ring ────────────────────────────────────────────────
    n_circle = 256
    ring_coords = [
        w(compass_r * math.sin(math.radians(a)),
          compass_r * math.cos(math.radians(a)))
        for a in [i * 360 / n_circle for i in range(n_circle + 1)]
    ]
    features.append(feat(
        _line("#334155", 1.2, 1.0, z=4),
        line_geom(ring_coords),
    ))

    # ── compass ticks ─────────────────────────────────────────────────────
    tick_lengths = {"cardinal": 0.09, "intercardinal": 0.065, "major": 0.045, "minor": 0.022}
    tick_styles  = {
        "cardinal":     _line("#1e293b", 2.0, 1.0,  z=5),
        "intercardinal":_line("#475569", 1.4, 1.0,  z=5),
        "major":        _line("#64748b", 1.0, 1.0,  z=5),
        "minor":        _line("#94a3b8", 0.5, 0.8,  z=5),
    }
    for a in range(0, 360, 2):
        kind = _tick_kind(float(a))
        tl = tick_lengths[kind]
        ar = math.radians(a)
        sx, sy = math.sin(ar), math.cos(ar)
        inner = w(sx * compass_r * (1 - tl), sy * compass_r * (1 - tl))
        outer = w(sx * compass_r,             sy * compass_r)
        features.append(feat(tick_styles[kind], line_geom([inner, outer])))

    # ── radial axes: N–S, E–W, NE–SW, NW–SE ─────────────────────────────
    for az_deg in (0, 90, 45, 135):
        ar = math.radians(az_deg)
        sx, sy = math.sin(ar), math.cos(ar)
        features.append(feat(
            _line("#cbd5e1", 0.6, 0.6, z=2),
            line_geom([w(-sx * compass_r, -sy * compass_r),
                       w( sx * compass_r,  sy * compass_r)]),
        ))

    # ── degree annotations on the periphery (every 30°) ──────────────────
    for a in range(0, 360, 30):
        ar = math.radians(a)
        features.append(feat(
            _label(f"{a}°", "#64748b", 9, bold=False, z=7),
            point_geom(w(math.sin(ar) * ann_r, math.cos(ar) * ann_r)),
        ))

    # ── direction labels (16 directions) ─────────────────────────────────
    for az_deg, label, cardinal in _DIRECTIONS_16:
        ar = math.radians(az_deg)
        color = "#1e293b" if cardinal else "#475569"
        size  = 13 if cardinal else 9
        features.append(feat(
            _label(label, color, size, bold=cardinal, z=8),
            point_geom(w(math.sin(ar) * label_r, math.cos(ar) * label_r)),
        ))

    # ── sun arcs + markers ────────────────────────────────────────────────
    seasons = [
        ("summer",  23.45,  "#f59e0b", False, 9,  2.0, 6),
        ("equinox",  0.0,   "#fbbf24", True,  7,  2.0, 6),
        ("winter", -23.45,  "#fed7aa", True,  5,  2.0, 6),
    ]
    marker_radii = {"summer": 5, "equinox": 4, "winter": 3}
    for season_id, dec, color, dash, n_markers, width, z in seasons:
        pts_m = _sun_arc_aeqd_points(lat, dec, compass_r)
        if pts_m is None:
            continue
        coords = [w(x, y) for x, y in pts_m]
        features.append(feat(
            _line(color, width, 0.9, dash=dash, z=z),
            line_geom(coords),
        ))
        n = len(coords)
        if n >= 2:
            for i in range(n_markers):
                idx = int(round(i * (n - 1) / (n_markers - 1)))
                features.append(feat(
                    _circle(color, marker_radii[season_id], 0.95, z=z + 1),
                    point_geom(coords[idx]),
                ))

    return {"type": "FeatureCollection", "features": features}
