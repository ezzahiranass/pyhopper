"""Write workspace artifacts directly onto subdomain documents."""

from __future__ import annotations

import io
import json
import struct
import time
from urllib.parse import quote
from uuid import uuid4

from firebase_admin import firestore as admin_firestore
from google.cloud.firestore_v1.base_query import FieldFilter

try:
    import contextily as _cx
    import geopandas as _gpd
    import pyproj as _pyproj
    from shapely.geometry import Point as _Point, Polygon as _Polygon
    from shapely.ops import transform as _shapely_transform, unary_union as _unary_union
    _GEO_AVAILABLE = True
except ImportError:  # pragma: no cover - optional runtime dependency
    _GEO_AVAILABLE = False

from analysis.sun_diagram import (
    compute_sun_path_geojson as _compute_sun_path_geojson,
    _sun_arc_aeqd_points,
)

from .client import get_firestore_client, get_storage_bucket

SITE_ANALYSIS_SUBDOMAIN_COPY = {
    "geolocation-parcel": {
        "summary_title": "Parcel Summary",
        "summary": (
            "The parcel footprint is suitable for a first-pass study. "
            "Assume boundary information is provisional and should be validated against cadastral data."
        ),
        "takeaway_title": "Initial Read",
        "takeaway": (
            "Use the current project center and analysis radius as the coordination anchor for all downstream site studies."
        ),
    },
    "topography": {
        "summary_title": "Terrain Read",
        "summary": (
            "Topography appears manageable at concept stage. "
            "Assume grading strategy can be resolved with a limited amount of cut-and-fill unless survey data proves otherwise."
        ),
        "takeaway_title": "Potential Action",
        "takeaway": (
            "Prepare for one primary building platform and keep circulation gradients conservative until detailed contours arrive."
        ),
    },
    "climate-sun-wind": {
        "summary_title": "Climate Snapshot",
        "summary": (
            "Solar exposure is assumed to be strong across the site envelope, with wind comfort becoming most relevant at edges and open exterior zones."
        ),
        "takeaway_title": "Design Implication",
        "takeaway": (
            "Early massing should prioritize controllable solar gain, shaded transition areas, and protected outdoor thresholds."
        ),
    },
    "access-mobility": {
        "summary_title": "Access Read",
        "summary": (
            "Approach routes appear feasible for a primary arrival sequence and basic service access, though exact traffic behavior remains unverified."
        ),
        "takeaway_title": "Planning Note",
        "takeaway": (
            "Separate ceremonial arrival, daily access, and service movement from the outset to reduce future conflicts."
        ),
    },
    "context-surroundings": {
        "summary_title": "Context Snapshot",
        "summary": (
            "The surrounding fabric should be treated as a mixed contextual field with opportunities for view capture, buffering, and controlled frontage."
        ),
        "takeaway_title": "Massing Prompt",
        "takeaway": (
            "A simple placeholder volume has been attached to support quick 3D context testing while proper surrounding data is still absent."
        ),
    },
    "vegetation-ecology": {
        "summary_title": "Ecology Read",
        "summary": (
            "Assume existing vegetation and ecological value are partially unknown. "
            "Early concepts should therefore preserve flexibility around landscape retention and stormwater strategy."
        ),
        "takeaway_title": "Risk Note",
        "takeaway": (
            "Keep a soft perimeter strategy and avoid overcommitting hardscape until baseline ecological data is collected."
        ),
    },
    "site-opportunities-risks": {
        "summary_title": "Opportunity / Risk Scan",
        "summary": (
            "The site presents a workable concept-stage balance: enough spatial freedom for design moves, but still enough uncertainty to justify staged validation."
        ),
        "takeaway_title": "Next Step",
        "takeaway": (
            "Treat all current site findings as directional guidance and update them once survey, mobility, and environmental inputs mature."
        ),
    },
}


