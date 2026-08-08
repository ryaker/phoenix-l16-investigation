#!/usr/bin/env python3
"""Verify the direct numeric-read census for owner-range displacements."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_OP_MEM

from scan_field_displacements_static import (
    DEFAULT_LIBCP,
    TEXT_BEGIN,
    TEXT_END,
    effective_memory_access,
)


EXPECTED_LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
DISPLACEMENTS = {0x78, 0x7C}
NUMERIC_READ_MNEMONICS = {
    "movss",
    "divss",
    "mulss",
    "addss",
    "subss",
    "minss",
    "maxss",
    "ucomiss",
    "comiss",
    "cvtss2sd",
    "movsd",
    "movups",
    "movupd",
    "movdqu",
    "movlpd",
    "movq",
}

EXPECTED_READS = {
    0x9DB99: ("movsd", "xmm6, qword ptr [rsi + 0x78]", "4x4-double matrix family"),
    0x9DF38: ("movsd", "xmm7, qword ptr [rsi + 0x78]", "4x4-double matrix family"),
    0xEA8A1: ("movups", "xmm1, xmmword ptr [r13 + 0x78]", "0xa0-byte record move"),
    0x101C00: ("movss", "xmm1, dword ptr [rax + 0x7c]", "caller stack-local transform record"),
    0x1C7596: ("movsd", "xmm3, qword ptr [rbx + 0x78]", "three-double vector magnitude"),
    0x21D142: ("movsd", "xmm1, qword ptr [rsi + rax + 0x78]", "0x40-stride double-array reduction"),
    0x24006F: ("movss", "xmm1, dword ptr [rbx + 0x78]", "State source-record composition"),
    0x240995: ("divss", "xmm0, dword ptr [r15 + 0x7c]", "State keyed source record"),
    0x2409D0: ("movss", "xmm1, dword ptr [r15 + 0x78]", "State keyed source record"),
    0x24E79D: ("movups", "xmm0, xmmword ptr [rbx + 0x78]", "0x88-byte record copy"),
    0x24E7FE: ("movups", "xmm0, xmmword ptr [rdi + 0x78]", "0x88-byte record copy"),
    0x3A47F7: ("movdqu", "xmm0, xmmword ptr [r9 + 0x78]", "four-int rectangle reduction"),
    0x3ABA07: ("movdqu", "xmm0, xmmword ptr [r8 + 0x78]", "four-int rectangle reduction"),
    0x3ABAD9: ("movdqu", "xmm0, xmmword ptr [rbx + 0x78]", "four-int rectangle reduction"),
    0x3C74EF: ("movss", "xmm1, dword ptr [rbx + 0x7c]", "tone_mapping.sharpening config"),
}

ANCHORS = {
    0x101949: ("lea", "rax, [rbp - 0x120]"),
    0x101950: ("mov", "qword ptr [rsp + 8], rax"),
    0x10197C: ("call", "0x1019d0"),
    0x101BC9: ("mov", "rax, qword ptr [rbp + 0x18]"),
    0x106C20: ("lea", "rax, [rbp - 0x120]"),
    0x106C27: ("mov", "qword ptr [rsp + 8], rax"),
    0x106C53: ("call", "0x1019d0"),
    0x23D33B: ("add", "rsi, 0x20"),
    0x23D34D: ("call", "0x2406a0"),
    0x2406B7: ("mov", "r15, rsi"),
    0x3C7514: ("lea", "rsi, [rip + 0x26d92a]"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def direct_call_sites(instructions, target: int) -> list[int]:
    return [
        instruction.address
        for instruction in instructions
        if instruction.mnemonic == "call" and instruction.op_str == hex(target)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == EXPECTED_LIBCP_SHA256, "libcp SHA-256 drift")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    disassembler.skipdata = True
    instructions = list(disassembler.disasm(blob[TEXT_BEGIN:TEXT_END], TEXT_BEGIN))
    by_address = {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in instructions
    }

    reads = {}
    for instruction in instructions:
        if instruction.mnemonic not in NUMERIC_READ_MNEMONICS:
            continue
        for operand_index, operand in enumerate(instruction.operands):
            if operand.type != X86_OP_MEM or operand.mem.disp not in DISPLACEMENTS:
                continue
            capstone_access = []
            access = effective_memory_access(
                instruction.mnemonic, operand_index, capstone_access
            )
            if "read" in access:
                reads[instruction.address] = (instruction.mnemonic, instruction.op_str)

    expected = {
        address: (mnemonic, operands)
        for address, (mnemonic, operands, _category) in EXPECTED_READS.items()
    }
    require(reads == expected, f"direct numeric-read census drift: {reads}")

    for address, expected_anchor in ANCHORS.items():
        require(
            by_address.get(address) == expected_anchor,
            f"anchor drift at 0x{address:x}: {by_address.get(address)}",
        )

    require(
        direct_call_sites(instructions, 0x1019D0) == [0x10197C, 0x106C53],
        "0x1019d0 caller census drift",
    )
    require(
        direct_call_sites(instructions, 0x2406A0) == [0x23D34D],
        "0x2406a0 caller census drift",
    )
    require(
        not any(0x20ADA0 <= address < 0x20C4BA for address in reads),
        "owner writer family unexpectedly contains a direct numeric read",
    )
    require(
        not any(0x22AE60 <= address < 0x22AEA8 for address in reads),
        "State caller unexpectedly contains a direct numeric read",
    )

    print(f"binary={args.libcp}")
    print(f"libcp_sha256={EXPECTED_LIBCP_SHA256}")
    print(f"direct_numeric_reads={len(reads)}")
    for address, (mnemonic, operands, category) in EXPECTED_READS.items():
        print(f"0x{address:x} {mnemonic} {operands} ; {category}")
    print("owner_writer_family_direct_numeric_reads=0")
    print("state_22ae60_direct_numeric_reads=0")
    print(
        "scope=no direct same-displacement floating/vector numeric consumer identified; "
        "aliases, adjusted pointers, integer bit-copies, and indirect accessors remain open"
    )


if __name__ == "__main__":
    main()
