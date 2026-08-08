#!/usr/bin/env python3
"""Verify the local effect of the 0x218bc4 positive-coordinate guard."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
WINDOW_BEGIN = 0x218B77
WINDOW_END = 0x218CBE
WINDOW_SHA256 = "0fe5e4f6ee87a19218f9338dafb89427748bbb6f2b9776b1bd28747e94eee89b"

ANCHORS = {
    0x218B7A: ("xorps", "xmm0, xmm0"),
    0x218B7D: ("xor", "r9d, r9d"),
    0x218BA9: ("xor", "r10d, r10d"),
    0x218BAC: ("xorps", "xmm1, xmm1"),
    0x218BC0: ("ucomiss", "xmm0, dword ptr [rdx + rbx*8]"),
    0x218BC4: ("jae", "0x218cb8"),
    0x218BCA: ("movss", "xmm3, dword ptr [rdx + rbx*8 + 4]"),
    0x218BD0: ("ucomiss", "xmm3, xmm0"),
    0x218BD3: ("jbe", "0x218cb8"),
    0x218C6E: ("sqrtss", "xmm3, xmm4"),
    0x218C95: ("ucomiss", "xmm2, xmm9"),
    0x218C99: ("seta", "cl"),
    0x218CA0: ("minss", "xmm3, xmm2"),
    0x218CA4: ("addss", "xmm1, xmm3"),
    0x218CA8: ("movzx", "ecx, cl"),
    0x218CAB: ("add", "r10d, ecx"),
    0x218CAE: ("inc", "r9d"),
    0x218CB8: ("inc", "rbx"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    window = blob[WINDOW_BEGIN:WINDOW_END]
    require(len(window) == WINDOW_END - WINDOW_BEGIN, "short guard window")
    require(hashlib.sha256(window).hexdigest() == WINDOW_SHA256, "guard SHA-256 drift")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in disassembler.disasm(window, WINDOW_BEGIN)
    }
    for address, expected in ANCHORS.items():
        require(instructions.get(address) == expected, f"anchor drift at 0x{address:x}: {instructions.get(address)}")

    skipped_effect_sites = {
        0x218CA4: "score_sum_xmm1",
        0x218CAB: "over_threshold_count_r10d",
        0x218CAE: "positive_pair_count_r9d",
    }
    require(
        all(0x218BC4 < address < 0x218CB8 for address in skipped_effect_sites),
        "effect site escaped skip interval",
    )

    print(f"binary={args.libcp}")
    print(f"window=0x{WINDOW_BEGIN:x}..0x{WINDOW_END:x} sha256={WINDOW_SHA256}")
    print("guard=x<=0@0x218bc4 or y<=0@0x218bd3 -> 0x218cb8")
    print("skip_interval=0x218bca..0x218cb4")
    print("skipped_effects=score_sum_xmm1,over_threshold_count_r10d,positive_pair_count_r9d")


if __name__ == "__main__":
    main()
