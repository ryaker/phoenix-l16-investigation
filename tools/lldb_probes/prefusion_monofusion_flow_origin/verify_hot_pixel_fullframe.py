#!/usr/bin/env python3
"""Replay the complete default hot-pixel worker from durable runtime captures."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
FORMULA_PATH = Path(__file__).with_name("diagnose_flow_source_hotpixel.py")
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
WIDTH = 4160
HEIGHT = 3120


def load_formula():
    spec = importlib.util.spec_from_file_location("hotpixel_fullframe_formula", FORMULA_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_parity(coordinate: int, extent: int) -> int:
    if coordinate < 0:
        return coordinate & 1
    if coordinate >= extent:
        return extent - 2 + (coordinate & 1)
    return coordinate


def border_value(source: np.ndarray, x: int, y: int) -> int:
    center_x = project_parity(x, WIDTH)
    center_y = project_parity(y, HEIGHT)
    values = sorted(
        int(source[neighbor_y, neighbor_x])
        for neighbor_y in (center_y - 2, center_y, center_y + 2)
        if 0 <= neighbor_y < HEIGHT
        for neighbor_x in (center_x - 2, center_x, center_x + 2)
        if 0 <= neighbor_x < WIDTH
    )
    return values[len(values) // 2]


def verify_views(report: dict, source: np.ndarray) -> int:
    checked = 0
    assert len(report["clipped_views"]) == 4
    for item in report["clipped_views"]:
        x0, y0, _x1, _y1 = item["rectangle"]
        origin_x, origin_y = item["dump"]["logical_origin"]
        extent_x, extent_y = item["dump"]["allocation_extent"]
        view = np.fromfile(item["dump"]["path"], dtype="<u2").reshape(
            extent_y, extent_x
        )
        for local_y in range(origin_y, origin_y + extent_y):
            y = y0 + local_y
            for local_x in range(origin_x, origin_x + extent_x):
                x = x0 + local_x
                actual = int(view[local_y - origin_y, local_x - origin_x])
                expected = (
                    int(source[y, x])
                    if 0 <= y < HEIGHT and 0 <= x < WIDTH
                    else border_value(source, x, y)
                )
                assert actual == expected, (item["rectangle"], x, y, actual, expected)
                checked += 1
    return checked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    assert sha256(LIBCP) == LIBCP_SHA256
    report = json.loads(args.report.read_text(encoding="ascii"))
    assert report["complete"] and not report["errors"]
    source_path = Path(report["helper"]["source_dump"]["path"])
    observed_path = Path(report["helper"]["destination_dump"]["path"])
    source = np.fromfile(source_path, dtype="<u2").reshape(HEIGHT, WIDTH)
    observed = np.fromfile(observed_path, dtype="<u2").reshape(HEIGHT, WIDTH)
    assert sha256(source_path) == report["helper"]["source_dump"]["sha256"]
    assert sha256(observed_path) == report["helper"]["destination_dump"]["sha256"]
    checked_view_samples = verify_views(report, source)

    luts = np.stack(
        [np.fromfile(item["path"], dtype="<f4") for item in report["worker"]["luts"]]
    )
    assert luts.shape == (4, 1024)
    formula = load_formula()
    padded = formula.bayer_median_halo(source)
    results = []
    for phase_xor in (0, 1):
        residual = formula.residual_pass(padded, phase_xor, 2)
        rebuilt, markers = formula.apply_isolated_bayer_halo(
            padded,
            source,
            residual,
            luts,
            phase_xor,
            np.float32(4.0),
            6,
        )
        mismatch = int(np.count_nonzero(rebuilt != observed))
        results.append(
            {
                "phase_xor": phase_xor,
                "mismatch": mismatch,
                "markers": int(np.count_nonzero(markers)),
                "changed": int(np.count_nonzero(rebuilt != source)),
                "sha256": hashlib.sha256(rebuilt.astype("<u2", copy=False)).hexdigest(),
            }
        )
    exact = [item for item in results if item["mismatch"] == 0]
    assert len(exact) == 1, results
    print(
        json.dumps(
            {
                "label": report["label"],
                "pixels_exact": WIDTH * HEIGHT,
                "checked_view_samples": checked_view_samples,
                "selected": exact[0],
                "phase_control": next(item for item in results if item not in exact),
                "source_sha256": report["helper"]["source_dump"]["sha256"],
                "observed_sha256": report["helper"]["destination_dump"]["sha256"],
                "lut_sha256": [item["sha256"] for item in report["worker"]["luts"]],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