def _find_or_create_area(db, project_id: str, area_slug: str) -> str:
    workspace_ref = db.collection("projects").document(project_id).collection("workspace")
    area_docs = workspace_ref.where(filter=FieldFilter("slug", "==", area_slug)).limit(1).get()
    print(f"[workspace] area query slug={area_slug!r} -> {len(area_docs)} result(s)")

    if area_docs:
        area_id = area_docs[0].id
        print(f"[workspace] found area id={area_id!r}")
        return area_id

    print(f"[workspace] area slug={area_slug!r} not found, creating it")
    new_ref = workspace_ref.document()
    new_ref.set({
        "slug": area_slug,
        "name": area_slug.replace("-", " ").title(),
        "description": "",
        "type": "Layers",
        "isLocked": True,
        "createdBy": None,
        "createdAt": int(time.time() * 1000),
    })
    print(f"[workspace] created area id={new_ref.id!r}")
    return new_ref.id


def _find_or_create_subdomain(db, project_id: str, area_id: str, subdomain_slug: str) -> str:
    subdomains_ref = (
        db.collection("projects")
        .document(project_id)
        .collection("workspace")
        .document(area_id)
        .collection("subdomains")
    )
    sub_docs = subdomains_ref.where(filter=FieldFilter("slug", "==", subdomain_slug)).limit(1).get()
    print(f"[workspace] subdomain query slug={subdomain_slug!r} under area={area_id!r} -> {len(sub_docs)} result(s)")

    if sub_docs:
        subdomain_id = sub_docs[0].id
        print(f"[workspace] found subdomain id={subdomain_id!r}")
        return subdomain_id

    print(f"[workspace] subdomain slug={subdomain_slug!r} not found, creating it")
    new_ref = subdomains_ref.document()
    new_ref.set({
        "slug": subdomain_slug,
        "name": subdomain_slug.replace("-", " ").title(),
        "description": "",
        "type": "subdomain",
        "isLocked": True,
        "createdBy": None,
        "createdAt": int(time.time() * 1000),
    })
    print(f"[workspace] created subdomain id={new_ref.id!r}")
    return new_ref.id


def write_subdomain_content(
    project_id: str,
    area_slug: str,
    subdomain_slug: str,
    content: str,
) -> dict:
    print(f"[workspace] write_subdomain_content: project={project_id!r} area={area_slug!r} subdomain={subdomain_slug!r}")

    if not project_id:
        print("[workspace] ERROR: no project_id")
        return {"error": "No project_id provided."}

    try:
        db = get_firestore_client()
        area_id = _find_or_create_area(db, project_id, area_slug)
        subdomain_id = _find_or_create_subdomain(db, project_id, area_id, subdomain_slug)

        subdomain_ref = (
            db.collection("projects")
            .document(project_id)
            .collection("workspace")
            .document(area_id)
            .collection("subdomains")
            .document(subdomain_id)
        )

        subdomain_ref.set(
            {
                "content": content,
                "updatedAt": int(time.time() * 1000),
            },
            merge=True,
        )

        print(f"[workspace] wrote content at path={subdomain_ref.path!r}")
        return {"ok": True, "path": subdomain_ref.path}

    except Exception as exc:
        print(f"[workspace] ERROR writing content: {exc}")
        return {"error": str(exc)}


def write_subdomain_artifacts(
    project_id: str,
    area_slug: str,
    subdomain_slug: str,
    artifacts: dict,
) -> dict:
    print(f"[workspace] write_subdomain_artifacts: project={project_id!r} area={area_slug!r} subdomain={subdomain_slug!r}")

    if not project_id:
        print("[workspace] ERROR: no project_id")
        return {"error": "No project_id provided."}

    try:
        db = get_firestore_client()
        area_id = _find_or_create_area(db, project_id, area_slug)
        subdomain_id = _find_or_create_subdomain(db, project_id, area_id, subdomain_slug)

        subdomain_ref = (
            db.collection("projects")
            .document(project_id)
            .collection("workspace")
            .document(area_id)
            .collection("subdomains")
            .document(subdomain_id)
        )

        subdomain_ref.set(
            {
                "artifacts": artifacts,
                "content": admin_firestore.DELETE_FIELD,
                "updatedAt": int(time.time() * 1000),
            },
            merge=True,
        )

        print(f"[workspace] wrote artifacts at path={subdomain_ref.path!r}")
        return {"ok": True, "path": subdomain_ref.path}

    except Exception as exc:
        print(f"[workspace] ERROR writing artifacts: {exc}")
        return {"error": str(exc)}


