#!/usr/bin/env python3
"""Verify 0x20ca00 as the Triangulator::refine3dPoints lambda callback."""

from __future__ import annotations

import argparse
import hashlib
import struct
import subprocess
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
ADDRESS_POINT = 0x657F00
TYPEINFO = 0x657F50
TYPE_NAME = 0x5D4A30
CALLBACK = 0x20CA00
CONSTRUCTOR_BEGIN = 0x20C274
CONSTRUCTOR_END = 0x20C2FB
CONSTRUCTOR_SHA256 = "08101f5c0fc8456c472566e294b2fa3e35e20ee6593e92ec033bf3570bc0b6d6"
RAW_TYPE_NAME = (
    "NSt3__110__function6__funcIZN2lt12Triangulator14refine3dPointsEvE3$_0"
    "NS_9allocatorIS4_EEFviiiEEE"
)
DEMANGLED_TYPE_NAME = (
    "std::__1::__function::__func<lt::Triangulator::refine3dPoints()::$_0, "
    "std::__1::allocator<lt::Triangulator::refine3dPoints()::$_0>, void (int, int, int)>"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def qword(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob: bytes, offset: int) -> str:
    end = blob.index(0, offset)
    return blob[offset:end].decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    require(qword(blob, ADDRESS_POINT - 0x10) == 0, "vtable offset-to-top drift")
    require(qword(blob, ADDRESS_POINT - 0x08) == TYPEINFO, "vtable typeinfo pointer drift")
    require(qword(blob, ADDRESS_POINT + 0x30) == CALLBACK, "vtable +0x30 callback drift")
    require(qword(blob, TYPEINFO + 0x08) == TYPE_NAME, "typeinfo name pointer drift")
    require(cstring(blob, TYPE_NAME) == RAW_TYPE_NAME, "raw typeinfo name drift")

    demangled = subprocess.run(
        ["c++filt", "-t", RAW_TYPE_NAME],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    require(demangled == DEMANGLED_TYPE_NAME, f"demangled type drift: {demangled}")

    window = blob[CONSTRUCTOR_BEGIN:CONSTRUCTOR_END]
    require(hashlib.sha256(window).hexdigest() == CONSTRUCTOR_SHA256, "constructor SHA-256 drift")
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    instructions = {instruction.address: instruction for instruction in disassembler.disasm(window, CONSTRUCTOR_BEGIN)}

    lea = instructions[0x20C28B]
    require(lea.mnemonic == "lea" and lea.op_str == "rcx, [rip + 0x44bc6e]", "address-point LEA drift")
    mem = lea.operands[1]
    require(mem.type == X86_OP_MEM, "address-point source is not memory")
    require(lea.address + lea.size + mem.mem.disp == ADDRESS_POINT, "address-point LEA target drift")
    require(
        (instructions[0x20C292].mnemonic, instructions[0x20C292].op_str)
        == ("mov", "qword ptr [rax], rcx"),
        "callable vtable store drift",
    )
    require(
        (instructions[0x20C2F6].mnemonic, instructions[0x20C2F6].op_str)
        == ("call", "0x5670"),
        "executor dispatch drift",
    )

    executor = list(disassembler.disasm(blob[0x56CD:0x56EC], 0x56CD))
    indirect = next((instruction for instruction in executor if instruction.address == 0x56E9), None)
    require(indirect is not None, "missing executor indirect call")
    require((indirect.mnemonic, indirect.op_str) == ("call", "qword ptr [rax + 0x30]"), "executor slot drift")

    print(f"binary={args.libcp}")
    print(f"typeinfo=0x{TYPEINFO:x} raw={RAW_TYPE_NAME}")
    print(f"demangled={DEMANGLED_TYPE_NAME}")
    print(f"address_point=0x{ADDRESS_POINT:x} slot_0x30=0x{CALLBACK:x}")
    print("dispatch=0x20c28b/address-point -> 0x20c2f6/0x5670 -> [vtable+0x30]")


if __name__ == "__main__":
    main()
