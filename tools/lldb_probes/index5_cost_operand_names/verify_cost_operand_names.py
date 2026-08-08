#!/usr/bin/env python3
"""Verify installed names for sampled index-5 Cost-volume worker operands."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
OPERAND_ROOT = ROOT / "runs/codex_276860_operand_source_context"
VECTOR_ROOT = ROOT / "runs/codex_276860_payload_vector_formula"
GEOMETRY_ROOT = ROOT / "runs/index5_composed_geometry_origin"
TIERS = ("28mm", "35mm", "70mm", "150mm")
EXPECTED_FIRST_KEYS = {"28mm": 0, "35mm": 0, "70mm": 8, "150mm": 8}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("index5_cost_operand_static", STATIC_PATH)


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    windows = {
        (0x26C480, 0x26C8E0): "35414961beb4f0bdf978214ed3ba653b980d84b5b81d3fa44e159ecf8898fe3e",
        (0x26C8E0, 0x26CC17): "9ae389ee942df008e410421d14c25d9f884476463a0bcc731e41a33cfaf8ba93",
        (0x276A80, 0x277A20): "4a02829b667e6413955248aec0f65c85fa8a9aeb7cccf266b841cf9aab1f4ce9",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")
    return digest


def producer_sample(report: dict, site: str) -> dict:
    samples = [sample for sample in report["producer_samples"] if sample["site"] == site]
    require(len(samples) == 1, f"{report['label']}: expected one {site}")
    return samples[0]


def geometry_first_key(tier: str) -> int:
    report = json.loads((GEOMETRY_ROOT / f"composed_geometry_{tier}.json").read_text())
    keys = [
        event["packet"]["camera_key"]
        for event in report["events"]
        if event["site_name"] == "after_23faf0_compose"
    ]
    require(len(keys) == 5, f"{tier}: geometry keys")
    return keys[0]


def verify_tier(tier: str) -> str:
    operand = json.loads((OPERAND_ROOT / f"operand_source_{tier}.json").read_text())
    require(operand["process"]["state"] == "exited", f"{tier}: operand process")
    require(operand["capture_complete"], f"{tier}: operand capture incomplete")
    require(operand["terminated_after_capture"], f"{tier}: operand termination scope")
    require(not operand["errors"], f"{tier}: operand errors")
    require(not operand["drive_hit_step_cap"], f"{tier}: operand step cap")
    require(operand["target_index"] == 5, f"{tier}: operand target index")
    require(
        operand["counts"]["guide_store_0x288_reuse_26c633"] == 1,
        f"{tier}: Guidance reuse count",
    )

    target = operand["target_object"]
    guide = producer_sample(operand, "guide_store_0x288_reuse_26c633")
    require(guide["kind"] == "reused_guide_descriptor", f"{tier}: Guidance producer kind")
    require(guide["write_object"] == target, f"{tier}: Guidance target")
    require(guide["field_offset"] == 0x288, f"{tier}: Guidance offset")
    require(guide["write_value_descriptor_like"]["read_ok"], f"{tier}: Guidance descriptor")
    require(
        guide["write_value_descriptor_like"]["u32_0x10_0x1c"] == [2080, 1560, 2080, 1560],
        f"{tier}: Guidance dimensions",
    )

    table = operand["packet"]["table"]
    context = table["operand_sources"]["xmm8_latest_load"]["target_stack_context"]
    fields = context["object_fields"]
    qwords = fields["qwords"]
    stack = context["stack_qwords"]
    require(context["object_from_stack_rbp_minus_0x1c8"] == target, f"{tier}: worker target")
    require(stack["rbp_minus_0x210"] == qwords["0x198"], f"{tier}: Min cost buf")
    require(stack["rbp_minus_0x208"] == qwords["0x1e8"], f"{tier}: Pixel buf base")
    require(stack["rbp_minus_0x250"] == qwords["0x200"], f"{tier}: Pixel buf midpoint")
    require(
        qwords["0x200"] - qwords["0x1e8"] == 33312,
        f"{tier}: Pixel buf midpoint delta",
    )
    matched_store = table["operand_sources"]["xmm8_latest_load"]["xmm8_vector_load"][
        "matched_store_sample"
    ]
    guide_bytes = matched_store["xmm8_vector_store"]["latest_guide_sample"][
        "guide_source"
    ]["source_u8x4_hex"]
    require(
        isinstance(guide_bytes, str) and len(guide_bytes) == 8,
        f"{tier}: missing Guidance byte sample",
    )

    vector = json.loads((VECTOR_ROOT / f"vector_formula_{tier}.json").read_text())
    require(vector["process"]["state"] == "exited", f"{tier}: vector process")
    require(vector["process"]["exit_status"] == 0, f"{tier}: vector exit")
    require(not vector["errors"], f"{tier}: vector errors")
    require(not vector["drive_hit_step_cap"], f"{tier}: vector step cap")
    require(vector["target_index"] == 5, f"{tier}: vector target index")
    require(vector["watchpoint_samples"], f"{tier}: no vector samples")
    stable = [
        sample["vector_context"]["origin_context"]["relationships"]
        for sample in vector["watchpoint_samples"]
    ]
    require(all(row["object_eq_target_object"] for row in stable), f"{tier}: vector target")
    require(
        all(row["stack_minus_0x200_eq_object_0x168"] for row in stable),
        f"{tier}: Line buf data pointer",
    )
    require(
        all(row["stack_minus_0x210_eq_object_0x198"] for row in stable),
        f"{tier}: Min cost buf data pointer",
    )

    first_key = geometry_first_key(tier)
    require(first_key == EXPECTED_FIRST_KEYS[tier], f"{tier}: tier anchor key")
    anchor = "A1" if first_key == 0 else "B4"
    return (
        f"{tier}: OK Guidance=first_Images_{anchor} "
        "Min_cost_buf=+0x198 Pixel_buf=+0x1e8/+0x200 "
        "Line_buf=+0x168"
    )


def main() -> None:
    digest = verify_static()
    print(f"static_index5_cost_operand_names=OK libcp={digest}")
    for tier in TIERS:
        print(verify_tier(tier))
    print("index5_cost_operand_names=OK")


if __name__ == "__main__":
    main()