def _serialize_coordinates(coordinates) -> list[dict]:
    if not isinstance(coordinates, list):
        return []

    serialized = []
    for ring in coordinates:
        if not isinstance(ring, list):
            continue
        points = []
        for point in ring:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            points.append({
                "lng": float(point[0]),
                "lat": float(point[1]),
            })
        if points:
            serialized.append({"points": points})
    return serialized


def _serialize_point(point):
    if not isinstance(point, (list, tuple)) or len(point) < 2:
        return None
    return {
        "lng": float(point[0]),
        "lat": float(point[1]),
    }


def _build_text_artifact(label: str, value: str) -> dict:
    return {
        "type": "text",
        "label": label,
        "value": value,
    }


def _build_image_artifact(label: str, url: str, *, alt: str | None = None) -> dict:
    value = {"url": url}
    if alt:
        value["alt"] = alt
    return {
        "type": "image",
        "label": label,
        "value": value,
    }


def _build_model_artifact(label: str, url: str, *, format_name: str = "glb") -> dict:
    return {
        "type": "model",
        "label": label,
        "value": {
            "url": url,
            "format": format_name,
        },
    }


def _build_demo_cube_glb() -> bytes:
    positions = [
        (-0.5, -0.5, -0.5),
        (0.5, -0.5, -0.5),
        (0.5, 0.5, -0.5),
        (-0.5, 0.5, -0.5),
        (-0.5, -0.5, 0.5),
        (0.5, -0.5, 0.5),
        (0.5, 0.5, 0.5),
        (-0.5, 0.5, 0.5),
    ]
    indices = [
        0, 1, 2, 2, 3, 0,
        4, 5, 6, 6, 7, 4,
        0, 4, 7, 7, 3, 0,
        1, 5, 6, 6, 2, 1,
        3, 2, 6, 6, 7, 3,
        0, 1, 5, 5, 4, 0,
    ]

    position_bytes = b"".join(struct.pack("<3f", *point) for point in positions)
    index_bytes = b"".join(struct.pack("<H", index) for index in indices)
    binary_chunk = position_bytes + index_bytes

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "archibot-initial-analysis",
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "AnalysisCube"}],
        "meshes": [{
            "name": "AnalysisCube",
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 1,
                "material": 0,
            }],
        }],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.23, 0.44, 0.91, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.72,
            },
        }],
        "buffers": [{"byteLength": len(binary_chunk)}],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(position_bytes),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes),
                "byteLength": len(index_bytes),
                "target": 34963,
            },
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": len(positions),
                "type": "VEC3",
                "min": [-0.5, -0.5, -0.5],
                "max": [0.5, 0.5, 0.5],
            },
            {
                "bufferView": 1,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR",
                "min": [0],
                "max": [7],
            },
        ],
    }

    json_chunk = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_padding = (4 - (len(json_chunk) % 4)) % 4
    if json_padding:
        json_chunk += b" " * json_padding

    binary_padding = (4 - (len(binary_chunk) % 4)) % 4
    if binary_padding:
        binary_chunk += b"\x00" * binary_padding

    total_length = 12 + 8 + len(json_chunk) + 8 + len(binary_chunk)
    return (
        struct.pack("<III", 0x46546C67, 2, total_length)
        + struct.pack("<I4s", len(json_chunk), b"JSON")
        + json_chunk
        + struct.pack("<I4s", len(binary_chunk), b"BIN\x00")
        + binary_chunk
    )


