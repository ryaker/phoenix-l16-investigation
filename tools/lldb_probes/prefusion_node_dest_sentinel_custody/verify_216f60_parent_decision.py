#!/usr/bin/env python3
"""Verify the four-zoom 0x216f60 score-selection and record gate."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs" / "prefusion_216f60_parent_decision"
RUNS = (
    ("28mm", "28mm"),
    ("35mm", "35mm"),
    ("70mm", "70mm"),
    ("150mm", "150mm"),
    ("unit2_35mm", "Unit-2 35mm"),
)

LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
WINDOW_BEGIN = 0x217A68
WINDOW_END = 0x217BC3
WINDOW_SHA256 = "aaaf9c8c42f9340798432511b77c2c65cd042f188f67a78d415612293dba40a7"

ANCHORS = {
    0x217A68: ("mov", "rax, qword ptr [rbp - 0x3f0]"),
    0x217A6F: ("mov", "rdx, qword ptr [rbp - 0x3e8]"),
    0x217A99: ("movss", "xmm0, dword ptr [rsi]"),
    0x217A9D: ("ucomiss", "xmm0, dword ptr [rcx]"),
    0x217AA0: ("jae", "0x217a90"),
    0x217AA4: ("sub", "rcx, rax"),
    0x217AAE: ("mov", "rsi, qword ptr [rbp - 0x410]"),
    0x217AB9: ("movss", "xmm0, dword ptr [rsi + rdx]"),
    0x217ABE: ("movss", "xmm1, dword ptr [rip + 0x39073a]"),
    0x217AC6: ("ucomiss", "xmm1, xmm0"),
    0x217AC9: ("jb", "0x217bf8"),
    0x217AD2: ("ucomiss", "xmm0, dword ptr [rsi + rdx*4]"),
    0x217AD6: ("ja", "0x217bf8"),
    0x217AE3: ("test", "r12d, r12d"),
    0x217AE6: ("jle", "0x217aff"),
    0x217AE8: ("movss", "xmm0, dword ptr [rax + rdx*4]"),
    0x217AED: ("mulss", "xmm0, dword ptr [rip + 0x3bd85b]"),
    0x217AF5: ("ucomiss", "xmm0, dword ptr [rax + rcx*4]"),
    0x217AF9: ("jb", "0x217bf8"),
    0x217AFF: ("mov", "rax, qword ptr [rbp - 0x430]"),
    0x217B06: ("lea", "rcx, [rcx + rcx*2]"),
    0x217B0A: ("movsd", "xmm0, qword ptr [rax + rcx*8]"),
    0x217B31: ("lea", "rdi, [rbp - 0x5a0]"),
    0x217B3F: ("call", "0x218390"),
    0x217B62: ("call", "0x264980"),
    0x217BBE: ("call", "0xf33d0"),
}
RIP_TARGETS = {
    0x217ABE: (0x5A8200, 0.25),
    0x217AED: (0x5D5350, 0.800000011920929),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(blob: bytes, address: int) -> float:
    return struct.unpack_from("<f", blob, address)[0]


def decode(blob: bytes) -> dict[int, tuple[str, str, int | None]]:
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    instructions = {}
    for instruction in disassembler.disasm(
        blob[WINDOW_BEGIN:WINDOW_END], WINDOW_BEGIN
    ):
        rip_target = None
        for operand in instruction.operands:
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                rip_target = instruction.address + instruction.size + operand.mem.disp
        instructions[instruction.address] = (
            instruction.mnemonic,
            instruction.op_str,
            rip_target,
        )
    return instructions


def verify_static() -> None:
    blob = LIBCP.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    require(
        hashlib.sha256(blob[WINDOW_BEGIN:WINDOW_END]).hexdigest() == WINDOW_SHA256,
        "selection-window SHA drift",
    )
    instructions = decode(blob)
    for address, expected in ANCHORS.items():
        actual = instructions.get(address)
        require(actual is not None, f"missing instruction at 0x{address:x}")
        require(actual[:2] == expected, f"instruction drift at 0x{address:x}: {actual}")
    for address, (expected_target, expected_value) in RIP_TARGETS.items():
        actual = instructions[address]
        require(actual[2] == expected_target, f"RIP target drift at 0x{address:x}")
        require(
            f32(blob, expected_target) == expected_value,
            f"float constant drift at 0x{expected_target:x}",
        )


def branch_taken(branch: dict) -> bool:
    flags = branch["flags"]
    if branch["kind"] == "jb":
        return bool(flags["cf"])
    if branch["kind"] == "ja":
        return not flags["cf"] and not flags["zf"]
    raise AssertionError(f"unknown branch kind {branch['kind']}")


def rejection_reason(packet: dict) -> str:
    for branch in packet["branches"]:
        if branch["taken"]:
            return branch["name"]
    return "accepted"


def verify_packet(tier: str, packet: dict) -> None:
    ordinal = packet["ordinal"]
    prefix = f"{tier} packet {ordinal}"
    require(packet["consumer_libcp_va"] == 0x217A68, f"{prefix}: consumer VA")
    require(packet["finalized"] is True, f"{prefix}: not finalized")

    returns = packet["return_vector"]
    sides = packet["side_vector"]
    records = packet["candidate_records"]
    count = returns["count"]
    require(isinstance(count, int) and count > 0, f"{prefix}: bad count")
    require(sides["count"] == count, f"{prefix}: side count mismatch")
    require(records["count"] == count, f"{prefix}: record count mismatch")

    winner = packet["winner"]
    require(winner["computed"] is True, f"{prefix}: winner not computed")
    winner_index = winner["index"]
    require(0 <= winner_index < count, f"{prefix}: winner out of range")
    require(
        winner["score"]["address"] == returns["begin"] + 4 * winner_index,
        f"{prefix}: winner address mismatch",
    )
    require(
        packet["winner_side"]["address"] == sides["begin"] + 4 * winner_index,
        f"{prefix}: winner side address mismatch",
    )
    require(
        packet["selected_record"]["address"] == records["begin"] + 24 * winner_index,
        f"{prefix}: selected record address mismatch",
    )
    require(packet["selected_record"]["read_ok"] is True, f"{prefix}: selected record unreadable")

    center_index = packet["center_index"]
    require(0 <= center_index < count, f"{prefix}: center index out of range")
    require(
        packet["center_side"]["address"] == sides["begin"] + 4 * center_index,
        f"{prefix}: center side address mismatch",
    )
    require(
        packet["center_score"]["address"] == returns["begin"] + 4 * center_index,
        f"{prefix}: center score address mismatch",
    )

    branches = packet["branches"]
    require(branches and branches[0]["name"] == "side_max_reject", f"{prefix}: first branch")
    for branch in branches:
        require(
            branch["taken"] == branch_taken(branch),
            f"{prefix}: flag/branch mismatch at {branch['name']}",
        )

    taken = [branch for branch in branches if branch["taken"]]
    require(len(taken) <= 1, f"{prefix}: multiple rejection branches")
    observed_accepted = not taken
    require(
        packet["observed_accepted"] == observed_accepted,
        f"{prefix}: observed acceptance mismatch",
    )
    require(
        packet["predicted"]["accepted"] == observed_accepted,
        f"{prefix}: arithmetic prediction mismatch",
    )

    names = [branch["name"] for branch in branches]
    if packet["predicted"]["side_max_pass"]:
        require("center_side_reject" in names, f"{prefix}: center-side gate missing")
    if (
        packet["predicted"]["side_max_pass"]
        and packet["predicted"]["center_side_pass"]
        and packet["optional_gate_count"] > 0
    ):
        require("score_ratio_reject" in names, f"{prefix}: score-ratio gate missing")
    if packet["optional_gate_count"] <= 0:
        require("score_ratio_reject" not in names, f"{prefix}: unexpected score-ratio gate")

    if observed_accepted:
        require(packet["accepted_record_hit"] is True, f"{prefix}: accept site not hit")
        require(
            packet["accepted_winner_index_from_rcx"] == winner_index,
            f"{prefix}: accepted winner index mismatch",
        )
        require(packet["observed_f33d0_complete"] is True, f"{prefix}: f33d0 incomplete")
        require(packet["f33d0_call"]["libcp_va"] == 0x217BBE, f"{prefix}: f33d0 call VA")
        require(packet["f33d0_call"]["r8"] == 1, f"{prefix}: f33d0 r8")
        require(packet["f33d0_return"]["libcp_va"] == 0x217BC3, f"{prefix}: f33d0 return VA")
    else:
        require(packet["accepted_record_hit"] is False, f"{prefix}: rejected record materialized")
        require(packet["f33d0_call"] is None, f"{prefix}: rejected packet called f33d0")
        require(packet["f33d0_return"] is None, f"{prefix}: rejected packet returned from f33d0")


def verify_runtime() -> dict[str, dict]:
    summaries = {}
    for stem, label in RUNS:
        report_path = RUN_DIR / f"parent_decision_{stem}.json"
        output_path = RUN_DIR / f"parent_decision_{stem}.hdr"
        report = json.loads(report_path.read_text())
        require(report["process_exit_status"] == 0, f"{label}: process exit")
        require(report["drive_hit_step_cap"] is False, f"{label}: step cap")
        require(report["errors"] == [], f"{label}: probe errors")
        require(report["active"] == [], f"{label}: unfinished active frames")
        require(output_path.stat().st_size > 0, f"{label}: empty HDR output")

        packets = report["packets"]
        counts = report["counts"]
        require(len(packets) > 0, f"{label}: no packets")
        require(counts["packets_started"] == len(packets), f"{label}: started count")
        require(counts["packets_finalized"] == len(packets), f"{label}: finalized count")
        require(counts["consumer_hits"] == len(packets), f"{label}: consumer count")
        require(counts["cleanup_hits"] == len(packets), f"{label}: cleanup count")
        require(counts["unmatched_hits"] == 0, f"{label}: unmatched hits")

        for packet in packets:
            verify_packet(label, packet)

        accepted = sum(packet["observed_accepted"] for packet in packets)
        reasons = {}
        for packet in packets:
            reason = rejection_reason(packet)
            reasons[reason] = reasons.get(reason, 0) + 1
        require(accepted > 0, f"{label}: no accepted packet")
        require(counts["accepted_record_hits"] == accepted, f"{label}: accepted count")
        require(counts["f33d0_calls"] == accepted, f"{label}: f33d0 call count")
        require(counts["f33d0_returns"] == accepted, f"{label}: f33d0 return count")
        summaries[stem] = {
            "label": label,
            "packets": len(packets),
            "accepted": accepted,
            "reasons": reasons,
            "counts": sorted({packet["return_vector"]["count"] for packet in packets}),
        }
    return summaries


def main() -> None:
    verify_static()
    summaries = verify_runtime()
    print(
        f"static_parent_decision=OK libcp_sha256={LIBCP_SHA256} "
        f"window_sha256={WINDOW_SHA256}"
    )
    for stem, _label in RUNS:
        summary = summaries[stem]
        reasons = ",".join(f"{name}:{count}" for name, count in sorted(summary["reasons"].items()))
        print(
            f"{summary['label']}: packets={summary['packets']} accepted={summary['accepted']} "
            f"vector_counts={summary['counts']} outcomes={reasons}"
        )


if __name__ == "__main__":
    main()
