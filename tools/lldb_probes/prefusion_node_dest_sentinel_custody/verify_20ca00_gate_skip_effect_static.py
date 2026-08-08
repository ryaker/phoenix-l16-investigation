#!/usr/bin/env python3
"""Byte-verify the local effect skipped by the 0x20d363 sentinel branch."""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import subprocess
from pathlib import Path


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
SKIP_BRANCH = 0x20D363
SKIP_TARGET = 0x20D565
SKIPPED_BEGIN = 0x20D369
ADD_RESIDUAL_CALL = 0x20D560
SUMMARY_CTOR_CALL = 0x20D5F0
SOLVE_CALL = 0x20D611
WINDOW_BEGIN = 0x20D344
WINDOW_END = SKIP_TARGET
WINDOW_SHA256 = "59eb24308fab2f0598293aca8d394b6f77b36f6ffd6eb469806b7fecadfd3be4"

EXPECTED_STUBS = {
    0x555E58: "__ZN5ceres5SolveERKNS_6Solver7OptionsEPNS_7ProblemEPNS0_7SummaryE",
    0x555E5E: "__ZN5ceres6Solver7SummaryC1Ev",
    0x555E64: "__ZN5ceres7Problem16AddResidualBlockEPNS_12CostFunctionEPNS_12LossFunctionEPd",
}

BYTE_GUARDS = {
    0x20D344: "4584f60f8418020000",
    0x20D35E: "410f2e04c70f83fc010000",
    0x20D369: "488b8560fdfffff3410f1044c7040f2e05521f3a000f86e1010000",
    0x20D3E8: "bf30000000e8a68f3400",
    0x20D4A4: "0f5a01660f2900660f13401048c7402000000000660f174030",
    0x20D524: "410f5a04cf660f294050660f13406048c7407000000000660f178080000000",
    0x20D54E: "488b5728488dbd40ffffff488d8d38ffffffe8ff883400",
    0x20D565: "488bbd20ffffff4885ff7429",
    0x20D5E9: "488dbd68fdffffe869883400",
    0x20D603: "488b7b304c89f6488d9568fdffffe842883400",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_at(blob: bytes, va: int, size: int) -> bytes:
    require(0 <= va <= len(blob) - size, f"range outside binary: 0x{va:x}+0x{size:x}")
    return blob[va : va + size]


def rel32_target(blob: bytes, instruction_va: int, opcode: bytes) -> int:
    require(read_at(blob, instruction_va, len(opcode)) == opcode, f"opcode drift at 0x{instruction_va:x}")
    displacement = struct.unpack_from("<i", blob, instruction_va + len(opcode))[0]
    return instruction_va + len(opcode) + 4 + displacement


def imported_stubs(libcp: Path) -> dict[int, str]:
    result = subprocess.run(
        ["otool", "-Iv", str(libcp)],
        check=True,
        capture_output=True,
        text=True,
    )
    out: dict[int, str] = {}
    pattern = re.compile(r"^0x([0-9a-fA-F]+)\s+\d+\s+(\S+)$")
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
    for va, expected_hex in BYTE_GUARDS.items():
        expected = bytes.fromhex(expected_hex)
        require(read_at(blob, va, len(expected)) == expected, f"byte guard drift at 0x{va:x}")

    window = read_at(blob, WINDOW_BEGIN, WINDOW_END - WINDOW_BEGIN)
    require(hashlib.sha256(window).hexdigest() == WINDOW_SHA256, "skipped-window SHA-256 drift")

    x_skip = rel32_target(blob, SKIP_BRANCH, bytes.fromhex("0f83"))
    y_skip = rel32_target(blob, 0x20D37E, bytes.fromhex("0f86"))
    add_residual = rel32_target(blob, ADD_RESIDUAL_CALL, b"\xe8")
    summary_ctor = rel32_target(blob, SUMMARY_CTOR_CALL, b"\xe8")
    solve = rel32_target(blob, SOLVE_CALL, b"\xe8")
    require(x_skip == SKIP_TARGET, f"x gate target 0x{x_skip:x}")
    require(y_skip == SKIP_TARGET, f"y gate target 0x{y_skip:x}")
    require(SKIPPED_BEGIN < ADD_RESIDUAL_CALL < SKIP_TARGET, "residual call outside skipped interval")

    stubs = imported_stubs(args.libcp)
    for target, symbol in EXPECTED_STUBS.items():
        require(stubs.get(target) == symbol, f"import mismatch at 0x{target:x}: {stubs.get(target)!r}")
    require(add_residual == 0x555E64, f"AddResidualBlock target 0x{add_residual:x}")
    require(summary_ctor == 0x555E5E, f"Summary ctor target 0x{summary_ctor:x}")
    require(solve == 0x555E58, f"Solve target 0x{solve:x}")

    print(f"binary={args.libcp}")
    print(f"window=0x{WINDOW_BEGIN:x}..0x{WINDOW_END:x} sha256={WINDOW_SHA256}")
    print(f"x_gate=0x{SKIP_BRANCH:x}->0x{x_skip:x} y_gate=0x20d37e->0x{y_skip:x}")
    print(f"skipped_interval=0x{SKIPPED_BEGIN:x}..0x{SKIP_TARGET:x}")
    print(f"skipped_call=0x{ADD_RESIDUAL_CALL:x}->0x{add_residual:x} {stubs[add_residual]}")
    print(f"post_loop=0x{SUMMARY_CTOR_CALL:x}->0x{summary_ctor:x},0x{SOLVE_CALL:x}->0x{solve:x}")


if __name__ == "__main__":
    main()