def _upload_demo_cube_model(project_id: str) -> dict:
    object_path = f"projects/{project_id}/artifacts/site-analysis/demo-context-cube.glb"
    upload = _upload_storage_bytes(
        object_path,
        _build_demo_cube_glb(),
        content_type="model/gltf-binary",
        cache_control="public,max-age=3600",
    )

    return {
        "url": upload["url"],
        "storagePath": object_path,
    }


def _upload_storage_bytes(
    object_path: str,
    payload: bytes,
    *,
    content_type: str,
    cache_control: str = "public,max-age=3600",
) -> dict:
    bucket = get_storage_bucket()
    token = uuid4().hex
    blob = bucket.blob(object_path)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.cache_control = cache_control
    blob.upload_from_string(payload, content_type=content_type)
    blob.patch()

    url = (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/"
        f"{quote(object_path, safe='')}?alt=media&token={token}"
    )
    return {"url": url, "storagePath": object_path}


def _geodesic_circle(lng: float, lat: float, radius_m: float, n_pts: int = 128):
    aeqd = _pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lng} +datum=WGS84 +units=m")
    wgs84 = _pyproj.CRS("EPSG:4326")
    to_wgs84 = _pyproj.Transformer.from_crs(aeqd, wgs84, always_xy=True).transform
    return _shapely_transform(to_wgs84, _Point(0, 0).buffer(radius_m, resolution=n_pts))




