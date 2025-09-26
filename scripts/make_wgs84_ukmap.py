#!/usr/bin/env python3
"""
Render a plain WGS84 coastline PNG of the UK and emit matching calibration JSON.

Defaults:
  - width: 1000 px
  - bounds: lon [-14.0, 4.5], lat [49.0, 61.9] (includes Shetland)
  - output image: res/ukmap_wgs84.png
  - output calibration: res/uk_map_calibration_wgs84.json

Projection: Plate Carrée (equirectangular), linear lon→x and lat→y mapping.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np
import requests
from PIL import Image, ImageDraw


def download_coastlines(resolution: str = "10m") -> dict:
    assert resolution in {"10m", "50m", "110m"}
    url = (
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
        f"geojson/ne_{resolution}_coastline.geojson"
    )
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def download_countries(resolution: str = "10m") -> dict:
    assert resolution in {"10m", "50m", "110m"}
    url = (
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
        f"geojson/ne_{resolution}_admin_0_countries.geojson"
    )
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def _point_in_ring(point: Tuple[float, float], ring: Sequence[Sequence[float]]) -> bool:
    x, y = point
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        # Ray cast in x-direction
        if (y1 > y) != (y2 > y):
            xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-15) + x1
            if x < xinters:
                inside = not inside
    return inside


def _extract_country_polygons(
    countries_gj: dict, iso3_set: Iterable[str]
) -> List[List[List[Tuple[float, float]]]]:
    polys: List[List[List[Tuple[float, float]]]] = []
    for feat in countries_gj.get("features", []):
        props = feat.get("properties", {})
        iso3 = (props.get("ADM0_A3") or props.get("ISO_A3") or "").upper()
        if iso3 not in {s.upper() for s in iso3_set}:
            continue
        geom = feat.get("geometry", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        if gtype == "Polygon":
            rings = []
            for ring in coords:
                rings.append([(float(x), float(y)) for x, y in ring])
            polys.append(rings)
        elif gtype == "MultiPolygon":
            for poly in coords:
                rings = []
                for ring in poly:
                    rings.append([(float(x), float(y)) for x, y in ring])
                polys.append(rings)
    return polys


def _point_in_polygons(
    pt: Tuple[float, float], polys: List[List[List[Tuple[float, float]]]]
) -> bool:
    # Only test against outer rings (first ring); holes ignored for speed
    for rings in polys:
        if not rings:
            continue
        if _point_in_ring(pt, rings[0]):
            return True
    return False


def filter_uk_lines(
    geojson: dict,
    lon_w: float,
    lat_s: float,
    lon_e: float,
    lat_n: float,
    country_polys: List[List[List[Tuple[float, float]]]] | None = None,
) -> List[List[Tuple[float, float]]]:
    lines: List[List[Tuple[float, float]]] = []
    for feat in geojson.get("features", []):
        geom = feat.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        coords: Sequence[Sequence[float]] = geom.get("coordinates", [])
        seg: List[Tuple[float, float]] = []
        for lon, lat in coords:
            if lon_w <= lon <= lon_e and lat_s <= lat <= lat_n:
                seg.append((float(lon), float(lat)))
            else:
                if len(seg) >= 2:
                    lines.append(seg)
                seg = []
        if len(seg) >= 2:
            lines.append(seg)
    if not lines:
        raise RuntimeError("No coastline segments found in bounds.")
    if country_polys is None:
        return lines
    # Keep segments where at least half the vertices lie within GBR or IRL
    kept: List[List[Tuple[float, float]]] = []
    for seg in lines:
        inside = sum(1 for p in seg if _point_in_polygons(p, country_polys))
        if inside >= max(1, int(0.5 * len(seg))):
            kept.append(seg)
    return kept


def densify_polyline(
    points: List[Tuple[float, float]], factor: int
) -> List[Tuple[float, float]]:
    """Insert evenly spaced points between each pair; factor=1 returns original.

    Factor n yields approximately n× points by adding (n-1) evenly spaced points
    between every consecutive pair.
    """
    if factor <= 1 or len(points) < 2:
        return points
    out: List[Tuple[float, float]] = [points[0]]
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        for k in range(1, factor):
            t = k / float(factor)
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        out.append((x1, y1))
    return out


def make_affine(
    width: int,
    lon_w: float,
    lat_s: float,
    lon_e: float,
    lat_n: float,
    lat_scale: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray, int, int]:
    px_per_deg = width / (lon_e - lon_w)
    height = int(round(px_per_deg * (lat_n - lat_s) * lat_scale))
    sx = px_per_deg
    sy = -px_per_deg * lat_scale  # y increases downwards
    tx = -sx * lon_w
    # Set translation so that y=0 at lat_n (top edge)
    ty = -sy * lat_n
    A = np.array([[sx, 0.0, tx], [0.0, sy, ty]], dtype=float)
    Minv = np.linalg.inv(np.vstack([A, [0, 0, 1]]))[:2]
    return A, Minv, width, height


def render(
    lines: List[List[Tuple[float, float]]],
    country_polys: List[List[List[Tuple[float, float]]]],
    A: np.ndarray,
    w: int,
    h: int,
) -> Image.Image:
    # Transparent background RGBA
    base = Image.new("RGBA", (w, h), color=(0, 0, 0, 0))

    # Build land mask from country polygons (GBR + IRL)
    mask = Image.new("L", (w, h), color=0)
    mdraw = ImageDraw.Draw(mask)

    def project(p: Tuple[float, float]) -> Tuple[int, int]:
        lon, lat = p
        x = A[0, 0] * lon + A[0, 1] * lat + A[0, 2]
        y = A[1, 0] * lon + A[1, 1] * lat + A[1, 2]
        return int(round(x)), int(round(y))

    for rings in country_polys:
        if not rings:
            continue
        # Outer ring filled
        outer = [project(p) for p in rings[0]]
        mdraw.polygon(outer, fill=255)
        # Holes (inner rings) carved out
        for hole in rings[1:]:
            hole_pts = [project(p) for p in hole]
            mdraw.polygon(hole_pts, fill=0)

    # Composite 10% grey land onto transparent sea
    land = Image.new("RGBA", (w, h), color=(26, 26, 26, 255))
    base.paste(land, (0, 0), mask)

    # Optional coastline strokes for crisp edges
    if lines:
        draw = ImageDraw.Draw(base)
        for seg in lines:
            if len(seg) < 2:
                continue
            pts = [project(p) for p in seg]
            draw.line(pts, fill=(40, 40, 40, 255), width=1)

    return base


def main() -> None:
    p = argparse.ArgumentParser(
        description="Render WGS84 UK coastline PNG + calibration"
    )
    p.add_argument("--width", type=int, default=1000)
    p.add_argument("--densify", type=int, default=10, help="Polyline densify factor")
    p.add_argument("--lon-west", type=float, default=-14.0)
    p.add_argument("--lon-east", type=float, default=4.5)
    p.add_argument("--lat-south", type=float, default=49.8)
    p.add_argument("--lat-north", type=float, default=60.9)
    p.add_argument("--out-image", default="res/ukmap_wgs84.png")
    p.add_argument("--out-calib", default="res/uk_map_calibration_wgs84.json")
    p.add_argument(
        "--resolution",
        default="10m",
        choices=["10m", "50m", "110m"],
        help="Natural Earth coastline resolution",
    )
    p.add_argument(
        "--lat-scale",
        type=float,
        default=1.0,
        help="Multiply vertical scale (e.g., cos(53°)=0.6018 to compress; 1/0.6018 to stretch)",
    )
    args = p.parse_args()

    gj = download_coastlines(args.resolution)
    countries = download_countries(args.resolution)
    uk_polys = _extract_country_polygons(
        countries, iso3_set=["GBR", "IRL"]
    )  # remove France
    lines = filter_uk_lines(
        gj,
        args.lon_west,
        args.lat_south,
        args.lon_east,
        args.lat_north,
        country_polys=uk_polys,
    )
    if args.densify and args.densify > 1:
        lines = [densify_polyline(seg, args.densify) for seg in lines]
    A, Ainv, w, h = make_affine(
        args.width,
        args.lon_west,
        args.lat_south,
        args.lon_east,
        args.lat_north,
        lat_scale=args.lat_scale,
    )
    im = render(lines, uk_polys, A, w, h)

    # Save image
    Path(args.out_image).parent.mkdir(parents=True, exist_ok=True)
    im.save(args.out_image, format="PNG")

    # Save calibration
    payload = {
        "affine": A.tolist(),
        "inverse": Ainv.tolist(),
        "pixel_bbox": [0, 0, w, h],
        "bounds_geo": [args.lon_west, args.lat_south, args.lon_east, args.lat_north],
    }
    with open(args.out_calib, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {args.out_image} and {args.out_calib}")


if __name__ == "__main__":
    main()
