#!/usr/bin/env python3
"""Verify the canonical tele firing topology from public LRIs and runtime."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import lane_b_crossunit_lri_public_carriers as carriers  # noqa: E402


RUNTIME_REPORTS = {
    "70mm": ROOT / "runs/capturedimage_f2770_origin/f2770_origin_70mm.json",
    "150mm": ROOT / "runs/capturedimage_f2770_origin/f2770_origin_150mm.json",
}
EXPECTED_IDS = list(range(5, 16))
EXPECTED_NAMES = [f"B{i}" for i in range(1, 6)] + [f"C{i}" for i in range(1, 7)]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_public_lris() -> list[dict]:
    report = carriers.build_report()
    tele_rows = [
        row for row in report["exact_focal_seeds"]
        if row["label"].endswith(("70mm", "150mm"))
    ]
    require(len(tele_rows) == 4, f"expected four two-body tele rows, got {len(tele_rows)}")

    seen = set()
    for row in tele_rows:
        names = row["modules"]["fired_camera_names"]
        ids = row["modules"]["fired_camera_ids"]
        require(ids == EXPECTED_IDS, f"{row['label']}: fired ids {ids}")
        require(names == EXPECTED_NAMES, f"{row['label']}: fired names {names}")
        seen.add((row["intrinsics"]["sha256_16"], row["focal"]))

    require(
        seen
        == {
            (carriers.UNIT1_SIG, 70),
            (carriers.UNIT1_SIG, 149),
            (carriers.UNIT2_SIG, 70),
            (carriers.UNIT2_SIG, 149),
        },
        f"unexpected body/focal coverage {seen}",
    )
    return tele_rows


def verify_runtime() -> list[dict]:
    rows = []
    for tier, path in RUNTIME_REPORTS.items():
        require(path.is_file(), f"missing runtime report {path}")
        report = json.loads(path.read_text())
        require(report["counts"] == {"pre": 11, "post": 11}, f"{tier}: counts")
        require(not report["errors"], f"{tier}: runtime errors {report['errors']}")
        require(not report["pending"], f"{tier}: unmatched constructor event")
        require(len(report["events"]) == 11, f"{tier}: event count")

        ids = sorted(event["output_fields"]["u32_0x60"] for event in report["events"])
        active = [event["output_fields"]["byte_0x30"] for event in report["events"]]
        require(ids == EXPECTED_IDS, f"{tier}: runtime camera ids {ids}")
        require(active == [1] * 11, f"{tier}: constructor active bytes {active}")

        hdr_path = path.with_suffix(".hdr")
        require(hdr_path.is_file(), f"{tier}: missing completed HDR {hdr_path}")
        header = hdr_path.open("rb").read(1024).decode("ascii", errors="ignore")
        require(
            re.search(r"-Y 7824 \+X 10432", header) is not None,
            f"{tier}: unexpected HDR dimensions",
        )
        rows.append(
            {
                "tier": tier,
                "report": str(path.relative_to(ROOT)),
                "camera_ids": ids,
                "active_bytes": active,
                "hdr": str(hdr_path.relative_to(ROOT)),
                "hdr_dimensions": [10432, 7824],
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    public_rows = verify_public_lris()
    runtime_rows = verify_runtime()
    result = {
        "status": "OK",
        "public_lri_scope": [
            {
                "label": row["label"],
                "path": row["path"],
                "focal": row["focal"],
                "unit_signature": row["intrinsics"]["sha256_16"],
                "fired_camera_ids": row["modules"]["fired_camera_ids"],
                "fired_camera_names": row["modules"]["fired_camera_names"],
            }
            for row in public_rows
        ],
        "runtime_scope": runtime_rows,
        "conclusion": "canonical tele firing set is B1..B5,C1..C6; not C-only",
        "scope_guard": (
            "The two calibration bodies and capture dates corroborate topology only; "
            "no observed difference is attributed to body or firmware."
        ),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(
        "PASS tele firing topology "
        "public=Unit1+Unit2@70/150 runtime=Unit1@70/150 "
        "set=B1..B5,C1..C6"
    )


if __name__ == "__main__":
    main()
