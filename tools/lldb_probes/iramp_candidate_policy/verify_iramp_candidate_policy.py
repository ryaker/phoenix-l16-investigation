#!/usr/bin/env python3
"""Verify the exhaustive installed IRAMP candidate/sentinel policy."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from capstone import (
    CS_ARCH_X86,
    CS_GRP_JUMP,
    CS_MODE_64,
    CS_OP_IMM,
    Cs,
)


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
START = 0x3661B0
END = 0x36B920


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("iramp_candidate_static_helpers", STATIC_PATH)


def direct_target(instruction):
    if (
        instruction.group(CS_GRP_JUMP)
        and instruction.operands
        and instruction.operands[0].type == CS_OP_IMM
    ):
        return instruction.operands[0].imm
    return None


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    displacement = int.from_bytes(raw[1:], "little", signed=True)
    return va + 5 + displacement


def verify() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    body = STATIC.bytes_at(data, mapping, START, END - START)
    require(
        hashlib.sha256(body).hexdigest()
        == "43d4d2ae88be6e594e45fc156f9d83535e56a98c5a9d3725343a5b32161d35d1",
        "IRAMP body changed",
    )

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = list(decoder.disasm(body, START))
    require(instructions[-1].address < END, "IRAMP decode range")

    sentinel_values = {
        0x80000000,
        -0x80000000,
        0x8000000080000000,
        -0x7FFFFFFF80000000,
    }
    sentinel_immediates = {}
    for instruction in instructions:
        values = {
            operand.imm
            for operand in instruction.operands
            if operand.type == CS_OP_IMM and operand.imm in sentinel_values
        }
        if values:
            sentinel_immediates[instruction.address] = (
                instruction.mnemonic,
                instruction.op_str,
            )
    require(
        set(sentinel_immediates)
        == {0x366C0D, 0x366C2C, 0x366DA0, 0x36930F, 0x369ED0, 0x36A7AC},
        f"sentinel instruction census changed: {sentinel_immediates}",
    )

    incoming = {}
    for instruction in instructions:
        target = direct_target(instruction)
        if target is not None:
            incoming.setdefault(target, []).append(
                (instruction.address, instruction.mnemonic)
            )
    expected_incoming = {
        0x366DA0: [
            (0x366C90, "jne"),
            (0x366D27, "jae"),
            (0x366D30, "jb"),
            (0x366D39, "jae"),
            (0x366D42, "jb"),
        ],
        0x368B89: [
            (0x366B60, "jle"),
            (0x366E18, "jle"),
            (0x366E25, "je"),
            (0x366E3C, "jle"),
        ],
        0x369ED0: [
            (0x36969B, "jle"),
            (0x3696B4, "jge"),
            (0x3696C8, "jle"),
            (0x3696E8, "jge"),
        ],
        0x369F0B: [
            (0x36931B, "jmp"),
            (0x369EC4, "jmp"),
        ],
        0x36A910: [(0x36A7B3, "je")],
    }
    for target, expected in expected_incoming.items():
        require(incoming.get(target) == expected, f"incoming edges to 0x{target:x}")

    guards = {
        0x366C77: "413b4530",  # source x upper bound
        0x366C7E: "413b7534",  # source y upper bound
        0x366D24: "0f2ed9",  # projected coordinate upper bound
        0x366D29: "0f2e1df0de2600",  # projected coordinate lower bound -8
        0x366E08: "2b8d3cbcff",  # first bbox span
        0x366E1E: "4181ffffffff7f",  # at least one valid projected pair
        0x366E32: "4429f8",  # second bbox span
        0x36930F: "3d00000080",  # first per-point sentinel check
        0x369ED0: "48b80000008000000080",  # boundary-failure sentinel rewrite
        0x36A7AC: "813cfb00000080",  # downstream same-pair sentinel check
        0x36A84B: "0f289d00bdffff",  # continuous score reload
        0x36A855: "f30f580dc3d82300",  # t - 0.5
        0x36A860: "f30f5fc1",  # branchless max(0,t-0.5)
        0x36A878: "0f58c1",  # score multiplier vector
        0x36A8FE: "f30f58d3",  # denominator += t
    }
    for va, expected_hex in guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    require(call_target(data, mapping, 0x369E3F) == 0x36CDE0, "score call")

    score_use = [
        instruction
        for instruction in instructions
        if 0x36A84B <= instruction.address <= 0x36A8FE
    ]
    compare_mnemonics = {
        "comiss",
        "comisd",
        "ucomiss",
        "ucomisd",
    }
    require(
        not any(instruction.mnemonic in compare_mnemonics for instruction in score_use),
        "score threshold compare appeared",
    )

    return digest


def main() -> None:
    digest = verify()
    print(f"iramp_candidate_policy_static=OK libcp={digest}")
    print("sentinel_immediate_sites=6")
    print("projection_rejection_edges=5")
    print("record_rejection_edges=4")
    print("post_wta_boundary_rejection_edges=4")
    print("score_policy=continuous_branchless_no_threshold")
    print("iramp_candidate_policy=OK")


if __name__ == "__main__":
    main()
