#!/usr/bin/env python3
"""Verify the installed numeric CalibStage mapping and two-body bank behavior."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import (
    X86_INS_CALL,
    X86_OP_IMM,
    X86_OP_MEM,
    X86_REG_RIP,
)


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
TEXT_BEGIN = 0x2250
TEXT_END = 0x555D20
F33D0 = 0xF33D0

F33D0_CALLS = {
    0x1F1328: 0,
    0x1F134B: 1,
    0x21159C: 1,
    0x217BBE: 1,
    0x22BB23: 1,
    0x22DF45: 1,
    0x22E755: 1,
    0x23D38D: 1,
    0x3F95D6: 1,
    0x3FA84A: 1,
}

SELECTOR_SETUP = {
    0x1F1322: ("xor", "r8d, r8d"),
    0x1F1342: ("mov", "r8d, 1"),
    0x211593: ("mov", "r8d, 1"),
    0x217BB1: ("mov", "r8d, 1"),
    0x22BB10: ("mov", "r8d, 1"),
    0x22DF32: ("mov", "r8d, 1"),
    0x22E745: ("mov", "r8d, 1"),
    0x23D372: ("mov", "r8d, 1"),
    0x3F95B8: ("mov", "r8d, 1"),
    0x3FA830: ("mov", "r8d, 1"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def decoder() -> Cs:
    result = Cs(CS_ARCH_X86, CS_MODE_64)
    result.detail = True
    return result


def instruction(blob: bytes, va: int):
    return next(decoder().disasm(blob[va : va + 16], va))


def direct_call_target(item) -> int:
    require(item.id == X86_INS_CALL, f"0x{item.address:x}: expected call")
    require(
        len(item.operands) == 1 and item.operands[0].type == X86_OP_IMM,
        f"0x{item.address:x}: expected direct call",
    )
    return item.operands[0].imm


def rip_target(item, operand_index: int) -> int:
    operand = item.operands[operand_index]
    require(
        operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP,
        f"0x{item.address:x}: expected RIP-relative operand",
    )
    return item.address + item.size + operand.mem.disp


def cstring(blob: bytes, va: int) -> str:
    end = blob.index(b"\0", va)
    return blob[va:end].decode("ascii")


def verify_static(blob: bytes) -> None:
    digest = hashlib.sha256(blob).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")

    disassembler = decoder()
    disassembler.skipdata = True
    xrefs = []
    for item in disassembler.disasm(blob[TEXT_BEGIN:TEXT_END], TEXT_BEGIN):
        if item.id == 0:
            continue
        immediate = any(
            operand.type == X86_OP_IMM and operand.imm == F33D0
            for operand in item.operands
        )
        rip_relative = any(
            operand.type == X86_OP_MEM
            and operand.mem.base == X86_REG_RIP
            and item.address + item.size + operand.mem.disp == F33D0
            for operand in item.operands
        )
        if immediate or rip_relative:
            xrefs.append(item)

    require(
        {item.address for item in xrefs} == set(F33D0_CALLS),
        "complete f33d0 code-reference census changed",
    )
    require(
        all(direct_call_target(item) == F33D0 for item in xrefs),
        "f33d0 is now addressed by a non-call reference",
    )
    require(
        blob.find(F33D0.to_bytes(8, "little")) == -1,
        "absolute f33d0 pointer appeared in installed bytes",
    )

    for va, expected_selector in F33D0_CALLS.items():
        require(
            direct_call_target(instruction(blob, va)) == F33D0,
            f"f33d0 call at 0x{va:x} changed",
        )
        require(expected_selector in (0, 1), "invalid expected selector")
    for va, expected in SELECTOR_SETUP.items():
        item = instruction(blob, va)
        require(
            (item.mnemonic, item.op_str) == expected,
            f"selector setup at 0x{va:x} changed: {item.mnemonic} {item.op_str}",
        )

    error_xref = instruction(blob, 0xF34AC)
    error_va = rip_target(error_xref, 1)
    require(
        cstring(blob, error_va) == "wrong CalibStage, must be factory or current",
        "installed CalibStage names changed",
    )

    accessor = {
        0xF34E4: ("lea", "rax, [rdi + 0x12c]"),
        0xF34EB: ("lea", "rcx, [rdi + 0x180]"),
        0xF34F2: ("cmp", "esi, 1"),
        0xF34F5: ("cmovne", "rax, rcx"),
        0x264440: ("push", "rbp"),
        0x264441: ("mov", "rbp, rsp"),
        0x264444: ("mov", "edx, 1"),
        0x26444A: ("jmp", "0x264270"),
    }
    for va, expected in accessor.items():
        item = instruction(blob, va)
        require(
            (item.mnemonic, item.op_str) == expected,
            f"accessor/wrapper instruction at 0x{va:x} changed",
        )

    require(
        hashlib.sha256(blob[0xF33D0:0xF349D]).hexdigest()
        == "ce947e1ecadeca1e37461eee9394c61e948ae7a86a84b71c6e39e557ae1656a8",
        "f33d0 selector-copy body changed",
    )
    require(
        hashlib.sha256(blob[0xF3E10:0xF3F73]).hexdigest()
        == "29a0ab9296d14b0b29978011fe09633a3495f4beb881065a584e1790a8561460",
        "f3e10 two-bank consumer changed",
    )


def source_packet(row: dict) -> tuple[str, str, str]:
    data = row["f33d0"]
    return (
        data["src1_raw_0x00_0x24"],
        data["src2_raw_0x00_0x24"],
        data["triple_raw_0x00_0x0c"],
    )


def verify_constructor_reports() -> int:
    run_dir = ROOT / "runs/state_helpers_23c5f0_f33d0_runtime"
    total_pairs = 0
    for focal in ("28mm", "35mm", "70mm", "150mm"):
        path = run_dir / f"state_helper_{focal}.json"
        packet = json.loads(path.read_text())
        require(packet["process"]["exit_status"] == 0, f"{focal}: process exit")
        require(not packet["errors"], f"{focal}: probe errors")
        require(not packet["drive_hit_step_cap"], f"{focal}: step cap")

        initialization = []
        for event in packet["events"]:
            data = event.get("f33d0")
            if not data:
                continue
            caller_va = event["stack"][1]["libcp_va"]
            if caller_va in (0x1F132D, 0x1F1350):
                initialization.append(event)
        stage0 = [row for row in initialization if row["f33d0"]["selector_r8d"] == 0]
        stage1 = [row for row in initialization if row["f33d0"]["selector_r8d"] == 1]
        require(len(stage0) == 10 and len(stage1) == 10, f"{focal}: init count")

        by_object_0 = {row["f33d0"]["dest_rdi"]: row for row in stage0}
        by_object_1 = {row["f33d0"]["dest_rdi"]: row for row in stage1}
        require(by_object_0.keys() == by_object_1.keys(), f"{focal}: init objects")
        for object_address in by_object_0:
            require(
                source_packet(by_object_0[object_address])
                == source_packet(by_object_1[object_address]),
                f"{focal}: unequal paired init source",
            )
        total_pairs += len(stage0)
    return total_pairs


def expected_bank_hex(packet: dict, prefix: str) -> str:
    return (
        packet[f"{prefix}_1_snapshot"]["hex"]
        + packet[f"{prefix}_2_snapshot"]["hex"]
        + packet[f"{prefix}_3_snapshot"]["hex"]
    )


def verify_existing_mutation_reports() -> None:
    unit1 = json.loads(
        (
            ROOT
            / "runs/prefusion_264270_output_watch/output_watch_35mm.json"
        ).read_text()
    )
    require(unit1["process_exit_status"] == 0, "Unit-1 mutation process exit")
    require(not unit1["errors"], "Unit-1 mutation probe errors")
    require(not unit1["drive_hit_step_cap"], "Unit-1 mutation step cap")
    transfer = unit1["wide_calib_transfer"]
    require(transfer["selector"] == 1, "Unit-1 transfer selector")
    require(
        transfer["bank_before"]["hex"] != transfer["bank_after"]["hex"],
        "Unit-1 selector-1 transfer did not change bank",
    )
    normalized = unit1["terminal_normalized_pipeline"]
    require(normalized["f33d0_selector"] == 1, "Unit-1 normalized selector")
    require(
        normalized["f33d0_bank_before"]["hex"]
        != normalized["f33d0_bank_after"]["hex"],
        "Unit-1 selector-1 normalized write did not change bank",
    )
    require(
        normalized["f33d0_bank_after"]["hex"]
        == expected_bank_hex(normalized, "f33d0_source"),
        "Unit-1 normalized selector-1 copy mismatch",
    )

    unit2 = json.loads(
        (
            ROOT
            / "runs/prefusion_216f60_accepted_bank_consumer/"
            "accepted_bank_consumer_unit2_35mm.json"
        ).read_text()
    )
    require(unit2["process_exit_status"] == 0, "Unit-2 mutation process exit")
    require(not unit2["errors"], "Unit-2 mutation probe errors")
    require(not unit2["drive_hit_step_cap"], "Unit-2 mutation step cap")
    require(
        unit2["f33d0_calls"]
        and all(row["selector"] == 1 for row in unit2["f33d0_calls"]),
        "Unit-2 accepted-bank selector",
    )
    require(
        all(row["exact_copy_match"] for row in unit2["f33d0_returns"]),
        "Unit-2 selector-1 exact-copy mismatch",
    )
    semantic_changes = [
        row
        for row in unit2["watch_samples"]
        if row["changed"] and row["libcp_va"] == 0xF345E
    ]
    require(len(semantic_changes) == 1, "Unit-2 selector-1 mutation discriminator")


def verify_bank_watch_reports() -> str:
    run_dir = ROOT / "runs/calibstage_public_names"
    summaries = []
    total_current_writes = 0
    for unit in ("unit1", "unit2"):
        packet = json.loads((run_dir / f"{unit}_35mm.json").read_text())
        require(packet["process_exit_status"] == 0, f"{unit}: process exit")
        require(not packet["errors"], f"{unit}: probe errors")
        require(not packet["drive_hit_step_cap"], f"{unit}: step cap")
        require(packet["tracked_camera_id"] == 5, f"{unit}: camera id")
        require(packet["initial"]["banks_equal"], f"{unit}: unequal initial banks")
        require(len(packet["watchpoints"]) == 2, f"{unit}: watchpoint count")

        semantic = [row for row in packet["events"] if row["libcp_va"] is not None]
        factory = [
            row for row in semantic if row["bank"] == "factory_candidate"
        ]
        current = [
            row for row in semantic if row["bank"] == "current_candidate"
        ]
        require(not factory, f"{unit}: selector-0 bank changed in libcp")
        if current:
            require(
                any(row["libcp_va"] == 0xF345E for row in current),
                f"{unit}: selector-1 write was not f33d0",
            )
        total_current_writes += len(current)
        summaries.append(
            f"{unit}:current_writes={len(current)},factory_writes=0"
        )
    require(total_current_writes >= 1, "two-body watch saw no selector-1 mutation")
    return ",".join(summaries)


def main() -> None:
    blob = LIBCP.read_bytes()
    verify_static(blob)
    pairs = verify_constructor_reports()
    verify_existing_mutation_reports()
    watch_summary = verify_bank_watch_reports()
    print(
        "calibstage_public_names=OK "
        "mapping=0:factory@+0x180,1:current@+0x12c "
        f"paired_initializations={pairs} {watch_summary}"
    )


if __name__ == "__main__":
    main()
