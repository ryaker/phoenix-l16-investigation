#!/usr/bin/env python3
"""Verify scorer-family custody for supported focal/topology variants."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs/lri_firing_set_census"
CASES = {
    "28mm_tele_unit1": "b",
    "28mm_tele_unit2": "b",
    "74mm_wide_unit2": "a",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify(label: str, expected_family: str) -> str:
    packet = json.loads((RUNS / f"custody_{label}.json").read_text())
    require(packet.get("process", {}).get("exit_status") == 0, f"{label}: process exit")
    require(not packet.get("drive_hit_step_cap"), f"{label}: step cap")
    require(not packet.get("errors"), f"{label}: errors")
    counts = packet["counts"]
    other = "b" if expected_family == "a" else "a"
    require(counts[f"family_{expected_family}_wrapper_entry_2481a0" if expected_family == "a" else "family_b_wrapper_entry_248580"] == 4, f"{label}: selected wrapper")
    require(counts[f"family_{other}_wrapper_entry_2481a0" if other == "a" else "family_b_wrapper_entry_248580"] == 0, f"{label}: sibling wrapper")
    require(len(packet["gate_calls"]) == 4, f"{label}: gate calls")
    require(len(packet["shared_gate_matches"]) == 4, f"{label}: shared matches")
    records = set()
    for call in packet["gate_calls"]:
        require(call["family"] == expected_family, f"{label}: gate family")
        require(call["matches_active_output_vec"], f"{label}: vector continuity")
        vector = call["output_vec_at_gate_call"]
        require(vector["read_ok"] and vector["stride"] == 44, f"{label}: vector layout")
        records.add(vector["record_count"])
    require(len(records) == 1, f"{label}: unstable record count")
    hdr = RUNS / f"custody_{label}.hdr"
    require(hdr.read_bytes()[:16].startswith(b"#?RADIANCE"), f"{label}: HDR")
    return f"{label}=family-{expected_family}/records-{records.pop()}"


def main() -> int:
    print("variant_custody=OK " + " ".join(verify(*item) for item in CASES.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
