"""
Geospatial calibration utilities for estimating a lon/lat → pixel mapping
by aligning coastline coordinates to edges extracted from a raster map.

This module intentionally avoids heavyweight geospatial deps. It uses
NumPy, Pillow and a small amount of linear algebra to estimate a 2D
affine transform via an ICP-like least squares fit.

Primary entry point:
    - calibrate_affine_from_coastline(...)

Outputs a CalibrationResult with helpers to project in both directions
and inferred geographic bounds (west, south, east, north).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np
import requests
from PIL import Image, ImageFilter

# -------------------------- Data structures ---------------------------


@dataclass
class CalibrationResult:
    """Result of coastline-to-image calibration.

    Attributes
    - affine: 2x3 matrix mapping [lon, lat, 1] → [x, y]
    - inverse: 2x3 matrix mapping [x, y, 1] → [lon, lat]
    - pixel_bbox: (left, top, right, bottom) area used for fitting
    - bounds_geo: (lon_west, lat_south, lon_east, lat_north) inferred from data
    """

    affine: np.ndarray
    inverse: np.ndarray
    pixel_bbox: Tuple[int, int, int, int]
    bounds_geo: Tuple[float, float, float, float]

    def lonlat_to_xy(self, lon: float, lat: float) -> Tuple[float, float]:
        v = np.array([lon, lat, 1.0], dtype=float)
        out = self.affine @ v
        return float(out[0]), float(out[1])

    def xy_to_lonlat(self, x: float, y: float) -> Tuple[float, float]:
        v = np.array([x, y, 1.0], dtype=float)
        out = self.inverse @ v
        return float(out[0]), float(out[1])


# -------------------------- Core algorithms ---------------------------


def _sobel_edge_points(
    img: Image.Image, threshold: Optional[float] = None, max_points: int = 5000
) -> np.ndarray:
    """Return edge pixels (x,y) using Sobel magnitude thresholding.

    - Converts to grayscale, applies slight blur to denoise, then Sobel filters.
    - If threshold is None, choose the 85th percentile of gradient magnitudes.
    - Downsamples uniformly to at most max_points points for efficiency.
    """

    gray = img.convert("L").filter(ImageFilter.GaussianBlur(radius=0.8))
    a = np.asarray(gray, dtype=np.float32) / 255.0

    # Sobel kernels
    kx = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]], dtype=np.float32)
    ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)

    def conv2d(src: np.ndarray, k: np.ndarray) -> np.ndarray:
        pad = 1
        p = np.pad(src, ((pad, pad), (pad, pad)), mode="edge")
        out = (
            k[0, 0] * p[0:-2, 0:-2]
            + k[0, 1] * p[0:-2, 1:-1]
            + k[0, 2] * p[0:-2, 2:]
            + k[1, 0] * p[1:-1, 0:-2]
            + k[1, 1] * p[1:-1, 1:-1]
            + k[1, 2] * p[1:-1, 2:]
            + k[2, 0] * p[2:, 0:-2]
            + k[2, 1] * p[2:, 1:-1]
            + k[2, 2] * p[2:, 2:]
        )
        return out

    gx = conv2d(a, kx)
    gy = conv2d(a, ky)
    mag = np.hypot(gx, gy)

    if threshold is None:
        threshold = float(np.percentile(mag, 85.0))

    ys, xs = np.nonzero(mag >= threshold)
    if xs.size == 0:
        return np.zeros((0, 2), dtype=np.float32)

    pts = np.stack([xs.astype(np.float32), ys.astype(np.float32)], axis=1)
    if pts.shape[0] > max_points:
        idx = np.linspace(0, pts.shape[0] - 1, num=max_points, dtype=int)
        pts = pts[idx]
    return pts


def _affine_from_correspondences(src_xy: np.ndarray, dst_xy: np.ndarray) -> np.ndarray:
    """Compute 2x3 affine matrix that maps src → dst via least squares.

    src_xy, dst_xy: shape (N, 2)
    Returns matrix A such that [x', y']^T = A @ [x, y, 1]^T
    """
    n = src_xy.shape[0]
    if dst_xy.shape[0] != n or n < 3:
        raise ValueError("Need at least 3 correspondence pairs with equal lengths")

    X = np.zeros((2 * n, 6), dtype=np.float64)
    y = np.zeros((2 * n,), dtype=np.float64)
    X[0::2, 0:3] = np.c_[src_xy, np.ones(n)]
    X[1::2, 3:6] = np.c_[src_xy, np.ones(n)]
    y[0::2] = dst_xy[:, 0]
    y[1::2] = dst_xy[:, 1]

    params, *_ = np.linalg.lstsq(X, y, rcond=None)
    A = np.vstack([params.reshape(2, 3)])
    return A


def _build_inverse_affine(A: np.ndarray) -> np.ndarray:
    """Return inverse 2x3 matrix for a given 2x3 affine."""
    M = np.vstack([A, np.array([0.0, 0.0, 1.0])])
    Minv = np.linalg.inv(M)
    return Minv[0:2, :]


def _nearest_neighbour(src_xy: np.ndarray, dst_xy: np.ndarray) -> np.ndarray:
    """Return indices j for each i in src such that dst[j] is nearest to src[i]."""
    # Naive O(N*M) is fine for a few thousand points
    d2 = (src_xy[:, None, 0] - dst_xy[None, :, 0]) ** 2 + (
        src_xy[:, None, 1] - dst_xy[None, :, 1]
    ) ** 2
    return np.argmin(d2, axis=1)


def _icp_affine(
    src_xy: np.ndarray,
    dst_xy: np.ndarray,
    init_affine: np.ndarray,
    max_iter: int = 50,
    tol: float = 1e-5,
) -> np.ndarray:
    """Iterative Closest Point (affine) to align src → dst.

    Returns the affine matrix mapping src to dst.
    """
    A = init_affine.copy()
    prev_err = float("inf")
    ones = np.ones((src_xy.shape[0], 1), dtype=np.float64)

    for _ in range(max_iter):
        src_h = np.hstack([src_xy, ones])
        src_to_dst = (A @ src_h.T).T
        idx = _nearest_neighbour(src_to_dst, dst_xy)
        A_delta = _affine_from_correspondences(src_xy, dst_xy[idx])
        A = A_delta

        # Compute mean squared error
        src_to_dst = (A @ src_h.T).T
        err = float(np.mean(np.sum((src_to_dst - dst_xy[idx]) ** 2, axis=1)))
        if abs(prev_err - err) < tol:
            break
        prev_err = err
    return A


# -------------------------- Public API ---------------------------


def calibrate_affine_from_coastline(
    image_path: str,
    coastline_lonlat: Sequence[Tuple[float, float]],
    pixel_bbox: Optional[Tuple[int, int, int, int]] = None,
    initial_geo_bounds: Tuple[float, float, float, float] = (-11.0, 49.0, 2.5, 61.5),
    edge_max_points: int = 5000,
) -> CalibrationResult:
    """Estimate lon/lat → pixel affine transform by aligning coastline.

    Parameters
    - image_path: raster silhouette of UK/IE with minimal rotation.
    - coastline_lonlat: iterable of (lon, lat) coastline points in WGS84.
    - pixel_bbox: optional (left, top, right, bottom) sub-rectangle used for fitting.
    - initial_geo_bounds: rough bounds used to seed the ICP with a simple
      equirectangular mapping.
    - edge_max_points: cap for extracted edge points.

    Returns CalibrationResult containing the affine transform and inferred bounds.
    """
    with Image.open(image_path) as im:
        w, h = im.size
        if pixel_bbox is None:
            pixel_bbox = (0, 0, w, h)
        left, top, right, bottom = pixel_bbox
        im_cropped = im.crop((left, top, right, bottom))

    edge_xy = _sobel_edge_points(im_cropped, max_points=edge_max_points)
    if edge_xy.shape[0] == 0:
        raise ValueError("No edges detected; verify the image and pixel_bbox.")

    # Shift to absolute pixel coordinates
    edge_xy[:, 0] += left
    edge_xy[:, 1] += top

    # Prepare coastline points
    coast = np.asarray(coastline_lonlat, dtype=np.float64)
    if coast.ndim != 2 or coast.shape[1] != 2:
        raise ValueError("coastline_lonlat must be Nx2 of (lon, lat)")

    # Seed with a plate-carrée mapping using rough bounds
    lon_w, lat_s, lon_e, lat_n = initial_geo_bounds
    sx = (right - left) / (lon_e - lon_w)
    sy = (bottom - top) / (lat_s - lat_n)  # note lat decreasing downward
    tx = left - sx * lon_w
    ty = top - sy * lat_n
    A0 = np.array([[sx, 0.0, tx], [0.0, sy, ty]], dtype=np.float64)

    # Run ICP to refine
    A = _icp_affine(coast, edge_xy, A0, max_iter=60, tol=1e-6)
    Ainv = _build_inverse_affine(A)

    # Inferred bounds from coastline extent
    # Compute mapped coastline extent (reserved for potential diagnostics)
    _ = (A @ np.c_[coast, np.ones(coast.shape[0])].T).T

    # Convert pixel bbox corners back to lon/lat for geo bounds
    lonlat_lt = _build_inverse_affine(A) @ np.array([left, top, 1.0])
    lonlat_rb = _build_inverse_affine(A) @ np.array([right, bottom, 1.0])
    lon_w_est = float(min(lonlat_lt[0], lonlat_rb[0]))
    lon_e_est = float(max(lonlat_lt[0], lonlat_rb[0]))
    lat_n_est = float(max(lonlat_lt[1], lonlat_rb[1]))
    lat_s_est = float(min(lonlat_lt[1], lonlat_rb[1]))

    return CalibrationResult(
        affine=A,
        inverse=Ainv,
        pixel_bbox=(left, top, right, bottom),
        bounds_geo=(lon_w_est, lat_s_est, lon_e_est, lat_n_est),
    )


# -------------------------- Data helpers ---------------------------


def download_natural_earth_coastline(
    resolution: str = "10m", max_points: int | None = None
) -> List[Tuple[float, float]]:
    """Download Natural Earth coastline and return UK/IE shoreline points.

    - resolution: one of {"10m", "50m", "110m"}
    - max_points: optional cap; if None, keep all points
    """

    if resolution not in {"10m", "50m", "110m"}:
        raise ValueError("resolution must be one of {'10m','50m','110m'}")
    url = (
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
        f"geojson/ne_{resolution}_coastline.geojson"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    coords: List[Tuple[float, float]] = []
    for feat in data.get("features", []):
        geom = feat.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        line: List[List[float]] = geom.get("coordinates", [])
        for lon, lat in line:
            if -14.5 <= lon <= 5.5 and 48.5 <= lat <= 62.5:
                coords.append((float(lon), float(lat)))

    if not coords:
        raise RuntimeError("No coastline points found in the UK bounding window.")

    pts = np.asarray(coords, dtype=np.float32)
    if max_points is not None and pts.shape[0] > max_points:
        idx = np.linspace(0, pts.shape[0] - 1, num=max_points, dtype=int)
        pts = pts[idx]
    return [(float(x), float(y)) for x, y in pts]


def download_natural_earth_110m_uk_coastline(
    max_points: int = 4000,
) -> List[Tuple[float, float]]:
    """Backwards-compatible wrapper returning 110m data."""
    return download_natural_earth_coastline("110m", max_points=max_points)


__all__ = [
    "CalibrationResult",
    "calibrate_affine_from_coastline",
    "download_natural_earth_coastline",
    "download_natural_earth_110m_uk_coastline",
]
