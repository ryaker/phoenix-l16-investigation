#!/usr/bin/env python3
"""Validate state+0x448 payload-copy reports against public calibration indexes."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/state_448_payload_public_origin"
TIERS = ("28mm", "35mm", "70mm", "150mm")
SITE_ORDER = (
    "first_payload_0x00_0x20_call_241590",
    "first_payload_0x24_0x2c_call_2415b0",
    "later_payload_0x30_0x34_call_2415d0",
    "later_payload_0x38_0x3c_call_2415f0",
)

EXPECTED_FIRST_KEYS = {
    "28mm": list(range(0, 10)),
    "35mm": list(range(0, 10)),
    "70mm": list(range(5, 15)),
    "150mm": list(range(5, 15)),
}

EXPECTED_LATER_KEYS = {
    "28mm": list(range(0, 5)),
    "35mm": list(range(0, 5)),
    "70mm": list(range(5, 10)),
    "150mm": list(range(5, 10)),
}

EXPECTED_ANCHOR = {
    "28mm": "A1",
    "35mm": "A1",
    "70mm": "B4",
    "150mm": "B4",
}


def load_audit_module():
    path = ROOT / "tools/lane_b_index5_public_meaning_audit.py"
    spec = importlib.util.spec_from_file_location("lane_b_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_audit_module()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier: str) -> None:
    hdr = RUN_ROOT / f"state_448_payload_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _compact_component_matches(tier: str, words: tuple[int, ...]) -> list[str]:
    public = AUDIT.public_intrinsics_compact_records(tier)
    out = []
    for cam_id, record in public.items():
        for name, field in (
            ("k", "k_matrix_raw"),
            ("rotation", "rotation_raw"),
            ("translation", "translation_raw"),
        ):
            if tuple(record[field]) == words:
                out.append(f"{name}:{AUDIT.CAMERA_NAMES[cam_id]}")
    return out


def _format_counter(counter: Counter) -> str:
    if not counter:
        return "none"
    return ",".join(f"{key}x{count}" for key, count in sorted(counter.items()))


def validate_tier(tier: str) -> str:
    packet = load_json(RUN_ROOT / f"state_448_payload_{tier}.json")
    process = packet["process"]
    require(process["state"] == "exited", f"{tier}: process did not exit")
    require(process["exit_status"] == 0, f"{tier}: nonzero exit")
    require(not packet.get("errors"), f"{tier}: JSON errors {packet.get('errors')}")
    require(not packet.get("drive_hit_step_cap"), f"{tier}: hit step cap")
    require_hdr_output(tier)
    require(packet["events"], f"{tier}: no captured events")
    require(packet["breakpoint_hit_counts"] == packet["counts"], f"{tier}: hit-count mismatch")

    fixed32_sequence_index = AUDIT.public_calibration_fixed32_sequence_index(tier)
    events_by_site: dict[str, list[dict]] = defaultdict(list)
    public_sequence_matches: Counter = Counter()
    compact_component_matches: Counter = Counter()
    unique_keys_by_site: dict[str, set[int]] = defaultdict(set)

    for event in packet["events"]:
        site = event["site_name"]
        require(site in SITE_ORDER, f"{tier}: unexpected site {site}")
        packet_body = event["packet"]
        words = packet_body["source_words_u32"]
        require(words, f"{tier}: missing source words for {site}")
        words_tuple = tuple(int(word) & 0xFFFFFFFF for word in words)
        key = packet_body["node_key_from_payload_minus_0x04"]
        require(key is not None, f"{tier}: missing node key for {site}")
        unique_keys_by_site[site].add(int(key))
        events_by_site[site].append(event)
        if words_tuple in fixed32_sequence_index:
            public_sequence_matches[site] += 1
        for match in _compact_component_matches(tier, words_tuple):
            compact_component_matches[(site, match)] += 1

    for site in SITE_ORDER:
        require(events_by_site[site], f"{tier}: missing site {site}")

    first_keys = unique_keys_by_site[SITE_ORDER[0]]
    second_keys = unique_keys_by_site[SITE_ORDER[1]]
    require(first_keys == second_keys, f"{tier}: first insertion key sets differ")
    require(
        sorted(first_keys) == EXPECTED_FIRST_KEYS[tier],
        f"{tier}: first insertion key set {sorted(first_keys)} != {EXPECTED_FIRST_KEYS[tier]}",
    )
    for site in SITE_ORDER[2:]:
        require(
            sorted(unique_keys_by_site[site]) == EXPECTED_LATER_KEYS[tier],
            f"{tier}: later write key set for {site} != {EXPECTED_LATER_KEYS[tier]}",
        )

    first_total = len(events_by_site[SITE_ORDER[0]])
    second_total = len(events_by_site[SITE_ORDER[1]])
    require(public_sequence_matches[SITE_ORDER[0]] == first_total, f"{tier}: first record public seq count")
    require(public_sequence_matches[SITE_ORDER[1]] == second_total, f"{tier}: first triple public seq count")
    for site in SITE_ORDER[2:]:
        require(public_sequence_matches[site] == 0, f"{tier}: later pair unexpectedly exact public seq")
    require(
        compact_component_matches[(SITE_ORDER[0], f"rotation:{EXPECTED_ANCHOR[tier]}")] == first_total,
        f"{tier}: first record public rotation anchor mismatch",
    )
    require(
        compact_component_matches[(SITE_ORDER[1], f"translation:{EXPECTED_ANCHOR[tier]}")] == second_total,
        f"{tier}: first triple public translation anchor mismatch",
    )

    site_parts = []
    for site in SITE_ORDER:
        total = len(events_by_site[site])
        keys = ",".join(AUDIT.CAMERA_NAMES.get(key, str(key)) for key in sorted(unique_keys_by_site[site]))
        seq_hits = public_sequence_matches[site]
        component_counter = Counter(
            {
                match: count
                for (counter_site, match), count in compact_component_matches.items()
                if counter_site == site
            }
        )
        site_parts.append(
            f"{site}:events={total}:keys={keys}:public_seq={seq_hits}/{total}:components={_format_counter(component_counter)}"
        )

    return f"{tier}: OK; " + "; ".join(site_parts)


def main() -> None:
    for tier in TIERS:
        print(validate_tier(tier))


if __name__ == "__main__":
    main()
