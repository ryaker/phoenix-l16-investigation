#!/usr/bin/env python3
"""Verify mode-selected depth endpoints through the 0x20ca00 Ceres bounds."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import (
    X86_INS_CALL,
    X86_OP_IMM,
    X86_OP_MEM,
    X86_REG_RIP,
)


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
DEFAULT_REPORT_DIR = Path("runs/stereo_candidate_gate")
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
TEXT_BEGIN = 0x2250
TEXT_END = 0x555D20
TABLE_NEAR = 0x609428
TABLE_FAR = 0x609430
LOWER_CALL = 0x20D270
UPPER_CALL = 0x20D291

WINDOWS = {
    "mode_argument": (
        0x3F2C54,
        0x3F2C63,
        "93a3e78c7f02994d8ab284e614f769a514a82671df77f14a0b29e166533f18f2",
    ),
    "sole_wrapper_call": (
        0x3F46D0,
        0x3F46EB,
        "3107ae3da348122a21e43ae4b6465c9de6d2f77d15c0de1c0dd308e4d0ea0523",
    ),
    "owner_literal_mode": (
        0x3B2FEB,
        0x3B3016,
        "202de9fb8c0b58ce1ba849d5244da28d51234e52c83753090acba150a973b0a7",
    ),
    "mode_pair": (
        0x3F4100,
        0x3F414F,
        "dad67886a007fd215dff36d82e7af902fe0365bde28350f760a58a32559db4bd",
    ),
    "state_entry": (
        0x225160,
        0x225177,
        "535f2037e2ad175549b41bb52c2778e13826e2ddc62170ca1afbdb6f8ac302b8",
    ),
    "state_copy": (
        0x2251D7,
        0x2251EC,
        "2ea2348e110dc5d7904ce6b675c77dd7f3a1f87d071084d40262184eedf65cc9",
    ),
    "constructor_pass": (
        0x225522,
        0x2255E2,
        "fad3e2d28ec4f08d154a198fdc80a5e03517e28d122abbc6a4b3ddbef891f3a5",
    ),
    "constructor_thunk": (
        0x20AD60,
        0x20AD94,
        "283bd643a6476a0f876d84f4cb824aa0c9fb65436bfd96ad640ed8fd0716e2e1",
    ),
    "owner_entry": (
        0x20AC60,
        0x20AC82,
        "d0afa12f273ca4de7ed98161cee817d9d74863c317619c0a6f28c83db946eabb",
    ),
    "owner_copy": (
        0x20AD30,
        0x20AD4D,
        "c42126ea9d97207f63cfb66e3db59419f0098006c3ce2a4a764d5bb74bc129a7",
    ),
    "bound_calls": (
        0x20D254,
        0x20D296,
        "4b6f2fb9649f1105dea45ef7608b0bfaf1f12024ad12baa8baa6bc150b1f3549",
    ),
}

ANCHORS = {
    0x3B3004: ("xor", "edx, edx"),
    0x3B3011: ("call", "0x3f46d0"),
    0x3F46E6: ("call", "0x3f2c40"),
    0x3F2C61: ("mov", "ebx, edx"),
    0x3F4100: ("test", "ebx, ebx"),
    0x3F4102: ("movabs", "rax, 0x491c400043480000"),
    0x3F410C: ("mov", "qword ptr [rbp - 0x798], rax"),
    0x3F4113: ("je", "0x3f4126"),
    0x3F4115: ("movabs", "rax, 0x471c4000428c0000"),
    0x3F411F: ("mov", "qword ptr [rbp - 0x798], rax"),
    0x3F4132: ("lea", "rcx, [rbp - 0x798]"),
    0x3F414A: ("call", "0x225160"),
    0x225171: ("mov", "r14, rcx"),
    0x2251D7: ("mov", "eax, dword ptr [r14]"),
    0x2251DA: ("mov", "dword ptr [r13 + 0x100], eax"),
    0x2251E1: ("mov", "eax, dword ptr [r14 + 4]"),
    0x2251E5: ("mov", "dword ptr [r13 + 0x104], eax"),
    0x225522: ("lea", "r12, [r13 + 0x100]"),
    0x2255DA: ("mov", "r9, r12"),
    0x2255DD: ("call", "0x20ad60"),
    0x20AD8F: ("jmp", "0x20ac60"),
    0x20AC71: ("mov", "qword ptr [rbp - 0x30], r9"),
    0x20AC7F: ("mov", "rbx, rdi"),
    0x20AD30: ("mov", "rcx, qword ptr [rbp - 0x30]"),
    0x20AD34: ("mov", "eax, dword ptr [rcx]"),
    0x20AD36: ("mov", "dword ptr [rbx + 0x70], eax"),
    0x20AD39: ("mov", "eax, dword ptr [rcx + 4]"),
    0x20AD3C: ("mov", "dword ptr [rbx + 0x74], eax"),
    0x20D254: ("mov", "rax, qword ptr [rbp - 0x2a8]"),
    0x20D25B: ("movss", "xmm0, dword ptr [rax + 0x70]"),
    0x20D260: ("cvtss2sd", "xmm0, xmm0"),
    0x20D269: ("lea", "rsi, [rbp - 0xc8]"),
    0x20D270: ("call", "0x555e82"),
    0x20D275: ("mov", "rax, qword ptr [rbp - 0x2a8]"),
    0x20D27C: ("movss", "xmm0, dword ptr [rax + 0x74]"),
    0x20D281: ("cvtss2sd", "xmm0, xmm0"),
    0x20D28A: ("lea", "rsi, [rbp - 0xc8]"),
    0x20D291: ("call", "0x555e88"),
}

REPORTS = {
    "28mm": "stereo_candidate_gate_28mm.json",
    "35mm": "stereo_candidate_gate_35mm.json",
    "70mm": "stereo_candidate_gate_70mm.json",
    "150mm": "stereo_candidate_gate_150mm.json",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rel32_target(blob: bytes, va: int) -> int:
    require(blob[va] == 0xE8, f"expected call at 0x{va:x}")
    displacement = struct.unpack_from("<i", blob, va + 1)[0]
    return va + 5 + displacement


def complete_code_references(blob: bytes, target: int) -> list:
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    disassembler.skipdata = True
    rows = []
    for instruction in disassembler.disasm(
        blob[TEXT_BEGIN:TEXT_END], TEXT_BEGIN
    ):
        if instruction.id == 0:
            continue
        immediate = any(
            operand.type == X86_OP_IMM and operand.imm == target
            for operand in instruction.operands
        )
        rip_relative = any(
            operand.type == X86_OP_MEM
            and operand.mem.base == X86_REG_RIP
            and instruction.address + instruction.size + operand.mem.disp
            == target
            for operand in instruction.operands
        )
        if immediate or rip_relative:
            rows.append(instruction)
    return rows


def require_sole_direct_call(
    blob: bytes, target: int, expected_callsite: int
) -> None:
    references = complete_code_references(blob, target)
    require(
        [item.address for item in references] == [expected_callsite],
        f"0x{target:x}: code-reference census changed",
    )
    item = references[0]
    require(
        item.id == X86_INS_CALL
        and len(item.operands) == 1
        and item.operands[0].type == X86_OP_IMM
        and item.operands[0].imm == target,
        f"0x{target:x}: sole reference is not the expected direct call",
    )
    require(
        blob.find(target.to_bytes(8, "little")) == -1,
        f"0x{target:x}: absolute function pointer appeared",
    )


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


def verify_report(path: Path, tier: str) -> int:
    report = json.loads(path.read_text())
    require(report["process"] == {"exit_status": 0, "state": "exited", "valid": True}, f"{tier}: process")
    require(report["errors"] == [], f"{tier}: probe errors")
    require(not report["drive_hit_step_cap"], f"{tier}: step cap")
    require(report["counts"]["constructor_entry_3f2c40"] == 1, f"{tier}: constructor count")
    entries = [sample for sample in report["samples"] if sample["site"] == "constructor_entry_3f2c40"]
    require(len(entries) == 1, f"{tier}: constructor sample count")
    mode = entries[0]["registers"]["rdx"]
    require(mode == 0, f"{tier}: expected selected mode 0, got {mode}")
    return mode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()

    blob = args.libcp.read_bytes()
    require(
        hashlib.sha256(blob).hexdigest() == LIBCP_SHA256,
        "installed libcp SHA-256 drift",
    )
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions: dict[int, tuple[str, str]] = {}
    for name, (begin, end, expected_sha256) in WINDOWS.items():
        window = blob[begin:end]
        require(len(window) == end - begin, f"short {name} window")
        require(hashlib.sha256(window).hexdigest() == expected_sha256, f"{name} SHA-256 drift")
        instructions.update(
            (instruction.address, (instruction.mnemonic, instruction.op_str))
            for instruction in disassembler.disasm(window, begin)
        )
    for address, expected in ANCHORS.items():
        require(instructions.get(address) == expected, f"anchor drift at 0x{address:x}: {instructions.get(address)}")

    require_sole_direct_call(blob, 0x3F2C40, 0x3F46E6)
    require_sole_direct_call(blob, 0x3F46D0, 0x3B3011)

    mode_zero = struct.unpack("<2f", struct.pack("<Q", 0x491C400043480000))
    mode_nonzero = struct.unpack("<2f", struct.pack("<Q", 0x471C4000428C0000))
    require(mode_zero == (200.0, 640000.0), "mode-zero pair drift")
    require(mode_nonzero == (70.0, 40000.0), "mode-nonzero pair drift")
    require(struct.unpack_from("<2f", blob, TABLE_NEAR) == (200.0, 70.0), "near table drift")
    require(struct.unpack_from("<2f", blob, TABLE_FAR) == (640000.0, 40000.0), "far table drift")

    imports = imported_stubs(args.libcp)
    require(
        imports.get(rel32_target(blob, LOWER_CALL)) == "__ZN5ceres7Problem22SetParameterLowerBoundEPdid",
        "lower-bound import drift",
    )
    require(
        imports.get(rel32_target(blob, UPPER_CALL)) == "__ZN5ceres7Problem22SetParameterUpperBoundEPdid",
        "upper-bound import drift",
    )

    modes = {tier: verify_report(args.report_dir / filename, tier) for tier, filename in REPORTS.items()}

    print(f"binary={args.libcp}")
    print(f"table_near=[200.0,70.0] table_far=[640000.0,40000.0]")
    print("mode0=[200.0,640000.0] mode_nonzero=[70.0,40000.0]")
    print("installed_origin=sole 0x3b3011 caller hardcodes edx=0 -> mode0")
    print("custody=3f2c40.edx -> state+0x100/+0x104 -> owner+0x70/+0x74 -> Ceres scalar lower/upper")
    print("runtime_modes=" + ",".join(f"{tier}:{mode}" for tier, mode in modes.items()))


if __name__ == "__main__":
    main()