def _render_sun_diagram_png(
    site_coordinates,
    site_center,
    analysis_radius,
    *,
    width: int = 1920,
    height: int = 1920,
) -> bytes | None:
    if not _GEO_AVAILABLE:
        raise RuntimeError("geopandas is not available.")

    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import contextily as _cx2

    if not isinstance(site_center, (list, tuple)) or len(site_center) < 2:
        return None

    lng, lat = float(site_center[0]), float(site_center[1])
    dpi = 200

    # ── project parcel into local metres (aeqd centred on site) ─────────────
    aeqd_crs = _pyproj.CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat} +lon_0={lng} +datum=WGS84 +units=m")
    to_aeqd = _pyproj.Transformer.from_crs(
        _pyproj.CRS("EPSG:4326"), aeqd_crs, always_xy=True)

    parcel_polys_m = []
    all_pts_m = []
    if isinstance(site_coordinates, list):
        for ring in site_coordinates:
            if not isinstance(ring, list) or len(ring) < 3:
                continue
            ring_pts = []
            for pt in ring:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    p = to_aeqd.transform(float(pt[0]), float(pt[1]))
                elif isinstance(pt, dict):
                    p = to_aeqd.transform(float(pt.get("lng", 0)), float(pt.get("lat", 0)))
                else:
                    continue
                ring_pts.append(p)
                all_pts_m.append(p)
            if len(ring_pts) >= 3:
                parcel_polys_m.append(ring_pts)

    # compass_r: just outside the parcel bounding box (30% margin on max extent)
    if all_pts_m:
        max_extent = max(math.hypot(x, y) for x, y in all_pts_m)
    else:
        max_extent = 80.0
    compass_r = max(max_extent * 1.30, 50.0)

    label_r = compass_r * 1.12
    view    = label_r * 1.10

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_aspect("equal")
    ax.set_xlim(-view, view)
    ax.set_ylim(-view, view)
    ax.set_axis_off()

    # ── basemap: greyscale tiles clipped to compass circle ───────────────────
    merc_crs = _pyproj.CRS("EPSG:3857")
    to_merc  = _pyproj.Transformer.from_crs(aeqd_crs, merc_crs, always_xy=True)
    circle_merc = [to_merc.transform(
        compass_r * math.sin(math.radians(a)),
        compass_r * math.cos(math.radians(a))) for a in range(0, 360, 5)]
    xs_m = [p[0] for p in circle_merc]
    ys_m = [p[1] for p in circle_merc]

    try:
        fig_t, ax_t = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
        ax_t.set_xlim(min(xs_m), max(xs_m))
        ax_t.set_ylim(min(ys_m), max(ys_m))
        _cx2.add_basemap(ax_t, crs="EPSG:3857",
                         source=_cx2.providers.CartoDB.PositronNoLabels,
                         zoom=17, alpha=1.0)
        ax_t.set_axis_off()
        fig_t.subplots_adjust(left=0, right=1, top=1, bottom=0)
        tile_buf = io.BytesIO()
        fig_t.savefig(tile_buf, format="png", dpi=dpi,
                      bbox_inches="tight", pad_inches=0)
        plt.close(fig_t)
        tile_buf.seek(0)
        import numpy as _np
        from PIL import Image as _PILImg
        tile_img = _PILImg.open(tile_buf).convert("L")
        # threshold: pixels darker than 220 become black, rest white — pure b&w linework
        arr = _np.array(tile_img)
        arr = _np.where(arr < 220, 0, 255).astype(_np.uint8)
        tile_img = _PILImg.fromarray(arr)
        ax.imshow(tile_img,
                  extent=[-compass_r, compass_r, -compass_r, compass_r],
                  origin="upper", aspect="equal", alpha=0.35, cmap="gray",
                  zorder=1, interpolation="lanczos",
                  clip_path=plt.Circle((0, 0), compass_r, transform=ax.transData),
                  clip_on=True)
    except Exception as _bm_exc:
        print(f"[sun_diagram] basemap skipped: {_bm_exc}")

    # ── altitude rings (10°, 20°, … 80°) — thin grey dashes ─────────────────
    for alt_ring in range(10, 90, 10):
        r_ring = compass_r * (1.0 - alt_ring / 90.0)
        ax.add_patch(plt.Circle((0, 0), r_ring,
                                 color="#bbbbbb", fill=False,
                                 linewidth=0.5, linestyle="--", zorder=2))

    # ── compass ring with ticks ───────────────────────────────────────────────
    ax.add_patch(plt.Circle((0, 0), compass_r,
                             color="black", fill=False, linewidth=1.5, zorder=5))

    directions_16 = [
        (0,    "N"),  (22.5, "NNE"), (45,  "NE"),  (67.5, "ENE"),
        (90,   "E"),  (112.5,"ESE"), (135, "SE"),  (157.5,"SSE"),
        (180,  "S"),  (202.5,"SSW"), (225, "SW"),  (247.5,"WSW"),
        (270,  "W"),  (292.5,"WNW"), (315, "NW"),  (337.5,"NNW"),
    ]
    cardinals = {"N", "S", "E", "W"}

    # fine ticks every 2° — monochromatic grey shades
    for a in range(0, 360, 2):
        ar = math.radians(a)
        sx, sy = math.sin(ar), math.cos(ar)
        if a % 45 == 0:
            tl, lw, col = compass_r * 0.07, 1.4, "black"
        elif a % 22 == 0 or a % 23 == 0:   # ~22.5° intercardinals
            tl, lw, col = compass_r * 0.05, 1.0, "#444444"
        elif a % 10 == 0:
            tl, lw, col = compass_r * 0.035, 0.7, "#777777"
        else:
            tl, lw, col = compass_r * 0.018, 0.4, "#aaaaaa"
        ax.plot([sx * (compass_r - tl), sx * compass_r],
                [sy * (compass_r - tl), sy * compass_r],
                color=col, linewidth=lw, zorder=5)

    # direction labels — N/S/E/W only, in black
    for az_deg, name in directions_16:
        if name not in cardinals:
            continue
        ar = math.radians(az_deg)
        sx, sy = math.sin(ar), math.cos(ar)
        ax.text(sx * label_r * 0.94, sy * label_r * 0.94, name,
                fontsize=13, fontweight="bold", color="black",
                ha="center", va="center", zorder=9)

    # ── parcel footprint ──────────────────────────────────────────────────────
    for ring_pts in parcel_polys_m:
        ax.add_patch(plt.Polygon(ring_pts, closed=True,
                                  facecolor="none", edgecolor="black",
                                  linewidth=2.0, zorder=6))
    ax.plot(0, 0, "o", color="black", markersize=4, zorder=6)

    # ── sun arcs (stereographic) ──────────────────────────────────────────────
    seasons = [
        (23.45,  "-",   11),   # summer solstice
        ( 0.0,   "--",   9),   # equinox
        (-23.45, ":",    7),   # winter solstice
    ]
    for dec, ls, n_suns in seasons:
        pts_m = _sun_arc_aeqd_points(lat, dec, compass_r)
        if pts_m is None:
            continue
        xs, ys = zip(*pts_m)
        ax.plot(xs, ys, color="black", linewidth=1.8, linestyle=ls,
                alpha=0.9, zorder=7, solid_capstyle="round")
        if len(xs) >= 2:
            idxs = sorted({int(round(i * (len(xs) - 1) / (n_suns - 1)))
                           for i in range(n_suns)})
            for idx in idxs:
                ax.plot(xs[idx], ys[idx], "o",
                        color="white", markersize=7, zorder=8,
                        markeredgecolor="black", markeredgewidth=1.2)

    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()


