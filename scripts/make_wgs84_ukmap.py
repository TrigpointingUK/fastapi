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
from typing import List, Sequence, Tuple

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


def filter_uk_lines(
    geojson: dict, lon_w: float, lat_s: float, lon_e: float, lat_n: float
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
    return lines


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
) -> Tuple[np.ndarray, np.ndarray, int, int]:
    px_per_deg = width / (lon_e - lon_w)
    height = int(round(px_per_deg * (lat_n - lat_s)))
    sx = px_per_deg
    sy = -px_per_deg  # y increases downwards
    tx = -sx * lon_w
    # Set translation so that y=0 at lat_n (top edge)
    ty = -sy * lat_n
    A = np.array([[sx, 0.0, tx], [0.0, sy, ty]], dtype=float)
    Minv = np.linalg.inv(np.vstack([A, [0, 0, 1]]))[:2]
    return A, Minv, width, height


def render(
    lines: List[List[Tuple[float, float]]], A: np.ndarray, w: int, h: int
) -> Image.Image:
    im = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)

    def project(p: Tuple[float, float]) -> Tuple[int, int]:
        lon, lat = p
        x = A[0, 0] * lon + A[0, 1] * lat + A[0, 2]
        y = A[1, 0] * lon + A[1, 1] * lat + A[1, 2]
        return int(round(x)), int(round(y))

    for seg in lines:
        if len(seg) < 2:
            continue
        pts = [project(p) for p in seg]
        draw.line(pts, fill=(0, 0, 0), width=2)
    return im


def main() -> None:
    p = argparse.ArgumentParser(
        description="Render WGS84 UK coastline PNG + calibration"
    )
    p.add_argument("--width", type=int, default=1000)
    p.add_argument("--densify", type=int, default=10, help="Polyline densify factor")
    p.add_argument("--lon-west", type=float, default=-14.0)
    p.add_argument("--lon-east", type=float, default=4.5)
    p.add_argument("--lat-south", type=float, default=49.0)
    p.add_argument("--lat-north", type=float, default=61.9)
    p.add_argument("--out-image", default="res/ukmap_wgs84.png")
    p.add_argument("--out-calib", default="res/uk_map_calibration_wgs84.json")
    p.add_argument(
        "--resolution",
        default="10m",
        choices=["10m", "50m", "110m"],
        help="Natural Earth coastline resolution",
    )
    args = p.parse_args()

    gj = download_coastlines(args.resolution)
    lines = filter_uk_lines(
        gj, args.lon_west, args.lat_south, args.lon_east, args.lat_north
    )
    if args.densify and args.densify > 1:
        lines = [densify_polyline(seg, args.densify) for seg in lines]
    A, Ainv, w, h = make_affine(
        args.width, args.lon_west, args.lat_south, args.lon_east, args.lat_north
    )
    im = render(lines, A, w, h)

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
