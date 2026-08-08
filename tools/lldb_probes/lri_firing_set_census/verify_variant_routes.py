#!/usr/bin/env python3
"""Verify the compact supported-variant route campaign."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/lri_firing_set_census"
CROP_150 = [0.26682692766189575, 0.2666666805744171, 0.7331730723381042, 0.7333333492279053]
CROP_74 = [0.0951923057436943, 0.10256410390138626, 0.8951923251152039, 0.9025641083717346]
CASES = {
    "unit1_28mm_tele": {"key": 8, "mode": 1, "family": None, "crop": CROP_150, "c6": 1, "mono0": 0},
    "unit2_28mm_tele": {"key": 8, "mode": 1, "family": "b", "crop": CROP_150, "c6": 1, "mono0": 0},
    "unit2_74mm_wide": {"key": 0, "mode": 0, "family": "a", "crop": CROP_74, "c6": 0, "mono0": 1},
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify(label, expected):
    data = json.loads((RUN / f"variant_route_{label}.json").read_text())
    require(data["process"]["exit_status"] == 0, f"{label}: exit")
    require(not data["drive_hit_step_cap"] and not data["errors"], f"{label}: probe")
    require([row["camera_key"] for row in data["reference_entries"]] == [expected["key"]], f"{label}: key")
    require([row["mode"] for row in data["mode_stores"]] == [expected["mode"]], f"{label}: mode")
    if expected["family"] is None:
        require(data["counts"]["family_a"] == 0, f"{label}: unexpected family A")
        require(data["counts"]["family_b"] == 0, f"{label}: unexpected family B")
    else:
        require(data["counts"][f"family_{expected['family']}"] == 4, f"{label}: family")
        sibling = "a" if expected["family"] == "b" else "b"
        require(data["counts"][f"family_{sibling}"] == 0, f"{label}: sibling")
    require(data["counts"]["monofusion_mode1_worker"] == 0, f"{label}: mode1")
    if expected["mono0"]:
        require(data["counts"]["monofusion_mode0_worker"] > 0, f"{label}: mono0")
    else:
        require(data["counts"]["monofusion_mode0_worker"] == 0, f"{label}: mono0")
    require(data["counts"]["c6_clear"] == expected["c6"], f"{label}: c6 count")
    for row in data["c6_clears"]:
        require(row["camera_key_0x60"] == 15 and row["active_before_0x30"] == 1, f"{label}: c6 identity")
    require(len(data["crop_results"]) == 1, f"{label}: crop count")
    crop = data["crop_results"][0]
    require(crop["reference_camera_0x44"] == expected["key"], f"{label}: crop reference")
    require(crop["crop"] == expected["crop"], f"{label}: crop")
    hdr = RUN / f"variant_route_{label}.hdr"
    require(hdr.read_bytes()[:16].startswith(b"#?RADIANCE"), f"{label}: HDR")
    family = expected["family"] or "selected-b-no-live-call"
    return f"{label}=key{expected['key']}/mode{expected['mode']}/family{family}"


def main():
    print("variant_routes=OK " + " ".join(verify(label, expected) for label, expected in CASES.items()))


if __name__ == "__main__":
    main()