def _render_parcel_preview_png(
    site_coordinates,
    site_center,
    analysis_radius,
    *,
    width: int = 1920,
    height: int = 1280,
) -> bytes | None:
    if not _GEO_AVAILABLE:
        raise RuntimeError(
            "geopandas/contextily are not available. Install them in the backend environment to render parcel previews."
        )

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.ticker as mticker

    lng = float(site_center[1] if isinstance(site_center, (list, tuple)) and len(site_center) >= 2 else 0)
    lat = float(site_center[0] if isinstance(site_center, (list, tuple)) and len(site_center) >= 2 else 0)
    # site_center is [lng, lat]
    lng, lat = float(site_center[0]), float(site_center[1])
    try:
        radius_m = float(analysis_radius) if analysis_radius is not None else 0
    except (TypeError, ValueError):
        radius_m = 0

    geoms_wgs84 = []

    circle_gdf = None
    if radius_m > 0:
        circle = _geodesic_circle(lng, lat, radius_m)
        circle_gdf = _gpd.GeoDataFrame(geometry=[circle], crs="EPSG:4326").to_crs("EPSG:3857")
        geoms_wgs84.append(circle)

    parcel_gdf = None
    if isinstance(site_coordinates, list):
        polys = []
        for ring in site_coordinates:
            if not isinstance(ring, list) or len(ring) < 3:
                continue
            coords = []
            for pt in ring:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    coords.append((float(pt[0]), float(pt[1])))
                elif isinstance(pt, dict):
                    coords.append((float(pt.get("lng", 0)), float(pt.get("lat", 0))))
            if len(coords) < 3:
                continue
            poly = _Polygon(coords)
            if poly.is_valid:
                polys.append(poly)
        if polys:
            parcel_gdf = _gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326").to_crs("EPSG:3857")
            geoms_wgs84.extend(polys)

    if not geoms_wgs84 and not isinstance(site_center, (list, tuple)):
        return None

    center_gdf = _gpd.GeoDataFrame(geometry=[_Point(lng, lat)], crs="EPSG:4326").to_crs("EPSG:3857")
    cx_m, cy_m = center_gdf.geometry.iloc[0].x, center_gdf.geometry.iloc[0].y

    if geoms_wgs84:
        bounds_gdf = _gpd.GeoDataFrame(geometry=[_unary_union(geoms_wgs84)], crs="EPSG:4326").to_crs("EPSG:3857")
        minx, miny, maxx, maxy = bounds_gdf.total_bounds
    else:
        pad = max(radius_m * 1.5, 500)
        minx, miny, maxx, maxy = cx_m - pad, cy_m - pad, cx_m + pad, cy_m + pad

    pad_x = (maxx - minx) * 0.25
    pad_y = (maxy - miny) * 0.25
    dpi = 200

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    _cx.add_basemap(ax, crs="EPSG:3857", source=_cx.providers.OpenStreetMap.Mapnik, zoom=17, alpha=1.0)

    if circle_gdf is not None:
        circle_gdf.plot(ax=ax, facecolor="#2563eb18", edgecolor="#1d4ed8cc", linewidth=2, zorder=2)

    if parcel_gdf is not None:
        parcel_gdf.plot(ax=ax, facecolor="#14b8a630", edgecolor="#0f766e", linewidth=2.5, zorder=3)

    ax.plot(cx_m, cy_m, marker="o", color="#1d4ed8", markersize=10, zorder=5)
    ax.plot(cx_m, cy_m, marker="o", color="white", markersize=4, zorder=6)

    to_wgs84 = _pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    def fmt_x(x, _):
        lng_val, _ = to_wgs84.transform(x, 0)
        return f"{lng_val:.4f}°"

    def fmt_y(_, y):
        _, lat_val = to_wgs84.transform(0, y)
        return f"{lat_val:.4f}°"

    ax.xaxis.set_major_locator(mticker.LinearLocator(numticks=6))
    ax.yaxis.set_major_locator(mticker.LinearLocator(numticks=5))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_x))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_y))
    ax.grid(True, color="#00000033", linewidth=0.6, linestyle="--", zorder=4)
    ax.tick_params(labelsize=7, colors="#333333")
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")

    legend_handles = []
    if circle_gdf is not None:
        legend_handles.append(mpatches.Patch(facecolor="#2563eb44", edgecolor="#1d4ed8", label=f"Analysis radius ({int(radius_m)} m)"))
    if parcel_gdf is not None:
        legend_handles.append(mpatches.Patch(facecolor="#14b8a644", edgecolor="#0f766e", label="Parcel"))
    if legend_handles:
        ax.legend(handles=legend_handles, loc="upper right", fontsize=8,
                  facecolor="white", edgecolor="#cccccc", framealpha=0.85)

    plt.tight_layout(pad=0.4)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="PNG", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()


