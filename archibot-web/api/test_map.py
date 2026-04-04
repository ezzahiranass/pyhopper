"""
Parcel preview renderer using geopandas + contextily + matplotlib + shapely.
Run from the api/ directory:  python test_map.py
Writes output.png next to this file.
"""

import io
import os

import contextily as cx
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pyproj
from pyproj import Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import transform as shapely_transform, unary_union

# ---------------------------------------------------------------------------
# Sample site — swap these out with real values to test
# ---------------------------------------------------------------------------
SITE_CENTER = [-7.9888, 31.6295]   # [lng, lat]
ANALYSIS_RADIUS = 300              # metres
SITE_COORDINATES = [[              # list of rings, each ring is [lng, lat] pairs
    [-7.9903, 31.6285],
    [-7.9873, 31.6285],
    [-7.9873, 31.6305],
    [-7.9903, 31.6305],
    [-7.9903, 31.6285],
]]

# Swap to any cx.providers.* you like, e.g.:
#   cx.providers.OpenStreetMap.Mapnik        — full-colour OSM
#   cx.providers.CartoDB.Positron            — light minimal
#   cx.providers.CartoDB.DarkMatter          — dark minimal
#   cx.providers.Stadia.StamenTerrain        — terrain
#   cx.providers.Esri.WorldImagery           — satellite
BASEMAP_PROVIDER = cx.providers.OpenStreetMap.Mapnik


def _geodesic_circle(lng: float, lat: float, radius_m: float, n_pts: int = 128) -> Polygon:
    aeqd = pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lng} +datum=WGS84 +units=m")
    wgs84 = pyproj.CRS("EPSG:4326")
    to_wgs84 = Transformer.from_crs(aeqd, wgs84, always_xy=True).transform
    return shapely_transform(to_wgs84, Point(0, 0).buffer(radius_m, resolution=n_pts))


def _merc_to_wgs84_axes(ax):
    """Return tick formatter functions that convert Web Mercator → lng/lat labels."""
    to_wgs84 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    def fmt_x(x, _):
        lng, _ = to_wgs84.transform(x, 0)
        return f"{lng:.4f}°"

    def fmt_y(_, y):
        _, lat = to_wgs84.transform(0, y)
        return f"{lat:.4f}°"

    return fmt_x, fmt_y


def render_preview_png(
    site_coordinates,
    site_center,
    analysis_radius,
    *,
    width_px: int = 960,
    height_px: int = 640,
    dpi: int = 150,
) -> bytes:
    lng, lat = float(site_center[0]), float(site_center[1])
    radius_m = float(analysis_radius) if analysis_radius else 0

    geoms_wgs84 = []

    circle_gdf = None
    if radius_m > 0:
        circle = _geodesic_circle(lng, lat, radius_m)
        circle_gdf = gpd.GeoDataFrame(geometry=[circle], crs="EPSG:4326").to_crs("EPSG:3857")
        geoms_wgs84.append(circle)

    parcel_gdf = None
    if isinstance(site_coordinates, list):
        polys = []
        for ring in site_coordinates:
            if not isinstance(ring, list) or len(ring) < 3:
                continue
            poly = Polygon(ring)
            if poly.is_valid:
                polys.append(poly)
        if polys:
            parcel_gdf = gpd.GeoDataFrame(geometry=polys, crs="EPSG:4326").to_crs("EPSG:3857")
            geoms_wgs84.extend(polys)

    center_merc = gpd.GeoDataFrame(geometry=[Point(lng, lat)], crs="EPSG:4326").to_crs("EPSG:3857")

    # --- bounds in Web Mercator ---
    if geoms_wgs84:
        bounds_gdf = gpd.GeoDataFrame(geometry=[unary_union(geoms_wgs84)], crs="EPSG:4326").to_crs("EPSG:3857")
        minx, miny, maxx, maxy = bounds_gdf.total_bounds
    else:
        cx_m, cy_m = center_merc.geometry.iloc[0].x, center_merc.geometry.iloc[0].y
        pad = max(radius_m * 1.5, 500)
        minx, miny, maxx, maxy = cx_m - pad, cy_m - pad, cx_m + pad, cy_m + pad

    pad_x = (maxx - minx) * 0.25
    pad_y = (maxy - miny) * 0.25

    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    # --- basemap ---
    cx.add_basemap(ax, crs="EPSG:3857", source=BASEMAP_PROVIDER, zoom=17, alpha=1.0)

    # --- analysis radius circle — lighter so basemap shows through ---
    if circle_gdf is not None:
        circle_gdf.plot(ax=ax, facecolor="#2563eb18", edgecolor="#1d4ed8cc", linewidth=2, zorder=2)

    # --- parcel polygon — lighter fill, crisp edge ---
    if parcel_gdf is not None:
        parcel_gdf.plot(ax=ax, facecolor="#14b8a630", edgecolor="#0f766e", linewidth=2.5, zorder=3)

    # --- center marker ---
    cx_m, cy_m = center_merc.geometry.iloc[0].x, center_merc.geometry.iloc[0].y
    ax.plot(cx_m, cy_m, marker="o", color="#1d4ed8", markersize=10, zorder=5)
    ax.plot(cx_m, cy_m, marker="o", color="white", markersize=4, zorder=6)

    # --- lat/lng grid overlay ---
    fmt_x, fmt_y = _merc_to_wgs84_axes(ax)
    ax.xaxis.set_major_locator(mticker.LinearLocator(numticks=6))
    ax.yaxis.set_major_locator(mticker.LinearLocator(numticks=5))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_x))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_y))
    ax.grid(True, color="#00000033", linewidth=0.6, linestyle="--", zorder=4)
    ax.tick_params(labelsize=7, colors="#333333")
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")

    # --- legend ---
    legend_handles = []
    if circle_gdf is not None:
        legend_handles.append(mpatches.Patch(facecolor="#2563eb44", edgecolor="#1d4ed8", label=f"Analysis radius ({int(radius_m)} m)"))
    if parcel_gdf is not None:
        legend_handles.append(mpatches.Patch(facecolor="#14b8a644", edgecolor="#0f766e", label="Parcel"))
    if legend_handles:
        ax.legend(handles=legend_handles, loc="upper right", fontsize=8,
                  facecolor="white", edgecolor="#cccccc", framealpha=0.85)

    plt.tight_layout(pad=0.4)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def main():
    here = os.path.dirname(__file__)

    print("Rendering parcel preview...")
    png_bytes = render_preview_png(SITE_COORDINATES, SITE_CENTER, ANALYSIS_RADIUS,
                                   width_px=1920, height_px=1280, dpi=200)
    out_path = os.path.join(here, "output.png")
    with open(out_path, "wb") as f:
        f.write(png_bytes)
    print(f"OK — {len(png_bytes):,} bytes written to {out_path}")

    print("Rendering sun diagram...")
    from firebase.workspace import _render_sun_diagram_png
    sun_bytes = _render_sun_diagram_png(SITE_COORDINATES, SITE_CENTER, ANALYSIS_RADIUS)
    if sun_bytes:
        sun_path = os.path.join(here, "output_sun.png")
        with open(sun_path, "wb") as f:
            f.write(sun_bytes)
        print(f"OK — {len(sun_bytes):,} bytes written to {sun_path}")
    else:
        print("ERROR: sun diagram returned None")


if __name__ == "__main__":
    main()
