#!/usr/bin/env python3
"""Verify owner +0x78/+0x7c phase reuse around 0x20ada0 and 0x20bd60."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)

WINDOWS = {
    "state_body_22ae60": (
        0x22AE60,
        0x22AEA8,
        "0a8dacb37c3f85d410e739acd61a022779574fb58236d75d64c0d30d49191e99",
    ),
    "pre_solve_summary_20ada0": (
        0x20ADA0,
        0x20AF6E,
        "055143c7598f1fa61b9d58491161bf30974af36a040af77c41372101c240fe87",
    ),
    "post_solve_summary_20c330": (
        0x20C330,
        0x20C4BA,
        "9bdcc9c3c8bbbc1e780087428cb6d7be8cf7c402b7b043ba9ad349681665d408",
    ),
}

ANCHORS = {
    0x22AE66: ("mov", "rbx, qword ptr [rdi + 8]"),
    0x22AE6A: ("mov", "rdi, qword ptr [rbx + 0x10]"),
    0x22AE6E: ("call", "0x20ada0"),
    0x22AE83: ("mov", "rdi, qword ptr [rbx + 0x10]"),
    0x22AE87: ("call", "0x20bd60"),
    0x20ADB1: ("mov", "r15, rdi"),
    0x20AEE0: ("movss", "xmm3, dword ptr [rax + rdx*8]"),
    0x20AEE5: ("movss", "xmm2, dword ptr [rax + rdx*8 + 4]"),
    0x20AF2C: ("minss", "xmm0, xmm3"),
    0x20AF30: ("maxss", "xmm1, xmm2"),
    0x20AF40: ("movss", "xmm2, dword ptr [rip + 0x39d1e0]"),
    0x20AF4B: ("divss", "xmm3, xmm1"),
    0x20AF4F: ("divss", "xmm2, xmm0"),
    0x20AF53: ("movss", "dword ptr [r15 + 0x78], xmm3"),
    0x20AF59: ("movss", "dword ptr [r15 + 0x7c], xmm2"),
    0x20C330: ("mov", "rax, qword ptr [r15]"),
    0x20C360: ("movss", "xmm3, dword ptr [rip + 0x3c1d1c]"),
    0x20C368: ("movss", "xmm2, dword ptr [rip + 0x39bdb4]"),
    0x20C3E6: ("movss", "xmm2, dword ptr [rcx - 0x3c]"),
    0x20C490: ("movss", "xmm0, dword ptr [rbx + 0x10]"),
    0x20C49D: ("minss", "xmm3, xmm0"),
    0x20C4A1: ("maxss", "xmm2, xmm0"),
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

    state_calls = [
        address
        for address in (0x22AE6E, 0x22AE87)
        if instructions.get(address, ("", ""))[0] == "call"
    ]
    require(state_calls == [0x22AE6E, 0x22AE87], f"state call order drift: {state_calls}")

    owner_writes = [
        (address, mnemonic, operands)
        for address, (mnemonic, operands) in sorted(instructions.items())
        if mnemonic == "movss"
        and operands in {
            "dword ptr [r15 + 0x78], xmm3",
            "dword ptr [r15 + 0x7c], xmm2",
        }
    ]
    require(
        owner_writes
        == [
            (0x20AF53, "movss", "dword ptr [r15 + 0x78], xmm3"),
            (0x20AF59, "movss", "dword ptr [r15 + 0x7c], xmm2"),
            (0x20C4AE, "movss", "dword ptr [r15 + 0x78], xmm3"),
            (0x20C4B4, "movss", "dword ptr [r15 + 0x7c], xmm2"),
        ],
        f"owner write drift: {owner_writes}",
    )

    print(f"binary={args.libcp}")
    for name, (begin, end, sha256) in WINDOWS.items():
        print(f"{name}=0x{begin:x}..0x{end:x} sha256={sha256}")
    print("0x22ae60 order=owner(*(state+0x08)+0x10) -> 0x20ada0, then same owner -> 0x20bd60")
    print("0x20ada0 writes owner+0x78/+0x7c after reciprocal extrema over pre-solve ranges")
    print("0x20bd60 later writes owner+0x78/+0x7c after positive solved record+0x10 extrema")
    print("scope=static writer/order proof only; no downstream read or public-field name proven")


if __name__ == "__main__":
    main()