def write_project_brief_artifact(
    project_id: str,
    *,
    name: str,
    description: str,
    project_type: str,
    site_coordinates,
    site_center,
    analysis_radius,
) -> dict:
    artifacts = {
        "project_name": {
            "type": "text",
            "label": "Project Name",
            "value": name or "Untitled project",
        },
        "project_type": {
            "type": "text",
            "label": "Type",
            "value": project_type or "Not provided",
        },
        "project_description": {
            "type": "text",
            "label": "Description",
            "value": description or "Not provided",
        },
    }

    return write_subdomain_artifacts(
        project_id=project_id,
        area_slug="inputs-definition",
        subdomain_slug="project-brief",
        artifacts=artifacts,
    )


def write_site_geolocation_artifact(
    project_id: str,
    *,
    site_coordinates,
    site_center,
    analysis_radius,
) -> dict:
    warnings: list[str] = []
    artifacts = {
        "parcel_definition": {
            "type": "geolocation",
            "label": "Parcel Definition",
            "value": {
                "coordinates": _serialize_coordinates(site_coordinates),
                "center": _serialize_point(site_center),
                "analysisRadiusMeters": float(analysis_radius) if analysis_radius is not None else None,
            },
        },
    }

    try:
        preview_png = _render_parcel_preview_png(
            site_coordinates,
            site_center,
            analysis_radius,
        )
        if preview_png:
            upload = _upload_storage_bytes(
                f"projects/{project_id}/artifacts/site-analysis/geolocation-parcel/parcel-preview.png",
                preview_png,
                content_type="image/png",
                cache_control="public,max-age=3600",
            )
            artifacts["parcel_preview"] = _build_image_artifact(
                "Parcel Preview",
                upload["url"],
                alt="Site parcel preview with analysis radius overlay",
            )
    except Exception as exc:
        warning = f"Parcel preview image generation failed: {exc}"
        warnings.append(warning)
        print(f"[workspace] WARNING {warning}")

    result = write_subdomain_artifacts(
        project_id=project_id,
        area_slug="site-analysis",
        subdomain_slug="geolocation-parcel",
        artifacts=artifacts,
    )
    if warnings:
        result["warnings"] = warnings
    return result


