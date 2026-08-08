#!/usr/bin/env python3
"""Verify the post-Solve triple-write formula in installed libcp bytes."""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import subprocess
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
WINDOW_BEGIN = 0x20D603
WINDOW_END = 0x20D746
WINDOW_SHA256 = "0435b52a251a08987e765033a8f561e3f0e81dc839747b80282d650fff24c592"
SOLVE_CALL = 0x20D611
REMOVE_PARAMETER_CALL = 0x20D741

ANCHORS = {
    0x20D603: ("mov", "rdi, qword ptr [rbx + 0x30]"),
    0x20D611: ("call", "0x555e58"),
    0x20D616: ("mov", "rdi, qword ptr [rbp - 0x2c8]"),
    0x20D61D: ("mov", "rax, qword ptr [rbp - 0x2d0]"),
    0x20D624: ("lea", "r8, [rdi + rax*4 + 0x10]"),
    0x20D629: ("lea", "r9, [rdi + rax*4 + 8]"),
    0x20D62E: ("lea", "rdx, [rdi + rax*4 + 0xc]"),
    0x20D633: ("mov", "rsi, qword ptr [rbx + 0x38]"),
    0x20D637: ("mov", "rcx, qword ptr [rbp - 0x2c0]"),
    0x20D690: ("movsd", "xmm3, qword ptr [rbp - 0xc8]"),
    0x20D698: ("cvtsd2ss", "xmm3, xmm3"),
    0x20D6A8: ("movss", "dword ptr [r9], xmm1"),
    0x20D6AD: ("movss", "dword ptr [rdx], xmm2"),
    0x20D6B1: ("movss", "dword ptr [r8], xmm0"),
    0x20D6B6: ("mov", "rdi, qword ptr [rbx + 0x20]"),
    0x20D6BA: ("mov", "rsi, qword ptr [rbx + 0x40]"),
    0x20D6BE: ("subss", "xmm1, dword ptr [rdi + 0x24]"),
    0x20D6C3: ("subss", "xmm2, dword ptr [rdi + 0x28]"),
    0x20D6C8: ("subss", "xmm0, dword ptr [rdi + 0x2c]"),
    0x20D729: ("movss", "dword ptr [r9], xmm3"),
    0x20D72E: ("movss", "dword ptr [rdx], xmm4"),
    0x20D732: ("movss", "dword ptr [r8], xmm0"),
    0x20D737: ("mov", "rdi, r14"),
    0x20D73A: ("lea", "rsi, [rbp - 0xc8]"),
    0x20D741: ("call", "0x555e7c"),
}

EXPECTED_IMPORTS = {
    0x555E58: "__ZN5ceres5SolveERKNS_6Solver7OptionsEPNS_7ProblemEPNS0_7SummaryE",
    0x555E7C: "__ZN5ceres7Problem20RemoveParameterBlockEPd",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rel32_target(blob: bytes, va: int) -> int:
    require(blob[va] == 0xE8, f"expected call at 0x{va:x}")
    displacement = struct.unpack_from("<i", blob, va + 1)[0]
    return va + 5 + displacement


def imported_stubs(libcp: Path) -> dict[int, str]:
    result = subprocess.run(
        ["otool", "-Iv", str(libcp)],
        check=True,
        capture_output=True,
        text=True,
    )
    pattern = re.compile(r"^0x([0-9a-fA-F]+)\s+\d+\s+(\S+)$")
    out: dict[int, str] = {}
    for line in result.stdout.splitlines():
        match = pattern.match(line.strip())
        if match:
            out[int(match.group(1), 16)] = match.group(2)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    window = blob[WINDOW_BEGIN:WINDOW_END]
    require(len(window) == WINDOW_END - WINDOW_BEGIN, "short post-solve window")
    require(hashlib.sha256(window).hexdigest() == WINDOW_SHA256, "post-solve SHA-256 drift")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in disassembler.disasm(window, WINDOW_BEGIN)
    }
    for address, expected in ANCHORS.items():
        require(instructions.get(address) == expected, f"anchor drift at 0x{address:x}: {instructions.get(address)}")

    solve = rel32_target(blob, SOLVE_CALL)
    remove = rel32_target(blob, REMOVE_PARAMETER_CALL)
    imports = imported_stubs(args.libcp)
    for target, symbol in EXPECTED_IMPORTS.items():
        require(imports.get(target) == symbol, f"import mismatch at 0x{target:x}")
    require(solve == 0x555E58, f"Solve target 0x{solve:x}")
    require(remove == 0x555E7C, f"RemoveParameterBlock target 0x{remove:x}")

    print(f"binary={args.libcp}")
    print(f"window=0x{WINDOW_BEGIN:x}..0x{WINDOW_END:x} sha256={WINDOW_SHA256}")
    print("triple_addr=[rbp-0x2c8]+4*[rbp-0x2d0]+8")
    print("stage1=mat3(context+0x38)*(source_xy,1)*f32(f64[rbp-0xc8])")
    print("stage2=mat3(context+0x40)*(stage1-(context+0x20)[0x24:0x30])")
    print(f"calls=0x{SOLVE_CALL:x}->0x{solve:x},0x{REMOVE_PARAMETER_CALL:x}->0x{remove:x}")


if __name__ == "__main__":
    main()
