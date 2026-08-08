#!/usr/bin/env python3
"""Verify operational roles for the index-5 SGM recurrence operands."""

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
VECTOR_VALIDATOR_PATH = (
    ROOT
    / "tools/lldb_probes/codex_276860_payload_vector_formula"
    / "validate_vector_formula.py"
)
TERM_VALIDATOR_PATH = (
    ROOT
    / "tools/lldb_probes/codex_276860_xmm3_term_step"
    / "validate_xmm3_term_step.py"
)
VECTOR_ROOT = ROOT / "runs/codex_276860_payload_vector_formula"
TERM_ROOT = ROOT / "runs/codex_276860_xmm3_term_step"
TIERS = ("28mm", "35mm", "70mm", "150mm")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("index5_sgm_recurrence_static", STATIC_PATH)
VECTOR_VALIDATOR = load_module("index5_sgm_recurrence_vector", VECTOR_VALIDATOR_PATH)
TERM_VALIDATOR = load_module("index5_sgm_recurrence_term", TERM_VALIDATOR_PATH)


def u16x8(raw_hex: str) -> list[int]:
    raw = bytes.fromhex(raw_hex)
    require(len(raw) == 16, f"expected 16 bytes, got {len(raw)}")
    return [raw[index] | (raw[index + 1] << 8) for index in range(0, 16, 2)]


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    windows = {
        (0x26C8E0, 0x26CC17): "9ae389ee942df008e410421d14c25d9f884476463a0bcc731e41a33cfaf8ba93",
        (0x2730C0, 0x273AC3): "51f7d235aa1fda5a092900ef05497a3848a324c2d4b4bb0331c96d96a1984e09",
        (0x276B72, 0x277A41): "f145d67c72d931faf8eb71297bb55b7ded254bc62fa80212ee35fbcc93731962",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")

    byte_guards = {
        0x26C929: "0fafc1",              # Line buf element count
        0x26C92F: "4b8d3c3f",            # Line buf byte count = 2 * elements
        0x26C9F7: "488d0443",            # Line buf midpoint
        0x26CA17: "428d04fd00000000",    # Min cost buf count = 8 * width
        0x26CAAD: "8d048500000000",      # Min cost buf midpoint = 4 * width
        0x276B72: "be40000000",          # 64-byte alignment for local-cost temp
        0x276B86: "4863b33c020000",      # hypothesis count
        0x277270: "660f38300438",         # Cost-volume bytes -> local u16 costs
        0x27786B: "0fb70c4f",            # Min cost buf baseline
        0x27791B: "01ca",                # baseline + adaptive P2
        0x2779D7: "660fddc1",            # adjacent path candidate + P1
        0x2779E9: "660f383af3",          # min with baseline + adaptive P2
        0x2779F4: "660fddc6",            # local cost + selected path term
        0x2779F8: "660fd9c2",            # subtract Min cost buf baseline
        0x2779FC: "f30f7f0451",          # current Line buf path-cost store
        0x277A10: "f3410f7f2c",          # Cost-volume payload accumulation
        0x277A3D: "6689044a",            # current Min cost buf store
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")
    return digest


def verify_term(tier: str) -> tuple[int, int, int]:
    path = TERM_ROOT / f"xmm3_term_step_{tier}.json"
    require(path.exists(), f"missing {path}")
    report = TERM_VALIDATOR.validate_report(path)
    packet = report["packet"]
    baseline = packet["table"]["table_load"]["table_value_u16"]
    adaptive_p2 = packet["preadd_int"]["registers"]["rdx"] & 0xFFFFFFFF
    cap = packet["postadd_scalar"]["registers"]["rdx"] & 0xFFFFFFFF
    require(cap == baseline + adaptive_p2, f"{tier}: cap relationship")
    require(
        u16x8(packet["broadcast_ready"]["xmm_hex"]["xmm2"]) == [baseline] * 8,
        f"{tier}: baseline broadcast",
    )
    require(
        u16x8(packet["broadcast_ready"]["xmm_hex"]["xmm3"]) == [cap] * 8,
        f"{tier}: cap broadcast",
    )
    return baseline, adaptive_p2, cap


def verify_vector(tier: str) -> tuple[int, int]:
    path = VECTOR_ROOT / f"vector_formula_{tier}.json"
    require(path.exists(), f"missing {path}")
    report = VECTOR_VALIDATOR.validate_report(path)
    samples = report["watchpoint_samples"]
    local_cost_matches = 0
    for index, sample in enumerate(samples):
        ctx = sample["vector_context"]
        origin = ctx["origin_context"]
        obj = origin["object_fields"]
        qwords = obj["qwords"]
        dwords = obj["dwords"]
        addresses = ctx["addresses"]

        line_base = qwords["0x168"]
        line_midpoint = qwords["0x180"]
        line_end = line_base + 2 * (line_midpoint - line_base)
        require(line_base < line_midpoint < line_end, f"{tier}:{index}: Line buf layout")
        for key in (
            "src0_rsi_plus_2rax",
            "src6_rdi_plus_2rdx",
            "side_rcx_plus_2rdx",
        ):
            address = addresses[key]
            require(
                line_base <= address and address + 16 <= line_end,
                f"{tier}:{index}: {key} outside Line buf",
            )

        min_base = qwords["0x198"]
        min_midpoint = qwords["0x1b0"]
        min_end = min_base + 2 * (min_midpoint - min_base)
        expected_min_midpoint = min_base + 8 * (dwords["0x130"] + 2)
        require(
            min_midpoint == expected_min_midpoint,
            f"{tier}:{index}: Min cost buf midpoint",
        )
        require(min_base < min_midpoint < min_end, f"{tier}:{index}: Min cost buf layout")

        temp_base = origin["stack_qwords"]["rbp_minus_0x2e0"]
        temp_end = temp_base + 2 * dwords["0x23c"]
        temp_address = addresses["accum_r10_plus_2rdx"]
        require(
            temp_base <= temp_address and temp_address + 16 <= temp_end,
            f"{tier}:{index}: local-cost temporary bounds",
        )

        if (
            ctx["memory16_hex"]["accum_r10_plus_2rdx"]
            == ctx["payload16_before_hit_hex"]
        ):
            local_cost_matches += 1

    require(local_cost_matches >= 1, f"{tier}: no initial local-cost/payload match")
    return len(samples), local_cost_matches


def main() -> None:
    digest = verify_static()
    print(f"static_index5_sgm_recurrence_roles=OK libcp={digest}")
    for tier in TIERS:
        baseline, adaptive_p2, cap = verify_term(tier)
        samples, local_cost_matches = verify_vector(tier)
        print(
            f"{tier}: OK baseline={baseline} adaptive_P2={adaptive_p2} cap={cap} "
            f"vector_samples={samples} initial_local_cost_matches={local_cost_matches}"
        )
    print(
        "roles=Line_buf_predecessor_candidates+P1; "
        "cap=Min_cost_buf_baseline+adaptive_P2; "
        "local_cost=temp; output=Line_buf+Cost_volume+Min_cost_buf"
    )
    print("index5_sgm_recurrence_roles=OK")


if __name__ == "__main__":
    main()
