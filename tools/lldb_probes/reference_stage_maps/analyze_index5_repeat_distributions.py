#!/usr/bin/env python3
"""Analyze ten complete index-5 map samples per canonical focal tier."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/reference_stage_maps"
FOCALS = (28, 35, 70, 150)
MAPS = ("index5_hypothesis_index", "index5_depth")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sample_dir(focal: int, sample: int) -> Path:
    if sample == 1:
        suffix = ""
    elif sample == 2:
        suffix = "_repeat"
    else:
        suffix = f"_repeat{sample:02d}"
    return RUN_ROOT / f"unit1_{focal}mm{suffix}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_sample(focal: int, sample: int) -> dict[str, dict]:
    directory = sample_dir(focal, sample)
    report = json.loads((directory / "report.json").read_text(encoding="ascii"))
    require(not report["errors"], f"{focal}/{sample}: {report['errors']}")
    captures = {item["name"]: item for item in report["captures"]}
    require(set(MAPS).issubset(captures), f"{focal}/{sample}: missing maps")
    for name in MAPS:
        item = captures[name]
        path = Path(item["path"])
        require(path.stat().st_size == item["logical_bytes"], f"{focal}/{sample}/{name}: size")
        require(file_sha256(path) == item["sha256"], f"{focal}/{sample}/{name}: hash")
    return captures


def compare(left: Path, right: Path, kind: str, chunk_values: int = 4_000_000) -> dict:
    dtype = np.dtype("<f4") if kind == "f32" else np.dtype("<u2")
    a = np.memmap(left, dtype=dtype, mode="r")
    b = np.memmap(right, dtype=dtype, mode="r")
    require(a.shape == b.shape, f"shape mismatch: {left} {right}")
    unequal = 0
    finite_pairs = 0
    sum_square = 0.0
    sum_reference_square = 0.0
    sum_absolute = 0.0
    sum_absolute_scale = 0.0
    max_abs = 0.0
    for start in range(0, a.size, chunk_values):
        end = min(a.size, start + chunk_values)
        av = np.asarray(a[start:end])
        bv = np.asarray(b[start:end])
        unequal += int(np.count_nonzero(av != bv))
        if kind == "f32":
            mask = np.isfinite(av) & np.isfinite(bv)
            av64 = av[mask].astype(np.float64)
            bv64 = bv[mask].astype(np.float64)
        else:
            av64 = av.astype(np.float64)
            bv64 = bv.astype(np.float64)
            mask = np.ones(av.shape, dtype=bool)
        delta = av64 - bv64
        finite_pairs += int(np.count_nonzero(mask))
        if delta.size:
            absolute = np.abs(delta)
            max_abs = max(max_abs, float(np.max(absolute)))
            sum_square += float(np.dot(delta, delta))
            sum_reference_square += float(np.dot(av64, av64) + np.dot(bv64, bv64)) * 0.5
            sum_absolute += float(np.sum(absolute))
            sum_absolute_scale += float(np.sum(np.abs(av64) + np.abs(bv64)))
    return {
        "count": int(a.size),
        "unequal": unequal,
        "unequal_fraction": unequal / int(a.size),
        "finite_pairs": finite_pairs,
        "max_abs": max_abs,
        "rmse": math.sqrt(sum_square / finite_pairs) if finite_pairs else None,
        "normalized_rmse": math.sqrt(sum_square / sum_reference_square) if sum_reference_square else 0.0,
        "symmetric_l1": sum_absolute / sum_absolute_scale if sum_absolute_scale else 0.0,
    }


def percentile(values: list[float], quantile: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), quantile))


def summarize_pairs(pairs: list[dict]) -> dict:
    fields = ("unequal_fraction", "max_abs", "rmse", "normalized_rmse", "symmetric_l1")
    return {
        field: {
            "minimum": min(item[field] for item in pairs),
            "median": percentile([item[field] for item in pairs], 50),
            "p95": percentile([item[field] for item in pairs], 95),
            "maximum": max(item[field] for item in pairs),
        }
        for field in fields
    }


def main() -> None:
    output = {"sample_count_per_focal": 10, "focals": {}}
    for focal in FOCALS:
        samples = {sample: load_sample(focal, sample) for sample in range(1, 11)}
        focal_result = {"maps": {}}
        for name in MAPS:
            hashes = [samples[sample][name]["sha256"] for sample in range(1, 11)]
            counts = Counter(hashes)
            pairs = []
            for left in range(1, 11):
                for right in range(left + 1, 11):
                    item = compare(
                        Path(samples[left][name]["path"]),
                        Path(samples[right][name]["path"]),
                        samples[left][name]["kind"],
                    )
                    item.update({"left": left, "right": right})
                    pairs.append(item)
            nearest = {}
            for sample in range(1, 11):
                candidates = [
                    item
                    for item in pairs
                    if item["left"] == sample or item["right"] == sample
                ]
                best = min(candidates, key=lambda item: item["normalized_rmse"])
                nearest[str(sample)] = {
                    "other": best["right"] if best["left"] == sample else best["left"],
                    "normalized_rmse": best["normalized_rmse"],
                    "symmetric_l1": best["symmetric_l1"],
                    "rmse": best["rmse"],
                    "unequal_fraction": best["unequal_fraction"],
                }
            focal_result["maps"][name] = {
                "kind": samples[1][name]["kind"],
                "logical_bytes": samples[1][name]["logical_bytes"],
                "exact_class_count": len(counts),
                "exact_class_sizes": sorted(counts.values(), reverse=True),
                "hashes": hashes,
                "pair_summary": summarize_pairs(pairs),
                "nearest_reference": nearest,
                "empirical_support_radius": {
                    field: max(item[field] for item in nearest.values())
                    for field in ("normalized_rmse", "symmetric_l1", "rmse", "unequal_fraction")
                },
            }
        output["focals"][str(focal)] = focal_result

    path = RUN_ROOT / "index5_repeat_distributions.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print("index5_repeat_distributions=OK", path)
    for focal, focal_result in output["focals"].items():
        for name, result in focal_result["maps"].items():
            print(
                focal,
                name,
                "classes",
                result["exact_class_count"],
                result["exact_class_sizes"],
                "pair_max_nrmse",
                result["pair_summary"]["normalized_rmse"]["maximum"],
                "support_nrmse",
                result["empirical_support_radius"]["normalized_rmse"],
            )


if __name__ == "__main__":
    main()
