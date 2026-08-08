#!/usr/bin/env python3
"""Stitch and summarize the captured four-focal undistorted cache planes."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/reference_undistorted_planes"
STITCH_PATH = Path(__file__).with_name("stitch_source_cache_tiles.py")
RUNS = {
    "28mm": RUN_ROOT / "unit1_28mm_tiles",
    "28mm_repeat": RUN_ROOT / "unit1_28mm_tiles_repeat",
    "35mm": RUN_ROOT / "unit1_35mm_tiles",
    "70mm": RUN_ROOT / "unit1_70mm_tiles",
    "150mm": RUN_ROOT / "unit1_150mm_tiles",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_stitch_module():
    spec = importlib.util.spec_from_file_location("undistort_stitch", STITCH_PATH)
    require(spec is not None and spec.loader is not None, "cannot load stitcher")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    stitch_module = load_stitch_module()
    analysis = {"runs": {}, "repeat_comparison": {}}
    for label, run_dir in RUNS.items():
        report_path = run_dir / "report.json"
        report = json.loads(report_path.read_text(encoding="ascii"))
        require(report["process"]["exit_status"] == 0, f"{label}: render failed")
        require(not report["errors"], f"{label}: {report['errors']}")
        camera_keys = sorted({item["camera_key"] for item in report["tiles"]})
        summaries = {}
        for camera_key in camera_keys:
            camera_name = next(
                item["camera_name"]
                for item in report["tiles"]
                if item["camera_key"] == camera_key
            )
            output_path = run_dir / f"{camera_name}_undistorted_plane.rgba16f"
            summary = stitch_module.stitch(report_path, output_path, camera_key)
            (run_dir / f"{camera_name}_undistorted_plane.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="ascii"
            )
            summaries[camera_name] = summary
        analysis["runs"][label] = {
            "hit_count": report["hit_count"],
            "cache_count": len(report["cache_objects"]),
            "tile_count": len(report["tiles"]),
            "planes": summaries,
        }

    base = analysis["runs"]["28mm"]["planes"]
    repeat = analysis["runs"]["28mm_repeat"]["planes"]
    require(set(base) == set(repeat), "28mm repeat camera set changed")
    for camera_name in sorted(base):
        first = base[camera_name]
        second = repeat[camera_name]
        analysis["repeat_comparison"][camera_name] = {
            "same_size": first["size"] == second["size"],
            "same_sha256": first["sha256"] == second["sha256"],
            "first_sha256": first["sha256"],
            "repeat_sha256": second["sha256"],
        }

    output = RUN_ROOT / "analysis.json"
    output.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print("undistorted_plane_analysis=OK", output)
    for label, run in analysis["runs"].items():
        print(
            label,
            run["hit_count"],
            run["tile_count"],
            [(name, value["size"], value["sha256"]) for name, value in run["planes"].items()],
        )
    print("28mm_repeat", analysis["repeat_comparison"])


if __name__ == "__main__":
    main()
