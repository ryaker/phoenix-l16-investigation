#!/usr/bin/env python3
"""Verify the 0x219210 caller output path for 0x218940 score-helper samples."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs" / "prefusion_20ca00_record_z_watch"
STEM = "record_z_watch_unit1_70mm"

WINDOW_BEGIN = 0x219210
WINDOW_END = 0x219409
WINDOW_SHA256 = "a988329eb834dbd9c64c0499f93e83fa24813d18c020827ccdfb9dc54c6c7540"

VTABLE_ADDRESS_POINT = 0x658138
VTABLE_TYPEINFO_PTR = 0x658130
VTABLE_SLOT_PLUS_0X30 = 0x658168
TYPEINFO_OBJECT = 0x658180
TYPEINFO_NAME = 0x5D5970
EXPECTED_TYPEINFO_NAME = (
    "NSt3__110__function6__funcIZN2lt26SparseMirrorAngleOptimizer8optimize"
    "ERKNS2_13CapturedImage6CameraERKNS_6vectorINS2_4Vec2IfEENS_9allocatorISA_EEE"
    "ERKNS2_5ImageINS2_8vec4x8uiEEENS3_10FreeParamsENS3_12CostFunctionEdSA_E3$_2"
    "NSB_ISN_EEFviiiEEE"
)

HELPER_CALL = 0x219375
HELPER_RETURN = 0x21937A
HELPER_OUTPUT_STORE = 0x219381
HELPER_ENTRY = 0x218940
Z_COMPARE = 0x2189C4

ANCHORS = {
    0x219210: ("push", "rbp"),
    0x219224: ("mov", "r14, rdi"),
    0x219227: ("movsxd", "r15, dword ptr [rsi]"),
    0x21922A: ("movsxd", "rax, dword ptr [rdx]"),
    0x219260: ("mov", "rsi, qword ptr [r14 + 8]"),
    0x219284: ("mov", "rdi, r12"),
    0x219287: ("call", "0x218390"),
    0x2192A7: ("call", "0x264980"),
    0x219353: ("call", "0x23faf0"),
    0x219358: ("mov", "rdx, qword ptr [r14 + 0x30]"),
    0x21935C: ("mov", "rax, qword ptr [r14 + 0x38]"),
    0x219360: ("lea", "rcx, [r15*4]"),
    0x219368: ("add", "rcx, qword ptr [rax]"),
    0x21936B: ("mov", "rdi, qword ptr [rbp - 0x228]"),
    0x219372: ("mov", "rsi, r13"),
    0x219375: ("call", "0x218940"),
    0x21937A: ("mov", "rax, qword ptr [r14 + 0x18]"),
    0x21937E: ("mov", "rax, qword ptr [rax]"),
    0x219381: ("movss", "dword ptr [rax + r15*4], xmm0"),
    0x2193E8: ("inc", "r15"),
    0x2193F2: ("jl", "0x219260"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u64(blob: bytes, address: int) -> int:
    return int.from_bytes(blob[address : address + 8], "little")


def cstring(blob: bytes, address: int) -> str:
    return blob[address:].split(b"\0", 1)[0].decode("ascii")


def verify_static_window(libcp: Path = DEFAULT_LIBCP) -> None:
    blob = libcp.read_bytes()
    window = blob[WINDOW_BEGIN:WINDOW_END]
    require(len(window) == WINDOW_END - WINDOW_BEGIN, "short 0x219210 window")
    require(hashlib.sha256(window).hexdigest() == WINDOW_SHA256, "0x219210 window SHA-256 drift")
    require(u64(blob, VTABLE_TYPEINFO_PTR) == TYPEINFO_OBJECT, "0x219210 vtable typeinfo pointer drift")
    require(u64(blob, TYPEINFO_OBJECT + 8) == TYPEINFO_NAME, "0x219210 typeinfo name pointer drift")
    require(cstring(blob, TYPEINFO_NAME) == EXPECTED_TYPEINFO_NAME, "0x219210 typeinfo name drift")
    require(u64(blob, VTABLE_SLOT_PLUS_0X30) == 0x219210, "0x219210 vtable +0x30 slot drift")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in disassembler.disasm(window, WINDOW_BEGIN)
    }
    for address, expected in ANCHORS.items():
        require(instructions.get(address) == expected, f"anchor drift at 0x{address:x}: {instructions.get(address)}")

    require(HELPER_CALL < HELPER_RETURN < HELPER_OUTPUT_STORE, "helper output store is not after helper return")


def verify_runtime_stack() -> dict:
    report_path = RUN_DIR / f"{STEM}.json"
    report = json.loads(report_path.read_text())
    require(report.get("process_exit_status") == 0, "report process exit not zero")
    require(report.get("drive_hit_step_cap") is False, "drive hit step cap")
    require(report.get("errors") == [], f"probe errors: {report.get('errors')}")

    armed = report.get("armed") or {}
    require(armed.get("gate_index") == 3906, "armed gate index drift")
    z_samples = [sample for sample in report.get("samples", []) if sample.get("libcp_va") == Z_COMPARE]
    require(len(z_samples) == 37, f"expected 37 z-compare samples, got {len(z_samples)}")
    r15_values = []
    rcx_bases = set()
    for sample in z_samples:
        stack = sample.get("stack") or []
        require(stack[0].get("libcp_va") == Z_COMPARE, "sample stack top is not 0x2189c4")
        require(stack[0].get("function") == "___lldb_unnamed_symbol_218940", "sample stack top is not helper 0x218940")
        require(stack[1].get("libcp_va") == HELPER_RETURN, "sample caller return is not 0x21937a")
        require(stack[1].get("function") == "___lldb_unnamed_symbol_219210", "sample caller is not 0x219210")
        registers = sample.get("registers", {})
        r15 = registers.get("r15")
        rcx = registers.get("rcx")
        require(isinstance(r15, int) and r15 >= 0, "sample r15 missing")
        require(isinstance(rcx, int), "sample rcx missing")
        r15_values.append(r15)
        rcx_bases.add(rcx - 4 * r15)
        require(registers.get("rax") == armed.get("z_addr"), "sample rax is not watched z")
    require(len(set(r15_values)) == len(r15_values), "caller indices are not unique")
    require(len(rcx_bases) == 1, f"rcx base drift: {sorted(rcx_bases)}")

    return {
        "report": report_path,
        "samples": len(z_samples),
        "gate_index": armed.get("gate_index"),
        "z": armed.get("z_at_arm", {}).get("value"),
        "r15_min": min(r15_values),
        "r15_max": max(r15_values),
        "rcx_base": next(iter(rcx_bases)),
    }


def main() -> None:
    verify_static_window()
    summary = verify_runtime_stack()
    print(f"binary={DEFAULT_LIBCP}")
    print(f"window=0x{WINDOW_BEGIN:x}..0x{WINDOW_END:x} sha256={WINDOW_SHA256}")
    print(
        "callback_type="
        "SparseMirrorAngleOptimizer::optimize::$_2 std::__function void(int,int,int) "
        f"address_point=0x{VTABLE_ADDRESS_POINT:x} slot+0x30=0x219210"
    )
    print(f"report={summary['report']}")
    print(
        "runtime_stack="
        f"gate_index={summary['gate_index']} z={summary['z']:.9f} "
        f"z_compare_samples={summary['samples']} caller_return=0x{HELPER_RETURN:x} "
        f"r15_range={summary['r15_min']}..{summary['r15_max']} rcx_base=0x{summary['rcx_base']:x}"
    )
    print("caller_output=0x219375 call 0x218940 -> 0x219381 store xmm0 into [r14+0x18][r15]")
    print("scope=caller output-vector path only; no stored value, image effect, or final acceptance proven")


if __name__ == "__main__":
    main()
