#!/usr/bin/env python3
"""Verify the IRAMP forward RGB-to-I1/I2/I3 transform and its live roles."""

from __future__ import annotations

import importlib.util
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
TERMINAL_PATH = (
    ROOT
    / "tools/lldb_probes/codex_opus_iramp_terminal_validation"
    / "verify_iramp_terminal_consolidation.py"
)
RUNTIME_PATH = ROOT / "runs/g56_iramp_forward_ohta/forward_28mm.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("g56_static", STATIC_PATH)
TERMINAL = load_module("g56_terminal", TERMINAL_PATH)


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def decode(data: bytes, mapping, start: int, end: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return list(decoder.disasm(STATIC.bytes_at(data, mapping, start, end - start), start))


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    expected_calls = {
        0x36695A: 0x374AC0,  # materialize src2
        0x366F1C: 0x374AC0,  # materialize direct contributor
        0x3692C6: 0x36B920,  # prepare transformed src2 reference patch
    }
    for call_va, target in expected_calls.items():
        require(call_target(data, mapping, call_va) == target, f"call target at 0x{call_va:x}")

    expected_skeleton = [
        "movaps",
        "movaps",
        "shufps",
        "mulps",
        "movaps",
        "shufps",
        "mulps",
        "addps",
        "movaps",
        "shufps",
        "mulps",
        "addps",
        "blendps",
        "movaps",
    ]
    loop_ranges = {
        "direct_contributor": (0x367030, 0x367064),
        "src2_reference": (0x368D40, 0x368D74),
    }
    for role, (start, end) in loop_ranges.items():
        insns = decode(data, mapping, start, end)
        require([insn.mnemonic for insn in insns] == expected_skeleton, f"{role}: transform skeleton drift")
        shuffles = [insn.op_str for insn in insns if insn.mnemonic == "shufps"]
        require([item.rsplit(", ", 1)[-1] for item in shuffles] == ["0", "0x55", "0xaa"], f"{role}: channel selectors drift")
        blends = [insn.op_str for insn in insns if insn.mnemonic == "blendps"]
        require(len(blends) == 1 and blends[0].endswith("8"), f"{role}: lane-3 preservation drift")

    constant_guards = {
        # Forward columns: [1980,198c,1998], [1984,1990,199c], [1988,1994,19a0].
        0x366F48: "f30f100d3caa3000f30f100528aa30000f14c1f30f100d35aa3000660f14c1",
        0x366F67: "f30f101521aa3000f30f100d0daa30000f14caf30f10151aaa3000660f14ca",
        0x366F86: "f30f101d06aa3000f30f1015f2a930000f14d3f30f101dffa93000660f14d3",
        # Inverse rows use the same scalar table as the transpose.
        0x36AC7D: "f30f100d036d3000f30f7e05f36c3000660f14c1",
        0x36AC91: "f30f1015fb6c3000f30f7e0deb6c3000660f14ca",
        0x36ACA5: "f30f101df36c3000f30f7e15e36c3000660f14d3",
    }
    for va, expected_hex in constant_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"constant-load opcode drift at 0x{va:x}: {actual.hex()}")

    patch_insns = decode(data, mapping, 0x36B920, 0x36CDD2)
    lane_mix = {
        "shufps",
        "shufpd",
        "unpcklps",
        "unpckhps",
        "unpcklpd",
        "unpckhpd",
        "blendps",
        "blendpd",
    }
    found = [(insn.address, insn.mnemonic) for insn in patch_insns if insn.mnemonic in lane_mix]
    require(found == [], f"0x36b920 patch helper unexpectedly mixes channels: {found[:8]}")

    require(0x366F1C < 0x367030, "direct transform no longer follows materialization")
    require(0x36695A < 0x368D40 < 0x3692C6, "src2 transform/patch custody order drift")
    return digest


def bits(values: list[float]) -> list[str]:
    return [struct.pack("<f", value).hex() for value in values]


def verify_runtime() -> str:
    require(RUNTIME_PATH.exists(), f"missing runtime packet {RUNTIME_PATH}")
    payload = json.loads(RUNTIME_PATH.read_text())
    require(payload.get("label") == "Unit-1 28mm", "unexpected runtime label")
    packets = payload.get("packets") or {}
    require(set(packets) == {"direct_contributor", "src2_reference"}, "runtime role set mismatch")

    a = 0.5773500204086304
    b = 0.7071099877357483
    c = 0.40825000405311584
    d = 0.8165000081062317
    expected = {
        "column_r_xmm0": [a, b, c, 0.0],
        "column_g_xmm1": [a, 0.0, -d, 0.0],
        "column_b_xmm2": [a, -b, c, 0.0],
    }
    for role, packet in packets.items():
        require(packet.get("role") == role, f"{role}: packet role mismatch")
        for field, values in expected.items():
            require(bits(packet[field]) == bits(values), f"{role}: {field} coefficient drift")
        require(packet["output_bits"] == packet["predicted_bits"], f"{role}: float32 replay mismatch")

    # These decimal constants intentionally differ slightly from ideal irrational values.
    require(not math.isclose(a, 1.0 / math.sqrt(3.0), rel_tol=0.0, abs_tol=1e-8), "a was idealized")
    require(not math.isclose(b, 1.0 / math.sqrt(2.0), rel_tol=0.0, abs_tol=1e-8), "b was idealized")
    require(not math.isclose(c, 1.0 / math.sqrt(6.0), rel_tol=0.0, abs_tol=1e-8), "c was idealized")

    for tier in TERMINAL.TIERS:
        TERMINAL.validate_tier(tier)
    return payload["label"]


def main() -> None:
    digest = verify_static()
    label = verify_runtime()
    print(f"g56_static=OK libcp={digest}")
    print(f"g56_runtime=OK sample={label} roles=direct_contributor,src2_reference")
    print("forward=I1=a*(R+G+B),I2=b*(R-B),I3=c*R-d*G+c*B,lane3=unchanged")
    print("constants=a:0.5773500204086304,b:0.7071099877357483,c:0.40825000405311584,d:0.8165000081062317")
    print("patch_helper_0x36b920=no_cross_channel_mix")
    print("four_focal_iramp_liveness=OK tiers=28mm,35mm,70mm,150mm")
    print("g56_iramp_forward_ohta=OK")


if __name__ == "__main__":
    main()
