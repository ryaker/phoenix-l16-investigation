#!/usr/bin/env python3
"""Verify the 0x216f60 consumer for the 0x219210 score-vector callback."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs" / "prefusion_216f60_score_vector_consumer"
STEM = "score_vector_consumer_unit1_70mm"

WINDOW_BEGIN = 0x216F60
WINDOW_END = 0x2180E0
WINDOW_SHA256 = "42b320ff8f9c3c0f5c2eaccff82a52fa4a105b1c475b799b2362a3d86e8d1f7e"

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

CALLBACK_ENTRY = 0x219210
CONSTRUCT_DONE = 0x21797A
STORE_AFTER = 0x219387
CONSUMER_ENTRY = 0x217A68

EXACT_ANCHORS = {
    0x216F60: ("push", "rbp"),
    0x21743A: ("lea", "rdi, [r15*4]"),
    0x217477: ("mov", "qword ptr [rbp - 0x3f0], rax"),
    0x21747E: ("lea", "r13, [rax + r15*4]"),
    0x217482: ("mov", "qword ptr [rbp - 0x3e0], r13"),
    0x2174AE: ("mov", "qword ptr [rbp - 0x3e8], r13"),
    0x2174CA: ("mov", "rdi, qword ptr [rbp - 0x5a8]"),
    0x2174D6: ("mov", "qword ptr [rbp - 0x410], rax"),
    0x2174E1: ("mov", "qword ptr [rbp - 0x400], r12"),
    0x2174F3: ("mov", "qword ptr [rbp - 0x408], r12"),
    0x21750F: ("lea", "rax, [r15*8]"),
    0x21752B: ("mov", "qword ptr [rbp - 0x428], rax"),
    0x217532: ("mov", "qword ptr [rbp - 0x430], rax"),
    0x217541: ("mov", "qword ptr [rbp - 0x420], rcx"),
    0x21793B: ("lea", "rcx, [rbp - 0x430]"),
    0x217942: ("mov", "qword ptr [rax + 0x10], rcx"),
    0x217946: ("lea", "rcx, [rbp - 0x3f0]"),
    0x21794D: ("mov", "qword ptr [rax + 0x18], rcx"),
    0x217967: ("mov", "qword ptr [rax + 0x30], r15"),
    0x21796B: ("lea", "rcx, [rbp - 0x410]"),
    0x217972: ("mov", "qword ptr [rax + 0x38], rcx"),
    0x217992: ("call", "0x5670"),
    0x217A68: ("mov", "rax, qword ptr [rbp - 0x3f0]"),
    0x217A6F: ("mov", "rdx, qword ptr [rbp - 0x3e8]"),
    0x217A81: ("mov", "rcx, rsi"),
    0x217A90: ("add", "rsi, 4"),
    0x217A99: ("movss", "xmm0, dword ptr [rsi]"),
    0x217A9D: ("ucomiss", "xmm0, dword ptr [rcx]"),
    0x217AA0: ("jae", "0x217a90"),
    0x217AA4: ("sub", "rcx, rax"),
    0x217AAE: ("mov", "rsi, qword ptr [rbp - 0x410]"),
    0x217AB9: ("movss", "xmm0, dword ptr [rsi + rdx]"),
    0x217AC6: ("ucomiss", "xmm1, xmm0"),
    0x217AC9: ("jb", "0x217bf8"),
    0x217AD2: ("ucomiss", "xmm0, dword ptr [rsi + rdx*4]"),
    0x217AD6: ("ja", "0x217bf8"),
    0x217ADC: ("shr", "rcx, 2"),
    0x217AE8: ("movss", "xmm0, dword ptr [rax + rdx*4]"),
    0x217AED: ("mulss", "xmm0, dword ptr [rip + 0x3bd85b]"),
    0x217AF5: ("ucomiss", "xmm0, dword ptr [rax + rcx*4]"),
    0x217AF9: ("jb", "0x217bf8"),
    0x217AFF: ("mov", "rax, qword ptr [rbp - 0x430]"),
    0x217B06: ("lea", "rcx, [rcx + rcx*2]"),
    0x217B0A: ("movsd", "xmm0, qword ptr [rax + rcx*8]"),
    0x217B31: ("lea", "rdi, [rbp - 0x5a0]"),
    0x217B3F: ("call", "0x218390"),
    0x217BB7: ("mov", "rdi, qword ptr [rbp - 0x628]"),
    0x217BBE: ("call", "0xf33d0"),
}

RIP_TARGETS = {
    0x217926: 0x658138,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u64(blob: bytes, address: int) -> int:
    return int.from_bytes(blob[address : address + 8], "little")


def cstring(blob: bytes, address: int) -> str:
    return blob[address:].split(b"\0", 1)[0].decode("ascii")


def decode_window(blob: bytes) -> dict[int, tuple[str, str, object]]:
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    decoded = {}
    for instruction in disassembler.disasm(blob[WINDOW_BEGIN:WINDOW_END], WINDOW_BEGIN):
        rip_target = None
        for operand in instruction.operands:
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                rip_target = instruction.address + instruction.size + operand.mem.disp
        decoded[instruction.address] = (instruction.mnemonic, instruction.op_str, rip_target)
    return decoded


def verify_static_window(libcp: Path = DEFAULT_LIBCP) -> None:
    blob = libcp.read_bytes()
    window = blob[WINDOW_BEGIN:WINDOW_END]
    require(len(window) == WINDOW_END - WINDOW_BEGIN, "short 0x216f60 window")
    require(hashlib.sha256(window).hexdigest() == WINDOW_SHA256, "0x216f60 window SHA-256 drift")
    require(u64(blob, VTABLE_TYPEINFO_PTR) == TYPEINFO_OBJECT, "0x219210 vtable typeinfo pointer drift")
    require(u64(blob, TYPEINFO_OBJECT + 8) == TYPEINFO_NAME, "0x219210 typeinfo name pointer drift")
    require(cstring(blob, TYPEINFO_NAME) == EXPECTED_TYPEINFO_NAME, "0x219210 typeinfo name drift")
    require(u64(blob, VTABLE_SLOT_PLUS_0X30) == CALLBACK_ENTRY, "0x219210 vtable +0x30 slot drift")

    instructions = decode_window(blob)
    for address, expected in EXACT_ANCHORS.items():
        actual = instructions.get(address)
        require(actual is not None, f"anchor missing at 0x{address:x}")
        require(actual[:2] == expected, f"anchor drift at 0x{address:x}: {actual[:2]}")
    for address, expected_target in RIP_TARGETS.items():
        actual = instructions.get(address)
        require(actual is not None, f"rip-target anchor missing at 0x{address:x}")
        require(actual[2] == expected_target, f"rip target drift at 0x{address:x}: {actual[2]}")


def verify_runtime_same_vector() -> dict:
    report_path = RUN_DIR / f"{STEM}.json"
    report = json.loads(report_path.read_text())
    require(report.get("process_exit_status") == 0, "report process exit not zero")
    require(report.get("drive_hit_step_cap") is False, "drive hit step cap")
    require(report.get("errors") == [], f"probe errors: {report.get('errors')}")

    counts = report.get("counts") or {}
    require(counts.get("constructs_recorded") == 1, "expected one recorded construction")
    require(counts.get("consumers_recorded") == 1, "expected one recorded consumer")
    require(counts.get("store_samples_recorded") == 64, "expected 64 recorded stores")
    require(counts.get("matching_store_hits", 0) >= 64, "insufficient matching store hits")

    constructs = report.get("constructs") or []
    stores = report.get("stores") or []
    consumers = report.get("consumers") or []
    require(len(constructs) == 1, "construction packet count drift")
    require(len(stores) == 64, "store packet count drift")
    require(len(consumers) == 1, "consumer packet count drift")

    construct = constructs[0]
    consumer = consumers[0]
    require(construct.get("libcp_va") == CONSTRUCT_DONE, "construction VA drift")
    require(consumer.get("libcp_va") == CONSUMER_ENTRY, "consumer VA drift")
    require(all((construct.get("field_matches") or {}).values()), "closure field/header mismatch")
    require(all((consumer.get("matches_constructed_headers") or {}).values()), "consumer header mismatch")

    return_vector = construct.get("return_vector") or {}
    side_vector = construct.get("side_vector") or {}
    candidate_records = construct.get("candidate_records") or {}
    require(return_vector.get("count") == 1089, "return-vector count drift")
    require(side_vector.get("count") == 1089, "side-vector count drift")
    require(candidate_records.get("count") == 1089, "candidate-record count drift")
    require((construct.get("closure_fields") or {}).get("+0x18") == return_vector.get("header"), "closure +0x18 drift")
    require((construct.get("closure_fields") or {}).get("+0x38") == side_vector.get("header"), "closure +0x38 drift")
    require(
        (construct.get("closure_fields") or {}).get("+0x10") == candidate_records.get("header"),
        "closure +0x10 drift",
    )

    store_indices = []
    for sample in stores:
        require(sample.get("libcp_va") == STORE_AFTER, "store VA drift")
        require(sample.get("closure") == construct.get("closure"), "store closure drift")
        require(sample.get("matches_constructed_return_begin") is True, "store return-vector begin drift")
        index = sample.get("index")
        require(isinstance(index, int) and 0 <= index < 1089, "store index out of range")
        require(
            sample.get("value_address") == return_vector.get("begin") + 4 * index,
            "store value address drift",
        )
        require((sample.get("stored_value") or {}).get("read_ok") is True, "stored value unreadable")
        store_indices.append(index)
    require(len(set(store_indices)) == 64, "store sample indices are not unique")

    consumer_return = consumer.get("return_vector") or {}
    require(consumer_return.get("header") == return_vector.get("header"), "consumer return header drift")
    require(consumer_return.get("begin") == return_vector.get("begin"), "consumer return begin drift")
    require(consumer_return.get("count") == 1089, "consumer return count drift")
    require(consumer.get("store_samples_recorded") == 64, "consumer did not observe 64 prior store samples")
    require(len(consumer.get("matching_store_samples") or []) == 10, "consumer matching-store sample drift")

    winner = consumer.get("winner") or {}
    require(winner.get("computed") is True, "min-like winner not computed")
    require(winner.get("count") == 1089, "winner count drift")
    require(winner.get("winner_index") == 505, "winner index drift")
    winner_value = winner.get("winner") or {}
    require(winner_value.get("hex") == "57309940", "winner bits drift")
    require(
        winner_value.get("addr") == return_vector.get("begin") + 4 * winner.get("winner_index"),
        "winner address drift",
    )

    return {
        "report": report_path,
        "closure": construct.get("closure"),
        "return_header": return_vector.get("header"),
        "return_begin": return_vector.get("begin"),
        "count": return_vector.get("count"),
        "store_samples": len(stores),
        "winner_index": winner.get("winner_index"),
        "winner_value": winner_value.get("value"),
        "winner_hex": winner_value.get("hex"),
    }


def main() -> None:
    verify_static_window()
    summary = verify_runtime_same_vector()
    print(f"binary={DEFAULT_LIBCP}")
    print(f"window=0x{WINDOW_BEGIN:x}..0x{WINDOW_END:x} sha256={WINDOW_SHA256}")
    print(
        "callback_construction="
        "0x216f60 stores vtable 0x658138 and captures vector headers "
        "+0x18=&[rbp-0x3f0], +0x38=&[rbp-0x410], +0x10=&[rbp-0x430]"
    )
    print(
        "runtime_same_vector="
        f"closure=0x{summary['closure']:x} return_header=0x{summary['return_header']:x} "
        f"return_begin=0x{summary['return_begin']:x} count={summary['count']} "
        f"stores={summary['store_samples']} consumer=0x{CONSUMER_ENTRY:x}"
    )
    print(
        "runtime_winner="
        f"index={summary['winner_index']} value={summary['winner_value']:.9f} "
        f"hex={summary['winner_hex']}"
    )
    print(f"runtime_report={summary['report']}")
    print(
        "scope=one Unit-1 70mm same-runtime callback-store to parent-consumer vector custody; "
        "no record-specific score, image effect, or final acceptance proven"
    )


if __name__ == "__main__":
    main()
