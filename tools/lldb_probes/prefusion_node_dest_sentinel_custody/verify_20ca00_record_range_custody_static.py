#!/usr/bin/env python3
"""Verify solved-record ownership through the immediate parent range scan."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)

WINDOWS = {
    "parent_entry": (
        0x20BD60,
        0x20BD81,
        "b006ebb7fd90d3b134d4c92fb403a55aeab5bdf5b073074b9ee6d30aca774514",
    ),
    "capture_dispatch": (
        0x20C26A,
        0x20C330,
        "31f14420213bfeb28ccced87d87e148aa4958f837494afc18f4e0d33302a3828",
    ),
    "callback_owner": (
        0x20CA14,
        0x20CA3A,
        "b376faed4ff3c139d6508c41ea97ab25c588c10cde858b05fa508f71b5afdc89",
    ),
    "record_address": (
        0x20D1D0,
        0x20D2AF,
        "c0b561d3f8c660d4dd316492aa40d81d91913ac869e29a7ba66eb5f9c47eaf0b",
    ),
    "postsolve_writes": (
        0x20D616,
        0x20D737,
        "66766b4529bd10e674c120a9f101beee3c0b51783b3038e3c130b63d84059c95",
    ),
    "parent_scan": (
        0x20C330,
        0x20C4BA,
        "9bdcc9c3c8bbbc1e780087428cb6d7be8cf7c402b7b043ba9ad349681665d408",
    ),
}

ANCHORS = {
    0x20BD74: ("mov", "r15, rdi"),
    0x20C26A: ("mov", "rax, qword ptr [r15]"),
    0x20C26D: ("mov", "r12, qword ptr [rax]"),
    0x20C270: ("mov", "rbx, qword ptr [rax + 8]"),
    0x20C295: ("mov", "qword ptr [rax + 8], r15"),
    0x20C2F6: ("call", "0x5670"),
    0x20CA14: ("mov", "qword ptr [rbp - 0x2b8], rdi"),
    0x20CA2F: ("mov", "rax, qword ptr [rdi + 8]"),
    0x20CA33: ("mov", "qword ptr [rbp - 0x2a8], rax"),
    0x20D1D0: ("mov", "rax, qword ptr [rbp - 0x2a8]"),
    0x20D1D7: ("mov", "rax, qword ptr [rax]"),
    0x20D1DA: ("mov", "rsi, qword ptr [rax]"),
    0x20D1DD: ("lea", "rdi, [rcx + rcx*4]"),
    0x20D1E1: ("movss", "xmm0, dword ptr [rsi + rdi*4 + 0x10]"),
    0x20D214: ("mov", "qword ptr [rbp - 0x2d0], rdi"),
    0x20D21B: ("mov", "qword ptr [rbp - 0x2c8], rsi"),
    0x20D616: ("mov", "rdi, qword ptr [rbp - 0x2c8]"),
    0x20D61D: ("mov", "rax, qword ptr [rbp - 0x2d0]"),
    0x20D624: ("lea", "r8, [rdi + rax*4 + 0x10]"),
    0x20D629: ("lea", "r9, [rdi + rax*4 + 8]"),
    0x20D62E: ("lea", "rdx, [rdi + rax*4 + 0xc]"),
    0x20D690: ("movsd", "xmm3, qword ptr [rbp - 0xc8]"),
    0x20D698: ("cvtsd2ss", "xmm3, xmm3"),
    0x20D6A8: ("movss", "dword ptr [r9], xmm1"),
    0x20D6AD: ("movss", "dword ptr [rdx], xmm2"),
    0x20D6B1: ("movss", "dword ptr [r8], xmm0"),
    0x20D729: ("movss", "dword ptr [r9], xmm3"),
    0x20D72E: ("movss", "dword ptr [rdx], xmm4"),
    0x20D732: ("movss", "dword ptr [r8], xmm0"),
    0x20C330: ("mov", "rax, qword ptr [r15]"),
    0x20C333: ("mov", "rcx, qword ptr [rax]"),
    0x20C336: ("mov", "rdi, qword ptr [rax + 8]"),
    0x20C3B1: ("add", "rcx, 0x4c"),
    0x20C3E6: ("movss", "xmm2, dword ptr [rcx - 0x3c]"),
    0x20C3EB: ("insertps", "xmm2, dword ptr [rcx - 0x28], 0x10"),
    0x20C3F2: ("insertps", "xmm2, dword ptr [rcx - 0x14], 0x20"),
    0x20C3F9: ("insertps", "xmm2, dword ptr [rcx], 0x30"),
    0x20C42A: ("add", "rcx, 0x50"),
    0x20C490: ("movss", "xmm0, dword ptr [rbx + 0x10]"),
    0x20C49B: ("jae", "0x20c4a5"),
    0x20C4A5: ("add", "rbx, 0x14"),
    0x20C4AE: ("movss", "dword ptr [r15 + 0x78], xmm3"),
    0x20C4B4: ("movss", "dword ptr [r15 + 0x7c], xmm2"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions: dict[int, tuple[str, str]] = {}

    for name, (begin, end, expected_sha256) in WINDOWS.items():
        window = blob[begin:end]
        require(len(window) == end - begin, f"short {name} window")
        actual_sha256 = hashlib.sha256(window).hexdigest()
        require(actual_sha256 == expected_sha256, f"{name} SHA-256 drift")
        instructions.update(
            (instruction.address, (instruction.mnemonic, instruction.op_str))
            for instruction in disassembler.disasm(window, begin)
        )

    for address, expected in ANCHORS.items():
        require(
            instructions.get(address) == expected,
            f"anchor drift at 0x{address:x}: {instructions.get(address)}",
        )

    scalar_accesses = [
        (address, mnemonic, operands)
        for address, (mnemonic, operands) in instructions.items()
        if 0x20D616 <= address < 0x20D737 and "[rbp - 0xc8]" in operands
    ]
    require(
        scalar_accesses == [(0x20D690, "movsd", "xmm3, qword ptr [rbp - 0xc8]")],
        f"post-Solve scalar access drift: {scalar_accesses}",
    )

    print(f"binary={args.libcp}")
    for name, (begin, end, sha256) in WINDOWS.items():
        print(f"{name}=0x{begin:x}..0x{end:x} sha256={sha256}")
    print("owner=rdi@0x20bd74 -> callable+0x08 -> callback[rbp-0x2a8]")
    print("record_begin=**owner stride=0x14 selected_offset=5*index")
    print("postsolve_write=record[index]+0x08,+0x0c,+0x10")
    print("postsolve_scalar_window=read-only rbp-0xc8 before triple writes")
    print("parent_consumer=positive(record[*]+0x10) range -> owner+0x78,+0x7c")


if __name__ == "__main__":
    main()
