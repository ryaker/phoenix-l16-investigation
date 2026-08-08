#!/usr/bin/env python3
"""Stitch one captured SourceImageCache RGBA16F tile partition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def stitch(report_path: Path, output_path: Path, camera_key: int | None = None) -> dict:
    report = json.loads(report_path.read_text(encoding="ascii"))
    tiles = report["tiles"]
    require(tiles, "no captured tiles")
    camera_keys = sorted({item["camera_key"] for item in tiles})
    if camera_key is None:
        require(len(camera_keys) == 1, f"select one camera from {camera_keys}")
        camera_key = camera_keys[0]
    tiles = [item for item in tiles if item["camera_key"] == camera_key]
    require(tiles, f"no tiles for camera key {camera_key}")
    caches = {item["cache"] for item in tiles}
    require(len(caches) == 1, f"multiple caches for camera key {camera_key}: {caches}")
    by_index = {(item["tile_index"][1], item["tile_index"][2]): item for item in tiles}
    xs = sorted({index[0] for index in by_index})
    ys = sorted({index[1] for index in by_index})
    require(xs == list(range(max(xs) + 1)), f"non-contiguous x indices: {xs}")
    require(ys == list(range(max(ys) + 1)), f"non-contiguous y indices: {ys}")
    require(len(by_index) == len(xs) * len(ys), "incomplete tile grid")

    row_widths = []
    row_heights = []
    for y in ys:
        widths = [by_index[(x, y)]["descriptor"]["size"][0] for x in xs]
        heights = {by_index[(x, y)]["descriptor"]["size"][1] for x in xs}
        require(len(heights) == 1, f"inconsistent heights in tile row {y}")
        row_widths.append(sum(widths))
        row_heights.append(heights.pop())
    require(len(set(row_widths)) == 1, f"inconsistent stitched widths: {row_widths}")
    width = row_widths[0]
    height = sum(row_heights)

    digest = hashlib.sha256()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as output:
        for y in ys:
            tile_handles = [Path(by_index[(x, y)]["path"]).open("rb") for x in xs]
            try:
                tile_height = by_index[(xs[0], y)]["descriptor"]["size"][1]
                for _ in range(tile_height):
                    for x, handle in zip(xs, tile_handles):
                        tile_width = by_index[(x, y)]["descriptor"]["size"][0]
                        raw = handle.read(tile_width * 8)
                        require(len(raw) == tile_width * 8, f"short tile row at {(x, y)}")
                        output.write(raw)
                        digest.update(raw)
                for x, handle in zip(xs, tile_handles):
                    require(not handle.read(1), f"trailing tile bytes at {(x, y)}")
            finally:
                for handle in tile_handles:
                    handle.close()

    result = {
        "report": str(report_path),
        "output": str(output_path),
        "cache": caches.pop(),
        "camera_key": camera_key,
        "camera_name": tiles[0].get("camera_name"),
        "grid": [len(xs), len(ys)],
        "size": [width, height],
        "pixel_format": "RGBA16F little-endian",
        "logical_bytes": width * height * 8,
        "sha256": digest.hexdigest(),
    }
    require(output_path.stat().st_size == result["logical_bytes"], "stitched size mismatch")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--camera-key", type=int)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    result = stitch(args.report, args.output, args.camera_key)
    if args.summary:
        args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print("source_cache_tile_stitch=OK", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
