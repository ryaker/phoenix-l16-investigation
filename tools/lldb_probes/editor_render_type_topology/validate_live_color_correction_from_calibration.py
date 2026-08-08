#!/usr/bin/env python3
"""Join public calibration maps to the retained live index-10 image effect."""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
from pathlib import Path


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def reciprocal_temperature_alpha(scene: float, lower: float, upper: float) -> float:
    reciprocal_upper = f32(f32(1.0) / f32(upper))
    reciprocal_lower = f32(f32(1.0) / f32(lower))
    numerator = (1.0 / float(f32(scene))) - float(reciprocal_upper)
    denominator = float(f32(reciprocal_lower - reciprocal_upper))
    return f32(numerator / denominator)


def interpolate_maps(upper_raw: bytes, lower_raw: bytes, alpha: float) -> bytes:
    if len(upper_raw) != len(lower_raw) or len(upper_raw) != 1089 * 16:
        raise ValueError("candidate map size mismatch")
    upper = struct.iter_unpack("<f", upper_raw)
    lower = struct.iter_unpack("<f", lower_raw)
    one_minus = f32(f32(1.0) - alpha)
    values = []
    for (upper_value,), (lower_value,) in zip(upper, lower):
        upper_term = f32(upper_value * one_minus)
        lower_term = f32(lower_value * alpha)
        values.append(f32(upper_term + lower_term))
    return struct.pack("<%df" % len(values), *values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map-manifest", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--body", default="unit1")
    parser.add_argument("--scene-cct", type=float, required=True)
    parser.add_argument("--lower-cct", type=float, required=True)
    parser.add_argument("--upper-cct", type=float, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.map_manifest.read_text())
    records = {
        (item["camera_id"], item["illuminant_type"]): item
        for item in manifest["results"]
        if item["body"] == args.body
    }
    camera_ids = sorted({camera for camera, _ in records})
    alpha = reciprocal_temperature_alpha(
        args.scene_cct, args.lower_cct, args.upper_cct
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for camera_id in camera_ids:
        lower = records[(camera_id, 0)]
        upper = records[(camera_id, 2)]
        candidate = interpolate_maps(
            Path(upper["map_path"]).read_bytes(),
            Path(lower["map_path"]).read_bytes(),
            alpha,
        )
        candidate_path = args.output_dir / f"camera_{camera_id:02d}_live_map.raw"
        candidate_path.write_bytes(candidate)
        completed = subprocess.run(
            [
                str(args.replay),
                str(args.input),
                str(candidate_path),
                str(args.expected),
            ],
            text=True,
            capture_output=True,
        )
        match = re.search(r"different_bytes=(\d+)", completed.stdout)
        if match is None:
            raise RuntimeError(
                f"camera {camera_id}: replay did not report a byte comparison: "
                f"{completed.stdout} {completed.stderr}"
            )
        results.append(
            {
                "camera_id": camera_id,
                "different_bytes": int(match.group(1)),
                "exact": completed.returncode == 0,
                "candidate_map": str(candidate_path),
                "replay_output": completed.stdout.strip().splitlines(),
            }
        )
    results.sort(key=lambda item: (item["different_bytes"], item["camera_id"]))
    exact = [item for item in results if item["exact"]]
    report = {
        "body": args.body,
        "scene_cct": f32(args.scene_cct),
        "lower_cct": f32(args.lower_cct),
        "upper_cct": f32(args.upper_cct),
        "alpha_word": "0x%08x" % struct.unpack("<I", struct.pack("<f", alpha))[0],
        "alpha": alpha,
        "camera_count": len(camera_ids),
        "exact_camera_ids": [item["camera_id"] for item in exact],
        "results": results,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if len(exact) != 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
