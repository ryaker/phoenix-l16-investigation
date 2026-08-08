#!/usr/bin/env python3
"""Verify the full-corpus firing-set census and supported variant renders."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "runs/lri_firing_set_census/corpus_firing_sets.json"
RENDERS = ROOT / "runs/lri_firing_set_census/renders"

WIDE = "A1,A2,A3,A4,A5,B1,B2,B3,B4,B5"
TELE = "B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6"
COMPLETE_ROUTE_EXCEPTIONS = {
    "/Volumes/Base Photos/Light/2018-05-25/L16_01175.lri": (28, 8, TELE),
    "/Volumes/Base Photos/Light/2018-06-26/L16_01931.lri": (74, 0, WIDE),
    "/Volumes/Base Photos/Light/2018-10-24/L16_02786.lri": (28, 8, TELE),
}
VARIANT_CROPS = {
    "/Volumes/Base Photos/Light/2018-05-25/L16_01175.lri":
        ([0.26682692766189575, 0.2666666805744171, 0.7331730723381042, 0.7333333492279053], 0),
    "/Volumes/Base Photos/Light/2018-06-26/L16_01931.lri":
        ([0.0951923057436943, 0.10256410390138626, 0.8951923251152039, 0.9025641083717346], 0),
    "/Volumes/Base Photos/Light/2018-10-24/L16_02786.lri":
        ([0.26682692766189575, 0.2666666805744171, 0.7331730723381042, 0.7333333492279053], 1),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_hdr(name: str) -> None:
    path = RENDERS / name
    require(path.exists(), f"missing render {path}")
    with path.open("rb") as stream:
        header = stream.read(96)
    require(header.startswith(b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n"), f"bad HDR header {path}")
    require(b"-Y 7824 +X 10432\n" in header, f"bad HDR dimensions {path}")
    require(path.stat().st_size > 300_000_000, f"truncated HDR {path}")


def main() -> int:
    data = json.loads(REPORT.read_text())
    require(data["status"] == "PASS", "census status")
    require(data["lri_count"] == data["decoded_count"] == 9438, "corpus count")
    require(data["failure_count"] == 0, "decode failures")
    require(data["complete_count"] == 9242, "complete count")
    require(data["incomplete_count"] == 196, "incomplete count")
    require(
        data["firing_set_counts"].get(f"complete|{WIDE}") == 6078,
        "complete wide count",
    )
    require(
        data["firing_set_counts"].get(f"complete|{TELE}") == 3164,
        "complete tele count",
    )
    require(
        set(key for key in data["firing_set_counts"] if key.startswith("complete|"))
        == {f"complete|{WIDE}", f"complete|{TELE}"},
        "unexpected complete firing set",
    )
    require(
        data["reference_firing_set_counts"]
        == {f"complete|0|{WIDE}": 6078, f"complete|8|{TELE}": 3164,
            **{key: value for key, value in data["reference_firing_set_counts"].items()
               if key.startswith("incomplete|")}},
        "complete reference-camera/firing-set invariant",
    )

    complete_exceptions = {
        row["path"]: (row["focal"], row["reference_camera"], ",".join(row["firing_names"]))
        for row in data["focal_route_exceptions"]
        if row["complete"]
    }
    require(complete_exceptions == COMPLETE_ROUTE_EXCEPTIONS, "complete focal-route exceptions")
    variant_rows = {
        row["path"]: (row["crop"], row["orientation"])
        for row in data["focal_route_exceptions"]
        if row["complete"]
    }
    require(variant_rows == VARIANT_CROPS, "variant public crop/orientation")
    require(
        all(not row["complete"] for row in data["exceptions"] if row["firing_class"] == "outlier"),
        "reduced/unknown firing set in a complete LRI",
    )

    verify_hdr("L16_01175_profile3.hdr")
    verify_hdr("L16_01931_profile3.hdr")
    verify_hdr("L16_02786_profile3.hdr")
    print(
        "lri_firing_set_census=OK "
        "complete=9242 wide=6078 tele=3164 "
        "reference_invariant=A1->wide,B4->tele focal_route_exceptions=3 renders=3"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
