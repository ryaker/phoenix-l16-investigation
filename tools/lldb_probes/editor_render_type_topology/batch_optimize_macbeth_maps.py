#!/usr/bin/env python3
"""Run the installed HSV-map optimizer across extracted calibration records."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path


def map_stats(raw: bytes) -> dict:
    cells = list(struct.iter_unpack("<4f", raw))
    if len(cells) != 1089:
        raise ValueError(f"expected 1089 cells, got {len(cells)}")
    return {
        "cell_count": len(cells),
        "lane_min": [min(cell[lane] for cell in cells) for lane in range(4)],
        "lane_max": [max(cell[lane] for cell in cells) for lane in range(4)],
        "lane_mean": [math.fsum(cell[lane] for cell in cells) / len(cells) for lane in range(4)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    results = []
    for body in manifest["bodies"]:
        body_dir = args.output_dir / body["body"]
        body_dir.mkdir(parents=True, exist_ok=True)
        for record in body["records"]:
            stem = f"camera_{record['camera_id']:02d}_type_{record['illuminant_type']}"
            map_path = body_dir / f"{stem}_hsv_map_vec4_f32.raw"
            completed = subprocess.run(
                [
                    "arch",
                    "-x86_64",
                    str(args.executable),
                    record["raw_path"],
                    str(map_path),
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            packet = json.loads(completed.stdout)
            if not packet["manual_optimizer_matches_wrapper"]:
                raise ValueError(f"{body['body']} {stem}: optimizer/wrapper mismatch")
            raw = map_path.read_bytes()
            results.append(
                {
                    "body": body["body"],
                    "camera_id": record["camera_id"],
                    "illuminant_type": record["illuminant_type"],
                    "source_sha256": record["raw_sha256"],
                    "matrix": packet["matrix"],
                    "matrix_words": packet["matrix_words"],
                    "optimizer_matrix": packet["optimizer_matrix"],
                    "optimizer_matrix_words": packet["optimizer_matrix_words"],
                    "manual_optimizer_matches_wrapper": True,
                    "map_dimensions": packet["map_dimensions"],
                    "map_path": str(map_path),
                    "map_sha256": hashlib.sha256(raw).hexdigest(),
                    "map_stats": map_stats(raw),
                }
            )
    results.sort(key=lambda item: (item["body"], item["camera_id"], item["illuminant_type"]))
    expected = sum(body["record_count"] for body in manifest["bodies"])
    if len(results) != expected:
        raise ValueError(f"expected {expected} results, got {len(results)}")
    print(
        json.dumps(
            {
                "input_manifest": str(args.manifest),
                "result_count": len(results),
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
