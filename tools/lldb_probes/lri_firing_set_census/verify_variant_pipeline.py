#!/usr/bin/env python3
"""Verify complete image-pipeline routing for the three supported variants."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/lri_firing_set_census"
ROUTE_VERIFIER = ROOT / "tools/lldb_probes/lri_firing_set_census/verify_variant_routes.py"
SELECTOR_VERIFIER = ROOT / "tools/lldb_probes/lri_firing_set_census/verify_reference_camera_family_selector.py"

CASES = {
    "unit1_28mm_tele": {
        "ids": [10, 11, 12, 13, 14],
        "scale": 2.1384615898132324,
        "c6": 1,
        "mono0": 0,
        "scorer_a": 0,
        "scorer_b": 0,
    },
    "unit2_28mm_tele": {
        "ids": [10, 11, 12, 13, 14],
        "scale": 2.1384615898132324,
        "c6": 1,
        "mono0": 0,
        "scorer_a": 0,
        "scorer_b": 8,
    },
    "unit2_74mm_wide": {
        "ids": [5, 6, 7, 8, 9],
        "scale": 2.507692337036133,
        "c6": 0,
        "mono0": 8,
        "scorer_a": 8,
        "scorer_b": 0,
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def camera_ids(entry: dict, label: str) -> list[int]:
    ids = []
    for item in entry["contributors"]:
        exact = [
            candidate["camera_id"]
            for candidate in item["candidate_funcdata_fields"]
            if candidate["object_offset"] == 8
        ]
        require(len(exact) == 1, f"{label}: contributor {item['index']} +0x08 camera field")
        ids.append(exact[0])
    return ids


def verify_case(label: str, expected: dict) -> str:
    path = RUN / f"variant_pipeline_{label}.json"
    require(path.exists(), f"{label}: missing report")
    packet = json.loads(path.read_text())
    require(packet.get("process", {}).get("exit_status") == 0, f"{label}: process exit")
    require(not packet.get("drive_hit_step_cap"), f"{label}: drive step cap")
    require(packet.get("errors") == [], f"{label}: probe errors")
    require(packet.get("cap") == 8, f"{label}: cap")

    counts = packet["counts"]
    exact_counts = {
        "calib_state_dispatcher": 2,
        "c6_clear": expected["c6"],
        "guided_upsample": 1,
        "warp_record_builder": 5,
        "cross_category_warp": 5,
        "stereo_runpass_sibling": 0,
        "stereo_cost_sibling": 0,
        "monofusion_mode1": 0,
        "monofusion_mode0": expected["mono0"],
        "prefusion_scorer_a": expected["scorer_a"],
        "prefusion_scorer_b": expected["scorer_b"],
    }
    for name, value in exact_counts.items():
        require(counts[name] == value, f"{label}: {name}={counts[name]} expected {value}")

    capped_live = [
        "stereo_runpass_dispatch",
        "stereo_runpass_primary",
        "stereo_tile_state_builder",
        "stereo_cost_primary",
        "range_map_builder",
        "iramp_src1_wrapper",
        "iramp_src2_wrapper",
        "iramp_direct_wrapper",
        "iramp_entry",
        "iramp_inner",
        "iramp_accumulator",
    ]
    for name in capped_live:
        require(counts[name] == 8, f"{label}: {name} did not reach cap")

    require(len(packet["iramp_entries"]) == 1, f"{label}: IRAMP packet count")
    entry = packet["iramp_entries"][0]
    require(camera_ids(entry, label) == expected["ids"], f"{label}: contributor IDs")
    require(entry["source_count"] == 5, f"{label}: source count")
    require(entry["scale"] == expected["scale"], f"{label}: scale")
    require(entry["warp_vector_end"] - entry["warp_vector_begin"] == 5 * 0x50, f"{label}: warp span")
    roi = entry["roi"]
    require(roi[2] - roi[0] == 512 and roi[3] - roi[1] == 512, f"{label}: first ROI")

    hdr = RUN / f"variant_pipeline_{label}.hdr"
    require(hdr.read_bytes()[:16].startswith(b"#?RADIANCE"), f"{label}: HDR")
    return f"{label}=contributors-{','.join(map(str, expected['ids']))}/scale-{expected['scale']:.9f}"


def run_verifier(path: Path, terminal: str) -> None:
    result = subprocess.run(["python3", str(path)], check=True, text=True, capture_output=True)
    require(terminal in result.stdout, f"nested verifier failed: {path}")


def main() -> None:
    run_verifier(ROUTE_VERIFIER, "variant_routes=OK")
    run_verifier(SELECTOR_VERIFIER, "reference_camera_family_selector=OK")
    print("variant_pipeline=OK " + " ".join(verify_case(label, expected) for label, expected in CASES.items()))


if __name__ == "__main__":
    main()