def write_site_analysis_boilerplate(
    project_id: str,
    *,
    name: str,
    description: str,
    project_type: str,
    site_coordinates,
    site_center,
    analysis_radius,
) -> dict:
    radius_text = f"{int(round(float(analysis_radius)))} m" if analysis_radius is not None else "unspecified"
    center_text = (
        f"{float(site_center[1]):.5f}, {float(site_center[0]):.5f}"
        if isinstance(site_center, (list, tuple)) and len(site_center) >= 2
        else "not yet set"
    )
    project_label = name or "this project"
    type_label = project_type or "unspecified type"
    description_label = description or "No detailed project description has been added yet."

    model_upload = None
    sun_path_geojson = None
    warnings: list[str] = []

    try:
        model_upload = _upload_demo_cube_model(project_id)
    except Exception as exc:
        warning = f"3D demo model upload failed: {exc}"
        warnings.append(warning)
        print(f"[workspace] WARNING {warning}")

    try:
        sun_path_geojson = _compute_sun_path_geojson(
            site_coordinates=site_coordinates,
            site_center=site_center,
        )
    except Exception as exc:
        warning = f"Sun path GeoJSON computation failed: {exc}"
        warnings.append(warning)
        print(f"[workspace] WARNING {warning}")

    writes = []
    for subdomain_slug, copy in SITE_ANALYSIS_SUBDOMAIN_COPY.items():
        artifacts = {
            "analysis_summary": _build_text_artifact(
                copy["summary_title"],
                (
                    f"{copy['summary']} "
                    f"Working context: {project_label} is currently tracked as {type_label}, "
                    f"centered around {center_text}, with an active analysis radius of {radius_text}."
                ),
            ),
            "analysis_takeaway": _build_text_artifact(
                copy["takeaway_title"],
                f"{copy['takeaway']} Project note: {description_label}",
            ),
        }

        if subdomain_slug == "context-surroundings" and model_upload:
            artifacts["context_mass_proxy"] = {
                "type": "model",
                "label": "Context Massing Proxy",
                "value": {
                    "url": model_upload["url"],
                    "storagePath": model_upload["storagePath"],
                    "format": "glb",
                },
            }

        if subdomain_slug == "climate-sun-wind" and sun_path_geojson:
            artifacts["sun_path_diagram"] = {
                "type": "geolocation",
                "label": "Sun Path Diagram",
                "value": {
                    "coordinates": None,
                    "center": list(site_center[:2]) if isinstance(site_center, (list, tuple)) and len(site_center) >= 2 else None,
                    "analysisRadiusMeters": None,
                    # GeoJSON stored as JSON string — Firestore rejects deeply
                    # nested arrays in document fields (400 invalid nested entity).
                    "overlaysGeojson": json.dumps(sun_path_geojson, separators=(",", ":")),
                    # Map style overrides applied by the frontend renderer.
                    "mapStyle": {
                        "showLabels": False,
                        "showIcons": False,
                        "backgroundColor": "#ffffff",
                    },
                },
            }

        result = write_subdomain_artifacts(
            project_id=project_id,
            area_slug="site-analysis",
            subdomain_slug=subdomain_slug,
            artifacts=artifacts,
        )
        writes.append({
            "subdomain": subdomain_slug,
            **result,
        })

    return {
        "ok": all(not write.get("error") for write in writes),
        "writes": writes,
        "warnings": warnings,
        "model": model_upload,
    }
