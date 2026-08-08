#!/usr/bin/env python3
"""Verify the 0x20ca00 ReProjectionCost wrapper, loss, and residual formula."""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import subprocess
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
ADDRESS_POINT = 0x667240
TYPEINFO = 0x667280
TYPE_NAME = 0x5D4AD0
EVALUATE = 0x20DED0
CAUCHY_GOT = 0x64F388
CAUCHY_PAYLOAD = 0x5C3580
ADD_RESIDUAL_CALL = 0x20D560
RAW_TYPE_NAME = (
    "N5ceres20AutoDiffCostFunctionIN2lt8Internal16ReProjectionCostELi2ELi1"
    "ELi0ELi0ELi0ELi0ELi0ELi0ELi0ELi0ELi0EEE"
)
DEMANGLED_TYPE_NAME = (
    "ceres::AutoDiffCostFunction<lt::Internal::ReProjectionCost, 2, 1, 0, 0, "
    "0, 0, 0, 0, 0, 0, 0>"
)

WINDOWS = {
    "cauchy": (
        0x20BE9D,
        0x20BEBD,
        "4d9848549d1156a08cd892bfb0bb7ddcba9a56db54396529be9d9ef546952f47",
    ),
    "loss_capture": (
        0x20C2BA,
        0x20C2C5,
        "32e3f84089c2632ed76886403f996e53d45cbf994692245289d145b1c104145d",
    ),
    "autodiff_wrapper": (
        0x20D0B3,
        0x20D119,
        "0b9a196c05646cbbbccfe140f85ac49d39a8e60d1df0089f2b147d837825f941",
    ),
    "residual_add": (
        0x20D43C,
        0x20D565,
        "ca71af033a6ddad7c5bb49d5ab709ba2b37fc2935107d3bdbcbafc236da94873",
    ),
    "evaluate": (
        0x20DED0,
        0x20DFC7,
        "8726f1b9b691b6ba75bb1d521964a7129ef8c52dd529b7d6c2e131e2d0118610",
    ),
}

