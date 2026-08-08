#!/usr/bin/env python3
"""Verify complete stage-map artifacts and measure same-route repeat deltas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "runs/reference_stage_maps"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_report(name: str) -> dict:
    report = json.loads((RUN_DIR / name / "report.json").read_text())
    require(not report["errors"], f"{name}: capture errors")
    require(report["process"]["exit_status"] == 0, f"{name}: process exit")
    require(len(report["captures"]) == 4, f"{name}: capture count")
    for item in report["captures"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["logical_bytes"], f"{name}: size {item['name']}")
        require(file_sha256(path) == item["sha256"], f"{name}: SHA {item['name']}")
    return report


def compare(left: Path, right: Path, kind: str, chunk_values: int = 4_000_000) -> dict:
    dtype = np.dtype("<f4") if kind == "f32" else np.dtype("<u2")
    a = np.memmap(left, dtype=dtype, mode="r")
    b = np.memmap(right, dtype=dtype, mode="r")
    require(a.shape == b.shape, f"shape mismatch: {left.name}")
    unequal = 0
    finite_pairs = 0
    sum_square = 0.0
    max_abs = 0.0
    for start in range(0, a.size, chunk_values):
        end = min(a.size, start + chunk_values)
        av = np.asarray(a[start:end])
        bv = np.asarray(b[start:end])
        unequal += int(np.count_nonzero(av != bv))
        if kind == "f32":
            mask = np.isfinite(av) & np.isfinite(bv)
            delta = av[mask].astype(np.float64) - bv[mask].astype(np.float64)
        else:
            mask = np.ones(av.shape, dtype=bool)
            delta = av.astype(np.int64) - bv.astype(np.int64)
        finite_pairs += int(np.count_nonzero(mask))
        if delta.size:
            absolute = np.abs(delta)
            max_abs = max(max_abs, float(np.max(absolute)))
            sum_square += float(np.dot(delta, delta))
    return {
        "count": int(a.size),
        "unequal": unequal,
        "unequal_fraction": unequal / int(a.size),
        "finite_pairs": finite_pairs,
        "max_abs": max_abs,
        "rmse": (sum_square / finite_pairs) ** 0.5 if finite_pairs else None,
    }


def main() -> None:
    reports = {f"unit1_{focal}mm": load_report(f"unit1_{focal}mm") for focal in (28, 35, 70, 150)}
    comparisons = {}
    for focal in (28, 35, 70, 150):
        repeat = load_report(f"unit1_{focal}mm_repeat")
        base_items = {
            item["name"]: item for item in reports[f"unit1_{focal}mm"]["captures"]
        }
        repeat_items = {item["name"]: item for item in repeat["captures"]}
        comparisons[str(focal)] = {}
        for name, base in base_items.items():
            other = repeat_items[name]
            comparisons[str(focal)][name] = compare(
                Path(base["path"]), Path(other["path"]), base["kind"]
            )
    summary = {
        "four_focal_reports": {
            name: {
                item["name"]: {
                    key: item[key]
                    for key in ("sha256", "logical_bytes", "minimum", "maximum", "mean")
                }
                for item in report["captures"]
            }
            for name, report in reports.items()
        },
        "unit1_same_route_repeats": comparisons,
    }
    output = RUN_DIR / "analysis.json"
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("reference_stage_maps=OK", output)
    for focal, maps in comparisons.items():
        for name, result in maps.items():
            print(focal, name, result)


if __name__ == "__main__":
    main()
