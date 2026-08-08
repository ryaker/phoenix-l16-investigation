#!/usr/bin/env python3
"""Verify full-map index-to-millimeter-depth coupling for all 40 samples."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
ANALYZER_PATH = Path(__file__).with_name("analyze_index5_repeat_distributions.py")
LOOKUP_PATH = (
    ROOT
    / "tools/lldb_probes/codex_index5_lookup_vector_public_origin"
    / "verify_lookup_vector_public_origin.py"
)
COUNTS = {28: 752, 35: 752, 70: 1472, 150: 1472}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYZER = load_module("index5_distribution_analyzer", ANALYZER_PATH)
LOOKUP = load_module("index5_lookup_formula", LOOKUP_PATH)


def main() -> None:
    output = {"focals": {}}
    total_pixels = 0
    for focal, count in COUNTS.items():
        lookup = np.asarray(LOOKUP.expected_reciprocal_ramp(count), dtype="<f4")
        samples = []
        for sample in range(1, 11):
            captures = ANALYZER.load_sample(focal, sample)
            index_item = captures["index5_hypothesis_index"]
            depth_item = captures["index5_depth"]
            indices = np.memmap(index_item["path"], dtype="<u2", mode="r")
            depth = np.memmap(depth_item["path"], dtype="<f4", mode="r")
            require(indices.shape == depth.shape, f"{focal}/{sample}: shape mismatch")
            require(int(indices.max()) < count, f"{focal}/{sample}: index outside lookup")
            expected = lookup[indices]
            mismatch = int(np.count_nonzero(expected.view("<u4") != depth.view("<u4")))
            require(mismatch == 0, f"{focal}/{sample}: {mismatch} depth-word mismatches")
            require(np.isfinite(depth).all(), f"{focal}/{sample}: nonfinite depth")
            require(float(depth.min()) >= 200.0, f"{focal}/{sample}: depth below bound")
            require(float(depth.max()) <= 640000.0, f"{focal}/{sample}: depth above bound")
            total_pixels += int(indices.size)
            samples.append(
                {
                    "sample": sample,
                    "pixel_count": int(indices.size),
                    "index_minimum": int(indices.min()),
                    "index_maximum": int(indices.max()),
                    "depth_minimum_mm": float(depth.min()),
                    "depth_maximum_mm": float(depth.max()),
                    "bit_mismatches": mismatch,
                }
            )
        output["focals"][str(focal)] = {"lookup_count": count, "samples": samples}
    output["total_pixels"] = total_pixels
    path = ROOT / "runs/reference_stage_maps/index5_full_map_coupling.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print("index5_full_map_coupling=OK", path, "pixels", total_pixels, "mismatches", 0)


if __name__ == "__main__":
    main()
