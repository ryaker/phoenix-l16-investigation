#!/usr/bin/env python3
"""Validate the four-zoom 0x23faf0 record-chain LLDB reports."""

from __future__ import annotations

import importlib.util
import json
import struct
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/state_helper_23faf0_record_chain"
TIERS = ("28mm", "35mm", "70mm", "150mm")
SITES = ("after_264440", "after_23faf0", "after_node_field_writes", "after_node_a0_write")


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
    hdr = RUN_ROOT / f"record_chain_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def raw_f32(values: list[float]) -> list[int]:
    return [struct.unpack("<I", struct.pack("<f", float(value)))[0] for value in values]


def record_components(record: dict) -> dict[str, list[int]]:
    return {
        "k": raw_f32(record["f32_0x00x8"]) + [record["i32_0x20"] & 0xFFFFFFFF],
        "rotation": raw_f32(record["f32_0x30x8"]) + [record["i32_0x50"] & 0xFFFFFFFF],
        "translation": [value & 0xFFFFFFFF for value in record["i32_0x24_0x2c"]],
    }


def public_component_matches(tier: str, role_records: list[tuple[str, dict]]) -> Counter:
    public = AUDIT.public_intrinsics_compact_records(tier)
    out: Counter = Counter()
    for role, record in role_records:
        components = record_components(record)
        for cam_id, pub in public.items():
            expected = {
                "k": pub["k_matrix_raw"],
                "rotation": pub["rotation_raw"],
                "translation": pub["translation_raw"],
            }
            for name, actual in components.items():
                if actual == expected[name]:
                    out[(role, name, cam_id)] += 1
    return out


def format_counter(counter: Counter, role: str) -> str:
    parts = []
    for component in ("k", "rotation", "translation"):
        items = []
        for (counter_role, counter_component, cam_id), count in sorted(counter.items()):
            if counter_role == role and counter_component == component:
                items.append(f"{AUDIT.CAMERA_NAMES[cam_id]}x{count}")
        if items:
            parts.append(f"{component}:{','.join(items)}")
    return "|".join(parts) if parts else "none"


def calib_payloads(tier: str) -> list[bytes]:
    return [
        block["payload"]
        for block in AUDIT.scan_lri_blocks(AUDIT.TIERS[tier])
        if block["payload_size"] in AUDIT.CALIB_BLOCK_SIZES
    ]


def payload_contains_any(payloads: list[bytes], needle_hex: str | None) -> bool:
    if not needle_hex:
        return False
    needle = bytes.fromhex(needle_hex)
    return any(payload.find(needle) >= 0 for payload in payloads)


