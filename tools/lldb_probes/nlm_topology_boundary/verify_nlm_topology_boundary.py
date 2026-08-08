#!/usr/bin/env python3
"""Verify installed PatchNLM<4> scheduling, overlap-add, and boundary policy."""

from __future__ import annotations

import hashlib
import importlib.util
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("nlm_static_helper", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


def instructions(data: bytes, mapping, start: int, end: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return list(decoder.disasm(static.bytes_at(data, mapping, start, end - start), start))


def at(items, address: int, mnemonic: str, operand_fragment: str = ""):
    matches = [item for item in items if item.address == address]
    require(len(matches) == 1, f"missing instruction at 0x{address:x}")
    item = matches[0]
    require(item.mnemonic == mnemonic, f"0x{address:x}: {item.mnemonic} != {mnemonic}")
    require(operand_fragment in item.op_str, f"0x{address:x}: missing {operand_fragment!r} in {item.op_str!r}")
    return item


def phase_prefix(step: int, pair_count: int):
    state = 0x330E
    result = []
    for _ in range(pair_count):
        pair = []
        for _ in range(2):
            state = (0x5DEECE66D * state + 0xB) & ((1 << 48) - 1)
            pair.append(((state >> 16) & 0xFFFFFFFF) % step)
        result.append(tuple(pair))
    return result


def verify_static() -> None:
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == static.LIBCP_SHA256, f"libcp digest changed: {digest}")

    hashes = {
        (0x3066D0, 0x306D40): "bfebe7619117a2db022e28894a2dbc2456fe8f2d255306939a508675d91b3da8",
        (0x1A3C0, 0x1A73B): "9f65748b5293f8c1c02c5e77c2e4d6eb7d6290e6467050cf7800da5e2b0f4ff3",
        (0x18F960, 0x18FCEA): "d950649d44164d3a6c36e1891bc1203e87e4c72887e76b1d9c67413e9e8fed74",
        (0x306717, 0x306817): "d3865d159e3bd6cc0af4bedd7b4a884314dd625292e0182f26caf3cd73e01893",
        (0x30689C, 0x306A16): "153e933278459dcaa37efb8755646294a9b8a899690a11f0d2ce43fa7eb1900a",
        (0x3070E0, 0x307D90): "862f185f5d4cd3d365ebf5ff65091520b2697cdd9d83a1e8bf4c42a4b2a5ddbb",
        (0x307D90, 0x307EA7): "1415cf342baae4666c4a15d84d99acb004eff16de46a3c71dd042643de8d5cab",
    }
    for (start, end), expected in hashes.items():
        actual = hashlib.sha256(static.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed: {actual}")

    seed = static.bytes_at(data, mapping, 0x5A8A60, 16)
    require(seed == struct.pack("<4f", *([0.01] * 4)), "PatchNLM seed constant changed")

    parent = instructions(data, mapping, 0x306717, 0x306C39)
    at(parent, 0x306733, "mov", "0x3109")
    at(parent, 0x306754, "mov", "0x330e")
    at(parent, 0x306764, "imul", "0xe66d")
    at(parent, 0x30677E, "imul", "0xdeec")
    at(parent, 0x3067B5, "div", "r14d")
    at(parent, 0x306806, "mov", "byte ptr [r9 + 1]")
    at(parent, 0x3068BB, "call", "0x1a3c0")
    at(parent, 0x30693C, "call", "0x18f960")
    at(parent, 0x306953, "mov", "[rbp - 0x188], 2")
    at(parent, 0x30695D, "mov", "[rbp - 0x184], 2")
    at(parent, 0x306967, "dec", "eax")
    at(parent, 0x306969, "dec", "ecx")
    at(parent, 0x306981, "movabs", "0x8000000080")
    at(parent, 0x306A11, "call", "0x5440")
    at(parent, 0x306A3B, "mov", "[rbp - 0x174], 1")
    at(parent, 0x306ACA, "call", "0x5440")
    at(parent, 0x306AF0, "mov", "[rbp - 0x174], 2")
    at(parent, 0x306B7F, "call", "0x5440")
    at(parent, 0x306BA5, "mov", "[rbp - 0x174], 3")
    at(parent, 0x306C34, "call", "0x5440")

    worker = instructions(data, mapping, 0x3070E0, 0x307D90)
    at(worker, 0x307121, "and", "1")
    at(worker, 0x307127, "and", "2")
    at(worker, 0x3071AB, "imul", "0xdeadbeef")
    at(worker, 0x307271, "movzx", "byte ptr [rcx + rdx*2]")
    at(worker, 0x307275, "movzx", "byte ptr [rcx + rdx*2 + 1]")
    at(worker, 0x3072D1, "lea", "[rsi - 2]")
    at(worker, 0x3072EB, "lea", "[rcx + r15 - 2]")
    at(worker, 0x3073DD, "sar", "1")
    at(worker, 0x3073E8, "cmp", "eax, 1")
    at(worker, 0x3073F0, "cmovle", "eax, esi")
    at(worker, 0x3073F9, "add", "eax, r8d")
    at(worker, 0x307403, "lea", "[r9 - 1]")
    at(worker, 0x307415, "cmp", "edi, r11d")
    at(worker, 0x307493, "mov", "ecx, eax")
    at(worker, 0x307495, "sub", "ecx, r8d")
    at(worker, 0x3074A4, "mov", "r15d, ecx")
    at(worker, 0x3074A7, "sub", "r15d, r8d")
    at(worker, 0x307640, "mov", "r9d, r15d")
    at(worker, 0x307643, "and", "r9d, 1")
    at(worker, 0x307647, "add", "[rbp - 0x2a0]")
    at(worker, 0x307690, "mov", "[rbp - 0x2b8]")
    at(worker, 0x307697, "imul", "edi, ebx")
    at(worker, 0x30769A, "mov", "[rbp - 0x2b0]")
    at(worker, 0x3076A1, "add", "edi, ebx")
    at(worker, 0x3076A6, "mov", "[rsi + 0x20]")
    at(worker, 0x3076AE, "movaps", "[rsi + rdi]")
    at(worker, 0x3076B2, "mulps", "[rbp - 0x2e0]")
    at(worker, 0x307700, "movaps", "[rdi - 0x20]")
    at(worker, 0x30774B, "add", "r12, 0x40")
    at(worker, 0x307752, "cmp", "r12d, 0x100")
    at(worker, 0x3077C6, "addps", "[rbp - 0x200]")
    at(worker, 0x3078C7, "add", "r9d, 2")
    at(worker, 0x3078CB, "add", "rdx, 2")
    at(worker, 0x3079F5, "inc", "r15d")
    at(worker, 0x307A96, "mov", "[rbp - 0x300]")
    at(worker, 0x307B87, "movaps", "[rax + rcx + 0x30]")
    at(worker, 0x307B93, "mov", "[rdi + 0x40]")
    at(worker, 0x307C82, "movaps", "[rax + rcx + 0x30]")

    numerator_stores = [
        item for item in worker
        if 0x307ABF <= item.address <= 0x307B87
        and item.mnemonic == "movaps"
        and "xmmword ptr [" in item.op_str.split(",", 1)[0]
    ]
    denominator_stores = [
        item for item in worker
        if 0x307BAB <= item.address <= 0x307C82
        and item.mnemonic == "movaps"
        and "xmmword ptr [" in item.op_str.split(",", 1)[0]
    ]
    require(len(numerator_stores) == 16, f"numerator store count changed: {len(numerator_stores)}")
    require(len(denominator_stores) == 16, f"denominator store count changed: {len(denominator_stores)}")

    normalizer = instructions(data, mapping, 0x307D90, 0x307EA7)
    require(sum(item.mnemonic == "rcpps" for item in normalizer) == 3, "normalizer rcpps count changed")
    require(sum(item.mnemonic == "blendps" and item.op_str.endswith(", 8") for item in normalizer) == 3,
            "normalizer lane-3 preserve count changed")

    prefix = phase_prefix(2, 8)
    expected_prefix = [(0, 1), (1, 0), (1, 1), (1, 1), (1, 0), (0, 1), (1, 0), (0, 0)]
    require(prefix == expected_prefix, f"phase replay changed: {prefix}")
    print(
        "static_nlm_topology_boundary=OK "
        f"libcp={digest} phase_pairs=12553 phase_prefix={prefix} "
        "region=[2,width-1)x[2,height-1) tile=128x128 modes=4 patch=4x4 window=5 "
        "reference_step=2 candidate_checkerboard_step=2 threshold=reference_center "
        "numerator_stores=16 denominator_stores=16"
    )


if __name__ == "__main__":
    verify_static()
