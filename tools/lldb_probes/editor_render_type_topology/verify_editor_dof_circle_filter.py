#!/usr/bin/env python3
"""Verify the installed uniform discrete-disk ImageCircleFilter formula."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path("/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib")
REPORT = ROOT / "runs/editor_render_type_topology/editor_dof_math_mode1_blur9_f2.json"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
BODY_HASHES = {
    (0xD0440, 0xD05A4): "0196e381c6f223b71de142f56becd7b2981b15274bf46fd9426978fe5bd48108",
    (0xD05B0, 0xD09AA): "ee7e955903f170245267763011fe87a8d93da9fdc4ceaae61a14e3e027869a68",
    (0xD09B0, 0xD0DAA): "629257cdfcc9425089526d126216d11beb4be9f7691ef681c8369e2106dcfde9",
    (0xD1010, 0xD15A9): "bb2c5134dd3e08e041f735bbb52c4c6233f796f681f32b5d633f1b8fd8de23aa",
    (0xD16B0, 0xD1BCA): "a95d992a4124a3ce797b81c6211056e9abbb1e0c7aa14054551de634340a5a2e",
    (0xD1BD0, 0xD1D34): "d6da7dc8f595323f60d44a012678b16c23839c2323ce6d7bac111a296981d48c",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def instruction(decoder: Cs, blob: bytes, va: int) -> tuple[str, str]:
    item = next(decoder.disasm(blob[va : va + 16], va))
    return item.mnemonic, item.op_str


def disk_kernel(radius: int) -> tuple[list[int], int]:
    halfwidths = [math.isqrt(radius * radius - dy * dy)
                  for dy in range(-radius, radius + 1)]
    return halfwidths, sum(2 * width + 1 for width in halfwidths)


def main() -> None:
    blob = LIBCP.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    for (start, end), expected in BODY_HASHES.items():
        actual = hashlib.sha256(blob[start:end]).hexdigest()
        require(actual == expected, f"body hash drift 0x{start:x}..0x{end:x}")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    expected_ops = {
        # vec4 builder: 2r+1 rows, floor(sqrt(r^2-dy^2)), point count, 1/count.
        0xD06C8: ("lea", "eax, [r15 + r15 + 1]"),
        0xD0742: ("imul", "edi, edi"),
        0xD0747: ("sub", "ebx, edi"),
        0xD0750: ("sqrtsd", "xmm0, xmm0"),
        0xD0754: ("cvttsd2si", "edi, xmm0"),
        0xD0758: ("mov", "dword ptr [rsi + rcx*4 - 4], edi"),
        0xD075C: ("lea", "edx, [rdx + rdi*2 + 1]"),
        0xD0792: ("cvtsi2ss", "xmm0, edx"),
        0xD07A1: ("divss", "xmm1, xmm0"),
        # Initial vec4 disk sum clamps both coordinates to input bounds.
        0xD04E9: ("cmovge", "r11d, r14d"),
        0xD04F3: ("cmovg", "r11d, edi"),
        0xD0518: ("cmovge", "edi, r13d"),
        0xD051E: ("cmovg", "edi, ebx"),
        0xD052B: ("addps", "xmm0, xmmword ptr [rsi + rdi]"),
        # Scalar builder is the same formula.
        0xD0AC8: ("lea", "eax, [r15 + r15 + 1]"),
        0xD0B42: ("imul", "edi, edi"),
        0xD0B50: ("sqrtsd", "xmm0, xmm0"),
        0xD0B54: ("cvttsd2si", "edi, xmm0"),
        0xD0B58: ("mov", "dword ptr [rsi + rcx*4 - 4], edi"),
        0xD0B5C: ("lea", "edx, [rdx + rdi*2 + 1]"),
        0xD0B92: ("cvtsi2ss", "xmm0, edx"),
        0xD0BA1: ("divss", "xmm1, xmm0"),
        # Initial scalar disk sum applies the same coordinate clamps.
        0xD1C77: ("cmovge", "r10d, r11d"),
        0xD1C7E: ("cmovg", "r10d, r14d"),
        0xD1C98: ("cmovge", "ecx, r12d"),
        0xD1C9E: ("cmovg", "ecx, ebx"),
        0xD1CA7: ("addss", "xmm0, dword ptr [rdi + rcx*4]"),
        # vec4/scalar workers multiply the clamped disk sum by that normalizer.
        0xD10E2: ("call", "0xd0440"),
        0xD10FB: ("mulps", "xmm1, xmm0"),
        0xD1180: ("mov", "ecx, dword ptr [r10 + rdx*4]"),
        0xD11D6: ("subps", "xmm1, xmmword ptr [rax + rsi]"),
        0xD11DA: ("addps", "xmm0, xmm1"),
        0xD120B: ("mulps", "xmm1, xmm0"),
        0xD177A: ("call", "0xd1bd0"),
        0xD178A: ("mulss", "xmm1, dword ptr [rax]"),
        0xD17F0: ("mov", "ecx, dword ptr [r11 + rdx*4]"),
        0xD183F: ("subss", "xmm1, dword ptr [rax + rcx*4]"),
        0xD1844: ("addss", "xmm0, xmm1"),
        0xD1859: ("mulss", "xmm1, xmm0"),
    }
    for va, expected in expected_ops.items():
        actual = instruction(decoder, blob, va)
        require(actual == expected, f"0x{va:x}: {actual} != {expected}")

    require(b"ImageCircleFilterINS_8vec4x32f" in blob, "missing vec4 RTTI")
    require(b"ImageCircleFilterIf" in blob, "missing float RTTI")

    report = json.loads(REPORT.read_text())
    require(report["circle_vec_calls"] == 2335, "vec4 call incidence drift")
    require(report["circle_float_calls"] == 375, "float call incidence drift")
    require((report["circle_vec_radius_min"], report["circle_vec_radius_max"]) == (1, 6),
            "vec4 radius incidence drift")
    require((report["circle_float_radius_min"], report["circle_float_radius_max"]) == (1, 7),
            "float radius incidence drift")

    kernels = {}
    for radius in range(1, 8):
        halfwidths, count = disk_kernel(radius)
        weight = struct.unpack("<f", struct.pack("<f", 1.0 / count))[0]
        kernels[radius] = {"halfwidths": halfwidths, "count": count,
                           "weight": weight,
                           "weight_bits": struct.pack("<f", weight).hex()}
    require([kernels[r]["count"] for r in range(1, 8)] ==
            [5, 13, 29, 49, 81, 113, 149], "disk point-count drift")

    print("static_circle_filter=OK vec4_and_float_builders_workers")
    print("runtime_circle_filter=OK vec4_calls=2335 radii=1..6 float_calls=375 radii=1..7")
    for radius, kernel in kernels.items():
        print(f"radius={radius} count={kernel['count']} halfwidths={kernel['halfwidths']} "
              f"weight={kernel['weight']:.17g} bits={kernel['weight_bits']}")


if __name__ == "__main__":
    main()
