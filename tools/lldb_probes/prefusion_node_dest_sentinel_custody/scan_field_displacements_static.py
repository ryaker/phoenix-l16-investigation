#!/usr/bin/env python3
"""Census installed-libcp instructions that access selected memory displacements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capstone import CS_AC_READ, CS_AC_WRITE, CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_OP_MEM


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
TEXT_BEGIN = 0x2250
TEXT_END = 0x555D20


def parse_int(value: str) -> int:
    return int(value, 0)


def effective_memory_access(mnemonic: str, operand_index: int, capstone_access: list[str]) -> list[str]:
    """Return Intel-syntax memory access, correcting incomplete Capstone flags."""
    if mnemonic == "lea":
        return []
    if mnemonic.startswith("mov") or mnemonic.startswith("cvt"):
        return ["write"] if operand_index == 0 else ["read"]
    if mnemonic in {"cmp", "test", "ucomiss", "comiss", "call", "jmp", "push"}:
        return ["read"]
    if mnemonic == "pop":
        return ["write"]
    if mnemonic.startswith("cmov"):
        return ["read"]
    if mnemonic in {
        "add", "sub", "and", "or", "xor", "imul", "divss", "mulss", "addss", "subss",
        "minss", "maxss", "shl", "shr", "sar", "sal", "inc", "dec", "xchg",
    }:
        return ["read", "write"] if operand_index == 0 else ["read"]
    return capstone_access


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    parser.add_argument("--displacement", type=parse_int, action="append", required=True)
    parser.add_argument("--mnemonic", action="append")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    text = blob[TEXT_BEGIN:TEXT_END]
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    disassembler.skipdata = True
    wanted_displacements = set(args.displacement)
    wanted_mnemonics = set(args.mnemonic or ())
    rows: list[dict] = []

    for instruction in disassembler.disasm(text, TEXT_BEGIN):
        if instruction.id == 0:
            continue
        if wanted_mnemonics and instruction.mnemonic not in wanted_mnemonics:
            continue
        matching = []
        memory_operands = []
        for operand_index, operand in enumerate(instruction.operands):
            if operand.type == X86_OP_MEM and operand.mem.disp in wanted_displacements:
                matching.append(operand.mem.disp)
                capstone_access = []
                if operand.access & CS_AC_READ:
                    capstone_access.append("read")
                if operand.access & CS_AC_WRITE:
                    capstone_access.append("write")
                memory_operands.append(
                    {
                        "displacement": operand.mem.disp,
                        "base": instruction.reg_name(operand.mem.base) or None,
                        "index": instruction.reg_name(operand.mem.index) or None,
                        "scale": operand.mem.scale,
                        "operand_index": operand_index,
                        "capstone_access": capstone_access,
                        "access": effective_memory_access(
                            instruction.mnemonic, operand_index, capstone_access
                        ),
                    }
                )
        if matching:
            rows.append(
                {
                    "address": instruction.address,
                    "address_hex": f"0x{instruction.address:x}",
                    "mnemonic": instruction.mnemonic,
                    "operands": instruction.op_str,
                    "displacements": matching,
                    "memory_operands": memory_operands,
                    "reads_selected_displacement": any(
                        "read" in operand["access"] for operand in memory_operands
                    ),
                    "writes_selected_displacement": any(
                        "write" in operand["access"] for operand in memory_operands
                    ),
                }
            )

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        for row in rows:
            disps = ",".join(f"0x{value:x}" for value in row["displacements"])
            memory = ",".join(
                f"{operand['base']}+0x{operand['displacement']:x}:"
                f"{'/'.join(operand['access']) or 'unknown'}"
                for operand in row["memory_operands"]
            )
            print(
                f"{row['address_hex']} {row['mnemonic']} {row['operands']} "
                f"; disp={disps} mem={memory}"
            )
        print(f"matches={len(rows)}")


if __name__ == "__main__":
    main()