def validate_tier(tier: str) -> str:
    packet = load_json(RUN_ROOT / f"record_chain_{tier}.json")
    process = packet["process"]
    require(process["state"] == "exited", f"{tier}: process did not exit")
    require(process["exit_status"] == 0, f"{tier}: nonzero exit")
    require(not packet.get("errors"), f"{tier}: JSON errors {packet.get('errors')}")
    require(not packet.get("drive_hit_step_cap"), f"{tier}: hit step cap")
    require_hdr_output(tier)

    expected_counts = {f"0x{va:x}": 26 for va in (0x23CBAB, 0x23CBC1, 0x23CE5E, 0x23D025)}
    require(packet["counts"] == expected_counts, f"{tier}: count mismatch {packet['counts']}")
    require(packet["breakpoint_hit_counts"] == expected_counts, f"{tier}: breakpoint count mismatch")

    events = packet["events"]
    require(len(events) == 104, f"{tier}: event count mismatch")
    groups = [events[index : index + 4] for index in range(0, len(events), 4)]
    require(len(groups) == 26, f"{tier}: group count mismatch")

    role_records: list[tuple[str, dict]] = []
    raw_candidates = []
    component_raw_nonmatches = 0
    component_raw_total = 0
    public = AUDIT.public_intrinsics_compact_records(tier)
    public_component_values = {
        name: {tuple(pub[field]) for pub in public.values()}
        for name, field in (
            ("k", "k_matrix_raw"),
            ("rotation", "rotation_raw"),
            ("translation", "translation_raw"),
        )
    }

    for group_index, group in enumerate(groups):
        require(tuple(event["site_name"] for event in group) == SITES, f"{tier}: site order at group {group_index}")
        packets = [event["packet"] for event in group]
        local = packets[0]["local_i32_minus_0x2d0"]
        source_obj = packets[0]["source_object_ptr_minus_0x430"]
        require(all(packet["local_i32_minus_0x2d0"] == local for packet in packets), f"{tier}: local changed")
        require(all(packet["source_object_ptr_minus_0x430"] == source_obj for packet in packets), f"{tier}: source ptr changed")

        pre = packets[0]
        require("pre_call_23faf0_args" in pre, f"{tier}: missing pre-call args")
        require("pre_call_left_record_rbx_plus_0x20" in pre, f"{tier}: missing pre-call left record")
        args = pre["pre_call_23faf0_args"]
        left = pre["pre_call_left_record_rbx_plus_0x20"]
        right_pre = pre["helper_record_rbp_minus_0x420"]
        out_pre = pre["compose_output_rbp_minus_0x378"]
        right_post = packets[1]["helper_record_rbp_minus_0x420"]
        out_post = packets[1]["compose_output_rbp_minus_0x378"]

        require(args["left_rbx_plus_0x20"] == left["addr"], f"{tier}: pre-call left pointer mismatch")
        require(args["right_rbp_minus_0x420"] == right_pre["addr"], f"{tier}: pre-call right pointer mismatch")
        require(args["dst_rbp_minus_0x378"] == out_pre["addr"], f"{tier}: pre-call dst pointer mismatch")
        require(right_pre["raw_0x00_0xa4"] == right_post["raw_0x00_0xa4"], f"{tier}: right record changed")
        require(out_pre["raw_0x00_0xa4"] != out_post["raw_0x00_0xa4"], f"{tier}: output did not change")
        require(
            out_post["raw_0x00_0xa4"] == packets[2]["compose_output_rbp_minus_0x378"]["raw_0x00_0xa4"],
            f"{tier}: output changed before node field writes",
        )

        node = packets[2]["tree_node_rbx"]
        require(node["i32_0x20"] == local, f"{tier}: node local key mismatch")
        for offset, expected in (("f64_0x28x2", (0, 2)), ("f64_0x38x2", (2, 4)), ("f64_0x48x2", (4, 6)), ("f64_0x58x2", (6, 8))):
            lo, hi = expected
            actual = node[offset]
            source = out_post["f32_0x00x8"][lo:hi]
            require(all(abs(float(a) - float(b)) < 1e-5 for a, b in zip(actual, source)), f"{tier}: node {offset} mismatch")

        for role, record in (
            ("pre_left", left),
            ("right", right_pre),
            ("output_pre", out_pre),
            ("output_post", out_post),
        ):
            role_records.append((role, record))
            raw_candidates.append(record["raw_0x00_0xa4"])
            for name, values in record_components(record).items():
                component_raw_total += 1
                if tuple(values) not in public_component_values[name]:
                    component_raw_nonmatches += 1

    payloads = calib_payloads(tier)
    full_hits = [raw for raw in raw_candidates if payload_contains_any(payloads, raw)]
    require(not full_hits, f"{tier}: full source-record byte span found in LRI calibration blocks")

    matches = public_component_matches(tier, role_records)
    require(matches, f"{tier}: no public component matches")
    require(component_raw_nonmatches > 0, f"{tier}: all components matched public records unexpectedly")

    return (
        f"{tier}: OK groups=26 full_record_lri_hits=0/{len(raw_candidates)} "
        f"component_nonmatches={component_raw_nonmatches}/{component_raw_total} "
        f"pre_left={format_counter(matches, 'pre_left')} "
        f"right={format_counter(matches, 'right')} "
        f"output_post={format_counter(matches, 'output_post')}"
    )


def main() -> None:
    for tier in TIERS:
        print(validate_tier(tier))


if __name__ == "__main__":
    main()
