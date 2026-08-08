#!/usr/bin/env python3
"""Verify the wide/tele IRAMP score intervention and repeat-render floors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from compare_rgbe import compare


REPO = Path(__file__).resolve().parents[3]
RUNS = REPO / "runs/final_iramp_image_effect"
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/"
    "libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
PATCH_VA = 0x36E515
EXPECTED = bytes.fromhex("f30f51c0")
PATCH = bytes.fromhex("0f57c090")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_patch(path: Path) -> dict:
    packet = json.loads(path.read_text())
    require(packet["verified"] is True, f"unverified runtime patch: {path}")
    require(packet["written"] == 4, f"short runtime patch: {path}")
    require(packet["before"] == EXPECTED.hex(), f"wrong patch source: {path}")
    require(packet["after"] == PATCH.hex(), f"wrong patch target: {path}")
    require(
        packet["address"] - packet["libcp_header"] == PATCH_VA,
        f"wrong patch VA: {path}",
    )
    return packet


def metric(left: Path, right: Path) -> dict:
    result = compare(left, right)
    require(
        (result["width"], result["height"]) == (10432, 7824),
        f"unexpected HDR dimensions: {left}, {right}",
    )
    return result


def main() -> None:
    libcp = LIBCP.read_bytes()
    require(hashlib.sha256(libcp).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    require(
        libcp[PATCH_VA : PATCH_VA + len(EXPECTED)] == EXPECTED,
        "installed score-kernel prologue drift",
    )

    patch_reports = {
        "35mm_zero": verify_patch(RUNS / "unit1_35mm/patch.json"),
        "70mm_zero_a": verify_patch(RUNS / "unit1_70mm/patch.json"),
        "70mm_zero_b": verify_patch(RUNS / "unit1_70mm/patch_b.json"),
    }

    wide = RUNS / "unit1_35mm"
    tele = RUNS / "unit1_70mm"
    comparisons = {
        "35_baseline_a_vs_b": metric(
            wide / "baseline_a.hdr", wide / "baseline_b.hdr"
        ),
        "35_baseline_a_vs_zero": metric(
            wide / "baseline_a.hdr", wide / "zero_score.hdr"
        ),
        "35_baseline_b_vs_zero": metric(
            wide / "baseline_b.hdr", wide / "zero_score.hdr"
        ),
        "70_baseline_a_vs_b": metric(
            tele / "baseline_a.hdr", tele / "baseline_b.hdr"
        ),
        "70_zero_a_vs_b": metric(
            tele / "zero_score.hdr", tele / "zero_score_b.hdr"
        ),
        "70_baseline_a_vs_zero_a": metric(
            tele / "baseline_a.hdr", tele / "zero_score.hdr"
        ),
        "70_baseline_b_vs_zero_a": metric(
            tele / "baseline_b.hdr", tele / "zero_score.hdr"
        ),
        "70_baseline_a_vs_zero_b": metric(
            tele / "baseline_a.hdr", tele / "zero_score_b.hdr"
        ),
        "70_baseline_b_vs_zero_b": metric(
            tele / "baseline_b.hdr", tele / "zero_score_b.hdr"
        ),
    }

    wide_floor = comparisons["35_baseline_a_vs_b"]
    wide_cross = [
        comparisons["35_baseline_a_vs_zero"],
        comparisons["35_baseline_b_vs_zero"],
    ]
    require(
        min(row["mean_abs_code_all_channels"] for row in wide_cross)
        > 100.0 * wide_floor["mean_abs_code_all_channels"],
        "35mm intervention does not clear the repeat floor by 100x",
    )
    require(
        min(row["differing_pixel_fraction"] for row in wide_cross) > 0.5,
        "35mm intervention does not affect a majority of output pixels",
    )

    tele_within = [
        comparisons["70_baseline_a_vs_b"],
        comparisons["70_zero_a_vs_b"],
    ]
    tele_cross = [
        comparisons["70_baseline_a_vs_zero_a"],
        comparisons["70_baseline_b_vs_zero_a"],
        comparisons["70_baseline_a_vs_zero_b"],
        comparisons["70_baseline_b_vs_zero_b"],
    ]
    require(
        min(row["mean_abs_code_all_channels"] for row in tele_cross)
        > 2.0
        * max(row["mean_abs_code_all_channels"] for row in tele_within),
        "70mm treatment/control separation does not exceed twice both floors",
    )

    report = {
        "libcp_sha256": LIBCP_SHA256,
        "patch_va": hex(PATCH_VA),
        "patch_reports": patch_reports,
        "comparisons": comparisons,
        "wide_cross_to_floor_ratio": min(
            row["mean_abs_code_all_channels"] for row in wide_cross
        )
        / wide_floor["mean_abs_code_all_channels"],
        "tele_min_cross_to_max_within_ratio": min(
            row["mean_abs_code_all_channels"] for row in tele_cross
        )
        / max(row["mean_abs_code_all_channels"] for row in tele_within),
    }
    report_path = RUNS / "verification.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        "PASS final IRAMP image effect "
        f"wide_ratio={report['wide_cross_to_floor_ratio']:.3f} "
        f"tele_ratio={report['tele_min_cross_to_max_within_ratio']:.3f}"
    )
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
