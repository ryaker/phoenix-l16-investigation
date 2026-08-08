#!/usr/bin/env python3
"""Validate the Opus IRAMP terminal consolidation run artifacts."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/codex_opus_iramp_terminal_validation"

TIERS = {
    "28mm": "L16_02130",
    "35mm": "L16_03041",
    "70mm": "L16_03434",
    "150mm": "L16_02285",
}

SITES = {
    "0x365960": "entry_365960",
    "0x3661b0": "inner_3661b0",
    "0x36930f": "sentinel_cmp_36930f",
    "0x369e91": "tuple_score_store_369e91",
    "0x36a938": "reciprocal_36a938",
    "0x36aa57": "weighted_store_36aa57",
    "0x36e511": "score_mul_36e511",
}

EXPECTED_SCALE = {
    "28mm": 2.507692337036133,
    "35mm": 2.507692337036133,
    "70mm": 2.1384615898132324,
    "150mm": 2.1384615898132324,
}

EXPECTED_SENTINEL_PARTNER_COUNT = {
    "28mm": 1,
    "35mm": 1,
    "70mm": 1,
    "150mm": 3,
}

TOL = 1e-5


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def approx(left: float, right: float, tol: float = TOL) -> bool:
    return abs(float(left) - float(right)) <= tol


def finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def require_vec4(value: object, label: str) -> list[float]:
    require(isinstance(value, list) and len(value) == 4, f"{label}: expected vec4")
    require(all(finite(item) for item in value), f"{label}: non-finite vec4 {value}")
    return [float(item) for item in value]


def require_hdr_output(tier: str) -> None:
    hdr = RUN_ROOT / f"iramp_terminal_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    with hdr.open("rb") as handle:
        prefix = handle.read(10)
    require(prefix.startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def load_packet(tier: str) -> dict:
    path = RUN_ROOT / f"iramp_terminal_{tier}.json"
    require(path.exists(), f"{tier}: missing JSON report {path}")
    return json.loads(path.read_text())


def events_by_site(packet: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for event in packet.get("events", []):
        out[event.get("site_name")].append(event)
    return out


def validate_top_level(tier: str, packet: dict, by_site: dict[str, list[dict]]) -> None:
    require(TIERS[tier] in packet.get("label", ""), f"{tier}: label does not contain LRI id")
    require(packet.get("sample_cap_per_site") == 8, f"{tier}: unexpected sample cap")
    require(packet.get("errors") == [], f"{tier}: probe errors {packet.get('errors')}")
    process = packet.get("process") or {}
    require(process.get("exit_status") == 0, f"{tier}: process did not exit cleanly")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: hit drive step cap")
    require(len(packet.get("events", [])) == 8 * len(SITES), f"{tier}: unexpected event count")
    require_hdr_output(tier)

    sequences = [event.get("sequence") for event in packet.get("events", [])]
    require(sequences == list(range(1, len(sequences) + 1)), f"{tier}: sequence numbers not contiguous")

    disabled = set(packet.get("disabled_after_cap") or [])
    require(disabled == set(SITES), f"{tier}: disabled set mismatch {disabled}")
    for va, name in SITES.items():
        require(packet.get("counts", {}).get(va) == 8, f"{tier}: count mismatch for {va}")
        require(len(by_site.get(name, [])) == 8, f"{tier}: event count mismatch for {name}")
        hit_count = packet.get("breakpoint_hit_counts", {}).get(va)
        require(isinstance(hit_count, int) and hit_count >= 8, f"{tier}: bad hit count for {va}")
        for event in by_site[name]:
            require(event.get("site_va") == int(va, 16), f"{tier}: VA mismatch for {name}")


def validate_entry(tier: str, events: list[dict]) -> tuple[set[int], set[int]]:
    src1_values: set[int] = set()
    src2_values: set[int] = set()
    for event in events:
        packet = event["packet"]
        src1_values.add(packet["src1_rsi"])
        src2_values.add(packet["src2_rdx"])
        require(packet["src1_rsi"] and packet["src2_rdx"], f"{tier}: missing src pointer")
        require(approx(packet["scale_xmm0"], EXPECTED_SCALE[tier]), f"{tier}: scale mismatch")

        roi = packet["roi_r9_i32x4"]
        require(isinstance(roi, list) and len(roi) == 4, f"{tier}: bad ROI")
        require(roi[2] > roi[0] and roi[3] > roi[1], f"{tier}: non-positive ROI {roi}")

        source = packet["source_vector_rcx"]
        require(source["diff"] == 80, f"{tier}: source vector byte span")
        require(source["end"] - source["begin"] == 80, f"{tier}: source vector endpoints")
        require(source["count_0x10"] == 5, f"{tier}: source vector count_0x10")
        require(source["count_0x8"] == 10, f"{tier}: source vector count_0x8")

        warp = packet["warp_vector_r8"]
        require(warp["diff"] == 400, f"{tier}: warp vector byte span")
        require(warp["end"] - warp["begin"] == 400, f"{tier}: warp vector endpoints")
        require(warp["count_0x50"] == 5, f"{tier}: warp vector count_0x50")
        require(warp["count_0x10"] == 25, f"{tier}: warp vector count_0x10")

    require(len(src1_values) == 1, f"{tier}: changing src1 pointers")
    require(len(src2_values) == 1, f"{tier}: changing src2 pointers")
    return src1_values, src2_values


def validate_inner(tier: str, events: list[dict], src1_values: set[int], src2_values: set[int]) -> None:
    for event in events:
        packet = event["packet"]
        require(packet["closure_plus_0x08"] in src1_values, f"{tier}: closure src1 mismatch")
        require(packet["closure_plus_0x10"] in src2_values, f"{tier}: closure src2 mismatch")
        require(packet["closure_output_image_0x38"], f"{tier}: missing closure output image")
        roi = packet["roi_rsi_i32x4"]
        require(isinstance(roi, list) and len(roi) == 4, f"{tier}: bad inner ROI")
        require(roi[2] > roi[0] and roi[3] > roi[1], f"{tier}: non-positive inner ROI {roi}")


def validate_sentinel(tier: str, events: list[dict]) -> None:
    expected_count = EXPECTED_SENTINEL_PARTNER_COUNT[tier]
    for event in events:
        packet = event["packet"]
        require(packet["eax_u32_hex"] == "0x80000000", f"{tier}: non-sentinel compare sample")
        require(packet["is_0x80000000"] is True, f"{tier}: sentinel flag mismatch")
        require(packet["partner_count_0x280"] == expected_count, f"{tier}: partner count mismatch")
        require(packet["partner_diff"] == expected_count * 0x280, f"{tier}: partner span mismatch")
        require(packet["partner_end"] - packet["partner_begin"] == packet["partner_diff"], f"{tier}: partner endpoints")
        require(packet["rdx_contributor_byte_offset"] == packet["rcx_contributor_index"] * 0x280, f"{tier}: record byte offset mismatch")
        require(packet["r12_indexmap_base"], f"{tier}: missing index-map base")


def validate_score_mul(tier: str, events: list[dict]) -> None:
    for event in events:
        packet = event["packet"]
        x0 = float(packet["factor_xmm0"])
        x1 = float(packet["factor_xmm1"])
        product = float(packet["product"])
        sqrt_product = float(packet["sqrt_product"])
        require(0.0 <= x0 <= 1.000001, f"{tier}: factor_xmm0 outside expected range")
        require(0.0 <= x1 <= 1.000001, f"{tier}: factor_xmm1 outside expected range")
        require(approx(product, x0 * x1), f"{tier}: product mismatch")
        require(approx(sqrt_product, math.sqrt(product)), f"{tier}: sqrt mismatch")


def validate_tuple_store(tier: str, events: list[dict]) -> None:
    for event in events:
        packet = event["packet"]
        score = float(packet["score_xmm0"])
        base = int(packet["tuple_base_rcx"])
        index_times3 = int(packet["tuple_index_times3_rax"])
        require(0.0 <= score <= 1.000001, f"{tier}: tuple score outside expected range")
        require(index_times3 % 3 == 0, f"{tier}: tuple index is not a three-float stride")
        require(packet["tuple_score_store_addr"] == base + index_times3 * 4 + 0x8, f"{tier}: tuple score address mismatch")


def validate_reciprocal(tier: str, events: list[dict]) -> None:
    for event in events:
        packet = event["packet"]
        vec = require_vec4(packet["xmm2_before_rcpss"], f"{tier}: reciprocal xmm2")
        low = vec[0]
        require(low > 0.0, f"{tier}: reciprocal low lane is not positive")
        require(all(approx(item, low) for item in vec), f"{tier}: reciprocal packet lanes differ")
        require(approx(packet["predicted_exact_reciprocal_low"], 1.0 / low), f"{tier}: reciprocal prediction mismatch")


def validate_weighted_store(tier: str, events: list[dict]) -> None:
    for event in events:
        packet = event["packet"]
        offset = int(packet["byte_offset_rdi"])
        base = int(packet["dest_base_rsi"])
        dest = int(packet["dest_addr_rsi_plus_rdi"])
        require(offset % 16 == 0, f"{tier}: weighted-store offset is not vec4 aligned")
        require(dest == base + offset, f"{tier}: weighted-store address mismatch")
        require_vec4(packet["dest_vec4_before_store"], f"{tier}: weighted-store dest before")
        result = require_vec4(packet["result_xmm1_before_store"], f"{tier}: weighted-store result")
        require(result[3] >= 0.0, f"{tier}: weighted-store lane 3 negative")


def validate_tier(tier: str) -> str:
    packet = load_packet(tier)
    by_site = events_by_site(packet)
    validate_top_level(tier, packet, by_site)
    src1_values, src2_values = validate_entry(tier, by_site["entry_365960"])
    validate_inner(tier, by_site["inner_3661b0"], src1_values, src2_values)
    validate_sentinel(tier, by_site["sentinel_cmp_36930f"])
    validate_score_mul(tier, by_site["score_mul_36e511"])
    validate_tuple_store(tier, by_site["tuple_score_store_369e91"])
    validate_reciprocal(tier, by_site["reciprocal_36a938"])
    validate_weighted_store(tier, by_site["weighted_store_36aa57"])

    return (
        f"{tier}: OK events=56 srcs=5 warps=5 "
        f"sentinel_partner_records={EXPECTED_SENTINEL_PARTNER_COUNT[tier]} "
        f"scale={EXPECTED_SCALE[tier]:.9f}"
    )


def main() -> None:
    for tier in TIERS:
        print(validate_tier(tier))


if __name__ == "__main__":
    main()
