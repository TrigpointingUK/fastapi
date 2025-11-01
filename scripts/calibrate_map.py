#!/usr/bin/env python3
"""
CLI to calibrate a UK coastline image and output an affine mapping + bounds.

Usage:
    python scripts/calibrate_map.py --image path/to/uk_map.png \
        --out res/uk_map_calibration.json

The tool downloads a lightweight Natural Earth coastline to align against.
If you want to provide your own coastline points (lon,lat CSV), pass
--coastline path/to/file.csv with two columns lon,lat.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure repository root is on sys.path when running this file directly
REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Import after sys.path manipulation
from api.utils.geocalibrate import (  # noqa: E402
    calibrate_affine_from_coastline,
    download_natural_earth_110m_uk_coastline,
)


def read_csv_lonlat(path: str) -> List[Tuple[float, float]]:
    pts: List[Tuple[float, float]] = []
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            try:
                lon = float(row[0])
                lat = float(row[1])
            except ValueError:
                continue
            pts.append((lon, lat))
    if not pts:
        raise ValueError("No valid lon,lat rows found in CSV")
    return pts


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate UK map image")
    parser.add_argument("--image", required=True, help="Path to the map image")
    parser.add_argument(
        "--out", required=True, help="Path to write JSON with affine and bounds"
    )
    parser.add_argument(
        "--pixel-bbox",
        type=int,
        nargs=4,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Optional pixel rectangle containing the drawn coastline",
    )
    parser.add_argument(
        "--coastline",
        help="Optional CSV of lon,lat points; if omitted, download Natural Earth",
    )
    args = parser.parse_args()

    if args.coastline:
        coastline = read_csv_lonlat(args.coastline)
    else:
        coastline = download_natural_earth_110m_uk_coastline()

    result = calibrate_affine_from_coastline(
        image_path=args.image,
        coastline_lonlat=coastline,
        pixel_bbox=tuple(args.pixel_bbox) if args.pixel_bbox else None,
    )

    payload = {
        "affine": result.affine.tolist(),
        "inverse": result.inverse.tolist(),
        "pixel_bbox": list(result.pixel_bbox),
        "bounds_geo": list(result.bounds_geo),
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote calibration to {args.out}")


if __name__ == "__main__":
    main()
