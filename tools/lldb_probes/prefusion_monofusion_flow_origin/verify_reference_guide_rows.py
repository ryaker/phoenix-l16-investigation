#!/usr/bin/env python3
"""Compare installed tiled DemosaickLightV1 A/B rows with Phoenix planes."""

import argparse
import json
import math
import struct
from pathlib import Path


WIDTH = 4160
HEIGHT = 3120


def read_segment(path):
    raw = Path(path).read_bytes()
    assert len(raw) % 4 == 0
    return raw, struct.unpack(f"<{len(raw) // 4}f", raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("guide")
    parser.add_argument("residual")
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text(encoding="ascii"))
    phoenix_paths = {
        "A": Path(args.guide),
        "B": Path(args.residual),
    }
    expected_size = WIDTH * HEIGHT * 4
    for name, path in phoenix_paths.items():
        assert path.stat().st_size == expected_size, (name, path.stat().st_size)

    totals = {
        "words": 0,
        "mismatches": 0,
        "abs_sum": 0.0,
        "max_abs": 0.0,
        "nonfinite": 0,
        "internal_edge_mismatches": 0,
        "internal_edge_words": 0,
    }
    rows = []
    handles = {name: path.open("rb") for name, path in phoenix_paths.items()}
    try:
        for item in sorted(
            report["demosaic_guide_rows"],
            key=lambda value: (value["output_y"], value["x0"]),
        ):
            for installed_name, plane_name, row_delta in (
                ("A1", "A", 0),
                ("A2", "A", 1),
                ("B1", "B", 0),
                ("B2", "B", 1),
            ):
                y = item["output_y"] + row_delta
                x0, x1 = item["x0"], item["x1"]
                installed_raw, installed = read_segment(
                    item["rows"][installed_name]["path"]
                )
                words = x1 - x0
                assert len(installed) == words
                handle = handles[plane_name]
                handle.seek((y * WIDTH + x0) * 4)
                phoenix_raw = handle.read(words * 4)
                assert len(phoenix_raw) == len(installed_raw)
                phoenix = struct.unpack(f"<{words}f", phoenix_raw)

                mismatch = 0
                abs_sum = 0.0
                max_abs = 0.0
                nonfinite = 0
                internal_edge_mismatch = 0
                internal_edge_words = 0
                for index, (have, want) in enumerate(zip(phoenix, installed)):
                    same_bits = (
                        phoenix_raw[index * 4:(index + 1) * 4]
                        == installed_raw[index * 4:(index + 1) * 4]
                    )
                    at_internal_edge = (
                        (x0 != 0 and index < 8)
                        or (x1 != WIDTH and index >= words - 8)
                    )
                    if at_internal_edge:
                        internal_edge_words += 1
                    if not same_bits:
                        mismatch += 1
                        if at_internal_edge:
                            internal_edge_mismatch += 1
                    difference = abs(have - want)
                    if math.isfinite(difference):
                        abs_sum += difference
                        max_abs = max(max_abs, difference)
                    else:
                        nonfinite += 1

                rows.append({
                    "plane": plane_name,
                    "installed": installed_name,
                    "y": y,
                    "x0": x0,
                    "x1": x1,
                    "words": words,
                    "mismatches": mismatch,
                    "mean_abs": abs_sum / words,
                    "max_abs": max_abs,
                    "internal_edge_mismatches": internal_edge_mismatch,
                    "internal_edge_words": internal_edge_words,
                })
                totals["words"] += words
                totals["mismatches"] += mismatch
                totals["abs_sum"] += abs_sum
                totals["max_abs"] = max(totals["max_abs"], max_abs)
                totals["nonfinite"] += nonfinite
                totals["internal_edge_mismatches"] += internal_edge_mismatch
                totals["internal_edge_words"] += internal_edge_words
    finally:
        for handle in handles.values():
            handle.close()

    totals["mean_abs"] = totals.pop("abs_sum") / totals["words"]
    result = {"totals": totals, "segments": rows}
    print(json.dumps(result, indent=2))
    return 0 if totals["mismatches"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