ANCHORS = {
    0x20BE9D: ("mov", "rax, qword ptr [rip + 0x4434e4]"),
    0x20BEA4: ("add", "rax, 0x10"),
    0x20BEA8: ("mov", "qword ptr [rbp - 0x288], rax"),
    0x20BEAF: ("movaps", "xmm0, xmmword ptr [rip + 0x3b76ca]"),
    0x20BEB6: ("movups", "xmmword ptr [rbp - 0x280], xmm0"),
    0x20C2BA: ("lea", "rcx, [rbp - 0x288]"),
    0x20C2C1: ("mov", "qword ptr [rax + 0x28], rcx"),
    0x20D0B3: ("mov", "r14, qword ptr [r12 + 0x28]"),
    0x20D0E1: ("mov", "dword ptr [rbx + 0x20], 2"),
    0x20D0E8: ("mov", "dword ptr [rbp - 0x34], 1"),
    0x20D0F3: ("call", "0xdea90"),
    0x20D0F8: ("lea", "rax, [rip + 0x45a141]"),
    0x20D0FF: ("mov", "qword ptr [rbx], rax"),
    0x20D102: ("mov", "qword ptr [rbx + 0x28], r14"),
    0x20D10A: ("mov", "qword ptr [r15 + 0x28], rbx"),
    0x20D443: ("mov", "rdi, qword ptr [rbp - 0x2b8]"),
    0x20D450: ("mov", "rsi, qword ptr [r12 + 0x28]"),
    0x20D54E: ("mov", "rdx, qword ptr [rdi + 0x28]"),
    0x20D552: ("lea", "rdi, [rbp - 0xc0]"),
    0x20D559: ("lea", "rcx, [rbp - 0xc8]"),
    0x20D560: ("call", "0x555e64"),
    0x20DED9: ("mov", "rdi, qword ptr [rdx + 0x28]"),
    0x20DEF5: ("mov", "rax, qword ptr [rsi]"),
    0x20DEF8: ("movsd", "xmm0, qword ptr [rax]"),
    0x20DEFC: ("movsd", "xmm3, qword ptr [rdi]"),
    0x20DF00: ("mulsd", "xmm3, xmm0"),
    0x20DF04: ("movsd", "xmm1, qword ptr [rdi + 8]"),
    0x20DF09: ("mulsd", "xmm1, xmm0"),
    0x20DF0D: ("movsd", "xmm2, qword ptr [rdi + 0xa0]"),
    0x20DF39: ("addsd", "xmm2, qword ptr [rdi + 0xb8]"),
    0x20DF41: ("movsd", "xmm4, qword ptr [rdi + 0xc0]"),
    0x20DF6D: ("addsd", "xmm4, qword ptr [rdi + 0xd8]"),
    0x20DF75: ("mulsd", "xmm3, qword ptr [rdi + 0xe0]"),
    0x20DF7D: ("mulsd", "xmm1, qword ptr [rdi + 0xe8]"),
    0x20DF89: ("mulsd", "xmm0, qword ptr [rdi + 0xf0]"),
    0x20DF95: ("addsd", "xmm0, qword ptr [rdi + 0xf8]"),
    0x20DF9D: ("movsd", "xmm1, qword ptr [rip + 0x39b41b]"),
    0x20DFA5: ("divsd", "xmm1, xmm0"),
    0x20DFA9: ("mulsd", "xmm2, xmm1"),
    0x20DFAD: ("subsd", "xmm2, qword ptr [rdi + 0x50]"),
    0x20DFB2: ("movsd", "qword ptr [rcx], xmm2"),
    0x20DFB6: ("mulsd", "xmm1, xmm4"),
    0x20DFBA: ("subsd", "xmm1, qword ptr [rdi + 0x58]"),
    0x20DFBF: ("movsd", "qword ptr [rcx + 8], xmm1"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def qword(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob: bytes, offset: int) -> str:
    end = blob.index(0, offset)
    return blob[offset:end].decode("ascii")


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


def rip_target(instruction) -> int:
    memory_operands = [operand for operand in instruction.operands if operand.type == X86_OP_MEM]
    require(len(memory_operands) == 1, f"expected one memory operand at 0x{instruction.address:x}")
    return instruction.address + instruction.size + memory_operands[0].mem.disp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    require(qword(blob, ADDRESS_POINT - 0x08) == TYPEINFO, "wrapper typeinfo pointer drift")
    require(qword(blob, ADDRESS_POINT + 0x10) == EVALUATE, "Evaluate slot drift")
    require(qword(blob, TYPEINFO + 0x08) == TYPE_NAME, "wrapper type-name pointer drift")
    require(cstring(blob, TYPE_NAME) == RAW_TYPE_NAME, "wrapper raw type name drift")

    demangled = subprocess.run(
        ["c++filt", "-t", RAW_TYPE_NAME],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    require(demangled == DEMANGLED_TYPE_NAME, f"demangled type drift: {demangled}")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    instructions = {}
    for name, (begin, end, expected_sha256) in WINDOWS.items():
        window = blob[begin:end]
        require(len(window) == end - begin, f"short {name} window")
        require(hashlib.sha256(window).hexdigest() == expected_sha256, f"{name} SHA-256 drift")
        instructions.update((instruction.address, instruction) for instruction in disassembler.disasm(window, begin))

    for address, expected in ANCHORS.items():
        instruction = instructions.get(address)
        actual = (instruction.mnemonic, instruction.op_str) if instruction else None
        require(actual == expected, f"anchor drift at 0x{address:x}: {actual}")

    require(rip_target(instructions[0x20BE9D]) == CAUCHY_GOT, "CauchyLoss GOT target drift")
    require(rip_target(instructions[0x20BEAF]) == CAUCHY_PAYLOAD, "Cauchy payload target drift")
    require(rip_target(instructions[0x20D0F8]) == ADDRESS_POINT, "wrapper address-point target drift")
    require(rip_target(instructions[0x20DF9D]) == 0x5A93C0, "projection one constant drift")
    require(struct.unpack_from("<2d", blob, CAUCHY_PAYLOAD) == (1.0, 1.0), "Cauchy payload drift")
    require(struct.unpack_from("<d", blob, 0x5A93C0)[0] == 1.0, "projection one constant drift")

    imports = imported_stubs(args.libcp)
    require(imports.get(CAUCHY_GOT) == "__ZTVN5ceres10CauchyLossE", "CauchyLoss import drift")
    require(
        imports.get(rel32_target(blob, ADD_RESIDUAL_CALL))
        == "__ZN5ceres7Problem16AddResidualBlockEPNS_12CostFunctionEPNS_12LossFunctionEPd",
        "AddResidualBlock import drift",
    )

    print(f"binary={args.libcp}")
    print(f"wrapper={DEMANGLED_TYPE_NAME}")
    print(f"address_point=0x{ADDRESS_POINT:x} evaluate=0x{EVALUATE:x}")
    print("loss=ceres::CauchyLoss payload=(1.0,1.0) captured_at=callable+0x28")
    print("parameter=one scalar residuals=two")
    print("ray=(functor[0]*s,functor[8]*s,s)")
    print("point=M3x4(functor+0xa0)*ray_homogeneous")
    print("residual=(point.x/point.z-functor[0x50],point.y/point.z-functor[0x58])")


if __name__ == "__main__":
    main()
