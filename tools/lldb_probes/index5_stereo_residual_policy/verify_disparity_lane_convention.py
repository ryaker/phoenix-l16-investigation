#!/usr/bin/env python3
"""Verify SGM hypothesis-lane direction against the reciprocal-depth lookup."""

from __future__ import annotations

import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
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


ROLES = load_module(
    "disparity_lane_roles",
    ROOT / "tools/lldb_probes/index5_sgm_recurrence_roles/verify_sgm_recurrence_roles.py",
)
LOOKUP = load_module(
    "disparity_lane_lookup",
    ROOT / "tools/lldb_probes/codex_index5_lookup_vector_public_origin/verify_lookup_vector_public_origin.py",
)


def words(raw_hex: str) -> list[int]:
    return list(struct.unpack("<8H", bytes.fromhex(raw_hex)))


def verify_tier(tier: str) -> tuple[int, set[tuple[int, int, int, int]]]:
    vector_path = ROOT / f"runs/codex_276860_payload_vector_formula/vector_formula_{tier}.json"
    packet = json.loads(vector_path.read_text())
    ROLES.VECTOR_VALIDATOR.validate_report(vector_path)

    lookup_report = LOOKUP.validate_packet(tier)
    lookup_values = LOOKUP.expected_reciprocal_ramp(lookup_report["count"])
    require(lookup_values[0] == 640000.0, f"{tier}: lookup does not start at far endpoint")
    require(lookup_values[-1] == 200.0, f"{tier}: lookup does not end at near endpoint")
    require(
        all(a > b for a, b in zip(lookup_values, lookup_values[1:])),
        f"{tier}: lookup is not strictly far-to-near by increasing index",
    )

    headers: set[tuple[int, int, int, int]] = set()
    for sample_index, sample in enumerate(packet["watchpoint_samples"]):
        ctx = sample["vector_context"]
        addresses = ctx["addresses"]
        memory = ctx["memory16_hex"]
        lower = words(memory["src0_rsi_plus_2rax"])
        higher = words(memory["src6_rdi_plus_2rdx"])

        require(
            addresses["src6_rdi_plus_2rdx"] - addresses["src0_rsi_plus_2rax"] == 4,
            f"{tier}:{sample_index}: neighbor pointers are not two u16 words apart",
        )
        require(lower[2:] == higher[:6], f"{tier}:{sample_index}: overlapping Line buf words differ")

        # With lower starting two words before higher, current is the eight
        # contiguous words between them: lower[1], then higher[0:7].
        current = [lower[1], *higher[:7]]
        shifted_lower = ROLES.VECTOR_VALIDATOR.psrld_16_as_words(lower)
        shifted_higher = ROLES.VECTOR_VALIDATOR.pslldq_2_as_words(higher)
        formula_blend = [shifted_lower[0], *shifted_higher[1:]]
        require(current == formula_blend, f"{tier}:{sample_index}: current-hypothesis splice")

        header = tuple(sample["watchpoint"]["record_header_u16"])
        require(len(header) == 4, f"{tier}:{sample_index}: record header")
        base, count, step, rounded = header
        require(step == 1, f"{tier}:{sample_index}: selected record step is not one")
        require(0 < count <= rounded and rounded % 8 == 0, f"{tier}:{sample_index}: record count")
        require(base + step * (count - 1) < len(lookup_values), f"{tier}:{sample_index}: lookup bounds")

        valid_depths = [lookup_values[base + step * lane] for lane in range(count)]
        require(
            all(a > b for a, b in zip(valid_depths, valid_depths[1:])),
            f"{tier}:{sample_index}: increasing record lane is not nearer",
        )
        headers.add(header)

    return len(packet["watchpoint_samples"]), headers


def main() -> None:
    digest = ROLES.verify_static()
    data = ROLES.STATIC.LIBCP.read_bytes()
    mapping = ROLES.STATIC.segments(data)
    guards = {
        0x2779B0: "8d0413",                  # logical lane offset = block + lane
        0x2779B5: "f30f6f0446",              # lower-neighbor vector
        0x2779BA: "f30f6f3457",              # higher-neighbor vector
        0x2779C3: "660f73ff02",              # higher shifted toward current
        0x2779CC: "660f72d510",              # lower shifted toward current
        0x2779D1: "660f3a0eeffe",            # exact current-vector blend
        0x277A16: "4883c208",                # next eight hypotheses
    }
    for va, expected_hex in guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = ROLES.STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    total = 0
    for tier in TIERS:
        samples, headers = verify_tier(tier)
        total += samples
        rendered_headers = ",".join(str(header) for header in sorted(headers))
        print(f"{tier}=OK samples={samples} headers={rendered_headers}")
    print(f"static_libcp={digest}")
    print(
        "disparity_lane_convention=OK samples="
        f"{total} lane_order=increasing_hypothesis_index "
        "lower_neighbor=farther higher_neighbor=nearer lookup=far_to_near"
    )


if __name__ == "__main__":
    main()
