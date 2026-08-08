#!/usr/bin/env python3
"""Validate the lightweight 0x20ca00 solve/output runtime report."""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUN_DIR = ROOT / "runs/prefusion_20ca00_solve_output_only"
DEFAULT_STEM = "prefusion_20ca00_solve_output_only_28mm"
EXPECTED_SITES = {
    "solve_pre_20d611",
    "first_triple_post_20d6b6",
    "second_triple_post_20d737",
}
OPTIONAL_SITE = "solve_post_20d616"
LOWER_BOUND = 200.0
UPPER_BOUND = 640000.0
LEGACY_28MM = {
    "stem": DEFAULT_STEM,
    "frames": 10,
    "groups": 1229,
    "paired_post": 907,
    "missing_post": 322,
    "max_frame_end": 6832,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--stem", default=DEFAULT_STEM)
    args = parser.parse_args()

    report_path = args.run_dir / f"{args.stem}.json"
    log_path = args.run_dir / f"{args.stem}.log"
    hdr_path = args.run_dir / f"{args.stem}.hdr"
    legacy_strict = args.stem == LEGACY_28MM["stem"]

    report = json.loads(report_path.read_text())
    log = log_path.read_text(errors="replace")
    require("Process " in log and "exited with status = 0" in log, "clean process exit missing")
    require("Traceback" not in log, "callback traceback present")
    require("error:" not in log.lower(), "LLDB error present")
    with hdr_path.open("rb") as handle:
        require(handle.read(10) == b"#?RADIANCE", "HDR output magic mismatch")
    require(report["errors"] == [], "probe errors present")
    require(report["incomplete_frames"] == [], "incomplete callback frames present")
    require(report["include_add_residual"] is False, "expected solve-only probe")

    frames = report["frames"]
    counts = report["counts"]
    require(len(frames) > 0, "no callback frames captured")
    require(counts["entries"] == len(frames), "entry/frame count mismatch")
    require(counts["returns"] == len(frames), "return/frame count mismatch")
    require(all(frame["completed"] for frame in frames), "incomplete frame flag")
    if legacy_strict:
        require(
            len(frames) == LEGACY_28MM["frames"],
            f"expected {LEGACY_28MM['frames']} callback frames, got {len(frames)}",
        )

    site_counts: Counter[str] = Counter()
    group_shapes: Counter[tuple[str, ...]] = Counter()
    changed = 0
    unchanged = 0
    paired_post = 0
    missing_post = 0
    first_z_eq_solved = 0
    pre_z_eq_pre = 0
    final_z_eq_solved = 0
    second_transform_changed = 0
    mode0_pre_outside = 0
    mode0_solved_outside = 0
    deltas: list[float] = []
    pre_values: list[float] = []
    solved_values: list[float] = []
    final_z_values: list[float] = []

    for frame in frames:
        entry = frame["entry"]
        start = entry["start_index"]
        end = entry["outer_count"]
        require(0 <= start < end, f"invalid frame range {start}..{end}")
        if legacy_strict:
            require(
                end <= LEGACY_28MM["max_frame_end"],
                f"invalid legacy frame range {start}..{end}",
            )

        groups: dict[int, list[dict]] = defaultdict(list)
        for snapshot in frame["snapshots"]:
            groups[snapshot["gate_index"]].append(snapshot)
            site_counts[snapshot["site"]] += 1

        for gate_index, snapshots in groups.items():
            require(start <= gate_index < end, f"gate index {gate_index} outside frame range")
            by_site: dict[str, dict] = {}
            for snapshot in snapshots:
                site = snapshot["site"]
                require(site not in by_site, f"duplicate {site} for gate {gate_index}")
                by_site[site] = snapshot
            sites = set(by_site)
            require(EXPECTED_SITES <= sites, f"missing required site for gate {gate_index}: {sites}")
            require(sites <= EXPECTED_SITES | {OPTIONAL_SITE}, f"unexpected site set {sites}")
            group_shapes[tuple(sorted(sites))] += 1

            pre = by_site["solve_pre_20d611"]
            first = by_site["first_triple_post_20d6b6"]
            second = by_site["second_triple_post_20d737"]
            expected_offset = 5 * gate_index
            expected_addr = pre["source_record_begin"] + 4 * expected_offset + 8

            for snapshot in (pre, first, second):
                require(snapshot["source_record_offset"] == expected_offset, "record offset/index mismatch")
                require(snapshot["output_triple"]["read_ok"], "triple read failed")
                require(snapshot["output_triple"]["addr"] == expected_addr, "triple address mismatch")
                require(math.isfinite(snapshot["parameter_scalar"]), "nonfinite scalar")
                if legacy_strict:
                    require(
                        LOWER_BOUND <= snapshot["parameter_scalar"] <= UPPER_BOUND,
                        "scalar outside bounds",
                    )

            pre_scalar = pre["parameter_scalar"]
            solved_scalar = first["parameter_scalar"]
            pre_values.append(pre_scalar)
            solved_values.append(solved_scalar)
            final_z_values.append(second["output_triple"]["values"][2])
            delta = solved_scalar - pre_scalar
            deltas.append(delta)
            if delta == 0.0:
                unchanged += 1
            else:
                changed += 1
            if not (LOWER_BOUND <= pre_scalar <= UPPER_BOUND):
                mode0_pre_outside += 1
            if not (LOWER_BOUND <= solved_scalar <= UPPER_BOUND):
                mode0_solved_outside += 1

            require(first["parameter_scalar"] == second["parameter_scalar"], "scalar drift between writes")
            if first["output_triple"]["hex"] != second["output_triple"]["hex"]:
                second_transform_changed += 1
            if legacy_strict:
                require(
                    first["output_triple"]["hex"] == second["output_triple"]["hex"],
                    "second transform changed triple",
                )
            if pre["output_triple"]["values"][2] == f32(pre_scalar):
                pre_z_eq_pre += 1
            if legacy_strict:
                require(pre["output_triple"]["values"][2] == f32(pre_scalar), "pre triple z/scalar mismatch")
            require(first["output_triple"]["values"][2] == f32(solved_scalar), "post triple z/scalar mismatch")
            first_z_eq_solved += 1
            if second["output_triple"]["values"][2] == f32(solved_scalar):
                final_z_eq_solved += 1

            post = by_site.get(OPTIONAL_SITE)
            if post is None:
                missing_post += 1
            else:
                paired_post += 1
                require(post["parameter_scalar"] == solved_scalar, "post-call scalar mismatch")
                require(post["output_triple"]["hex"] == pre["output_triple"]["hex"], "triple changed before write sites")

    total = changed + unchanged
    require(total > 0, "no solve/write groups captured")
    require(changed > 0, "no solve-adjusted scalar observed")
    if legacy_strict:
        require(
            total == LEGACY_28MM["groups"],
            f"expected {LEGACY_28MM['groups']} solve/write groups, got {total}",
        )
        require(
            paired_post == LEGACY_28MM["paired_post"]
            and missing_post == LEGACY_28MM["missing_post"],
            "post-stop coverage drift",
        )
    require(site_counts["solve_pre_20d611"] == total, "solve-pre count mismatch")
    require(site_counts["first_triple_post_20d6b6"] == total, "first-write count mismatch")
    require(site_counts["second_triple_post_20d737"] == total, "second-write count mismatch")
    require(site_counts["solve_post_20d616"] == paired_post, "solve-post count mismatch")
    require(counts["solve_pre_hits"] == total, "reported solve-pre count mismatch")
    require(counts["solve_post_hits"] == paired_post, "reported solve-post count mismatch")
    require(counts["first_triple_post_hits"] == total, "reported first-write count mismatch")
    require(counts["second_triple_post_hits"] == total, "reported second-write count mismatch")

    print(f"report={report_path}")
    print(f"frames={len(frames)} completed={counts['returns']}")
    print(f"groups={total} paired_post={paired_post} missing_post={missing_post}")
    print(f"solve_changed={changed} solve_unchanged={unchanged}")
    print(f"pre_range=[{min(pre_values):.9f},{max(pre_values):.9f}]")
    print(f"solved_range=[{min(solved_values):.9f},{max(solved_values):.9f}]")
    print(f"delta_range=[{min(deltas):.9f},{max(deltas):.9f}] max_abs={max(map(abs, deltas)):.9f}")
    print(f"mode0_bound_outside_pre={mode0_pre_outside} solved={mode0_solved_outside}")
    print(f"pre_triple_z=f32(pre_scalar) {pre_z_eq_pre}/{total}")
    print(f"first_triple_z=f32(solved_scalar) {first_z_eq_solved}/{total}")
    print(f"second_transform_changed={second_transform_changed}/{total}")
    print(f"final_triple_z=f32(solved_scalar) {final_z_eq_solved}/{total}")
    print(f"final_z_range=[{min(final_z_values):.9f},{max(final_z_values):.9f}]")


if __name__ == "__main__":
    main()
