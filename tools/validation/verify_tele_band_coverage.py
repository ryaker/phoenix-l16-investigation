#!/usr/bin/env python3
"""Bind a Lumen index-5 depth map to one Phoenix local range-band dump.

The Phoenix dump stores uint16 pairs ``(lower, lower + count)``.  The second
word is therefore an exclusive upper bound.  The report also includes the
legacy closed-bound reading because the historical 53.1% note did not retain
the original comparison script, and silently changing ``>=`` to ``>`` would
create another interpretation error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np


DIM_RE = re.compile(r"_(\d+)x(\d+)\.")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dimensions(path: Path, width: int | None, height: int | None) -> tuple[int, int]:
    if width is not None and height is not None:
        return width, height
    match = DIM_RE.search(path.name)
    if not match:
        raise ValueError("band filename has no _WIDTHxHEIGHT suffix; pass --width and --height")
    return int(match.group(1)), int(match.group(2))


def depth_to_index(depth: np.ndarray, lookup: np.ndarray) -> tuple[np.ndarray, float]:
    if lookup.size < 2 or not np.all(np.diff(lookup.astype(np.float64)) < 0):
        raise ValueError("lookup must be a strictly descending float32 depth ladder")
    near_inv = 1.0 / float(lookup[-1])
    far_inv = 1.0 / float(lookup[0])
    raw = (1.0 / depth - far_inv) * (lookup.size - 1) / (near_inv - far_inv)
    rounded = np.rint(raw)
    return rounded.astype(np.int32), float(np.max(np.abs(raw - rounded)))


def percentages(*masks: np.ndarray) -> list[float]:
    return [float(mask.mean() * 100.0) for mask in masks]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=Path, required=True, help="Lumen index5_depth.f32le")
    ap.add_argument("--lookup", type=Path, required=True, help="captured descending lookup.f32le")
    ap.add_argument("--band", type=Path, required=True, help="Phoenix (lower,lower+count) uint16 dump")
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    width, height = dimensions(args.band, args.width, args.height)
    lookup = np.fromfile(args.lookup, dtype="<f4")
    depth = np.fromfile(args.depth, dtype="<f4")
    if depth.size != width * height:
        raise ValueError(f"depth has {depth.size} cells; expected {width}x{height}")
    depth = depth.reshape(height, width).astype(np.float64)
    truth, round_error = depth_to_index(depth, lookup)
    if round_error > 0.05:
        raise ValueError(f"depth is not on the supplied ladder; max index residual {round_error:.6g}")

    pairs = np.fromfile(args.band, dtype="<u2")
    if pairs.size != width * height * 2:
        raise ValueError(f"band has {pairs.size} words; expected {width * height * 2}")
    pairs = pairs.reshape(height, width, 2).astype(np.int32)
    lower, upper_exclusive = pairs[..., 0], pairs[..., 1]
    if np.any(upper_exclusive < lower):
        raise ValueError("band contains upper < lower")

    half_open = percentages(
        (truth >= lower) & (truth < upper_exclusive),
        truth >= upper_exclusive,
        truth < lower,
    )
    legacy_closed = percentages(
        (truth >= lower) & (truth <= upper_exclusive),
        truth > upper_exclusive,
        truth < lower,
    )

    bins = []
    for lo in range(0, int(truth.max()) + 1, 5):
        hi = min(lo + 5, int(truth.max()) + 1)
        mask = (truth >= lo) & (truth < hi)
        if mask.any():
            bins.append({
                "truth_interval": [lo, hi],
                "cells": int(mask.sum()),
                "above_exclusive_pct": float((truth[mask] >= upper_exclusive[mask]).mean() * 100.0),
                "above_legacy_strict_pct": float((truth[mask] > upper_exclusive[mask]).mean() * 100.0),
                "mean_upper_exclusive": float(upper_exclusive[mask].mean()),
            })

    report = {
        "inputs": {
            "depth": {"path": str(args.depth), "sha256": sha256(args.depth)},
            "lookup": {"path": str(args.lookup), "sha256": sha256(args.lookup)},
            "band": {"path": str(args.band), "sha256": sha256(args.band)},
        },
        "dimensions": [width, height],
        "lookup_count": int(lookup.size),
        "truth": {
            "min_index": int(truth.min()),
            "max_index": int(truth.max()),
            "distinct_indices": int(np.unique(truth).size),
            "max_rounding_residual": round_error,
        },
        "band": {
            "lower_percentiles": np.percentile(lower, [0, 5, 50, 95, 100]).tolist(),
            "upper_exclusive_percentiles": np.percentile(
                upper_exclusive, [0, 5, 50, 95, 100]
            ).tolist(),
        },
        "coverage": {
            "half_open_lower_le_truth_lt_upper": {
                "inside_pct": half_open[0],
                "above_or_equal_upper_pct": half_open[1],
                "below_lower_pct": half_open[2],
            },
            "legacy_closed_lower_le_truth_le_upper": {
                "inside_pct": legacy_closed[0],
                "strictly_above_upper_pct": legacy_closed[1],
                "below_lower_pct": legacy_closed[2],
            },
        },
        "truth_bins": bins,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
