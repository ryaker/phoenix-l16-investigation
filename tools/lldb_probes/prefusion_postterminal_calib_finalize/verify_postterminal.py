#!/usr/bin/env python3
"""Verify the post-terminal calibration finalizer and overlay-route exclusion."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from capstone import CS_AC_WRITE, CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import (
    X86_INS_CALL,
    X86_INS_JMP,
    X86_OP_IMM,
    X86_OP_MEM,
    X86_OP_REG,
    X86_REG_RBP,
    X86_REG_RBX,
    X86_REG_RSP,
)


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs/prefusion_postterminal_calib_finalize"
CASES = ("unit1_35mm", "unit2_35mm")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u32(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def segments(data: bytes):
    require(u32(data) == 0xFEEDFACF, "libcp is not the pinned Mach-O")
    result = []
    offset = 32
    for _ in range(u32(data, 16)):
        command = u32(data, offset)
        size = u32(data, offset + 4)
        if command == 0x19:
            result.append(
                (
                    u64(data, offset + 24),
                    u64(data, offset + 32),
                    u64(data, offset + 40),
                    u64(data, offset + 48),
                )
            )
        offset += size
    return result


def file_offset(mapping, va: int) -> int:
    for vmaddr, vmsize, fileoff, filesize in mapping:
        if vmaddr <= va < vmaddr + vmsize:
            delta = va - vmaddr
            require(delta < filesize, f"VA 0x{va:x} outside file bytes")
            return fileoff + delta
    raise AssertionError(f"unmapped VA 0x{va:x}")


def bytes_at(data: bytes, mapping, va: int, size: int) -> bytes:
    offset = file_offset(mapping, va)
    result = data[offset : offset + size]
    require(len(result) == size, f"short read at 0x{va:x}")
    return result


def call_target(data: bytes, mapping, va: int) -> int:
    raw = bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify_replacement_constructor(data: bytes, mapping) -> tuple[str, str]:
    constructor = bytes_at(data, mapping, 0x239A90, 0x28)
    body = bytes_at(data, mapping, 0x2399A0, 0xE1)
    constructor_digest = hashlib.sha256(constructor).hexdigest()
    body_digest = hashlib.sha256(body).hexdigest()
    require(
        constructor_digest
        == "de1eb9c3a668ed7014c4ff7e3a99e8e07aad632beca2f31d3ee4d3f2de3a35f8",
        f"replacement constructor hash changed: {constructor_digest}",
    )
    require(
        body_digest
        == "46f06252560ef1638eebe13db828b33f7bced9e3758b2e4d37790d22998ae68b",
        f"replacement constructor body hash changed: {body_digest}",
    )

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    constructor_insns = list(decoder.disasm(constructor, 0x239A90))
    body_insns = list(decoder.disasm(body, 0x2399A0))
    require(
        constructor_insns
        and constructor_insns[-1].id == X86_INS_JMP
        and constructor_insns[-1].operands[0].type == X86_OP_IMM
        and constructor_insns[-1].operands[0].imm == 0x2399A0,
        "replacement constructor no longer tail-jumps to pinned body",
    )
    require(
        sum(insn.size for insn in constructor_insns) == len(constructor),
        "replacement constructor did not decode exactly",
    )
    require(
        sum(insn.size for insn in body_insns) == len(body),
        "replacement constructor body did not decode exactly",
    )

    call_targets = []
    field_writes = set()
    for insn in body_insns:
        if insn.id in (X86_INS_CALL, X86_INS_JMP):
            require(
                len(insn.operands) == 1 and insn.operands[0].type == X86_OP_IMM,
                f"indirect control transfer in constructor body at 0x{insn.address:x}",
            )
            call_targets.append(insn.operands[0].imm)
        for index, operand in enumerate(insn.operands):
            if (
                insn.address > 0x2399B8
                and operand.type == X86_OP_REG
                and operand.reg == X86_REG_RBX
            ):
                require(
                    not (operand.access & 1),
                    f"constructor copies this as a value at 0x{insn.address:x}",
                )
            if operand.type != X86_OP_MEM or not (operand.access & CS_AC_WRITE):
                continue
            if operand.mem.base == X86_REG_RBX:
                field_writes.add(operand.mem.disp)
                require(
                    index == 0,
                    f"unexpected this-relative write form at 0x{insn.address:x}",
                )
            else:
                require(
                    operand.mem.base in (X86_REG_RBP, X86_REG_RSP),
                    f"constructor writes outside this/stack at 0x{insn.address:x}",
                )
    require(
        set(call_targets) == {0x556314, 0x556320},
        f"replacement constructor body call targets changed: {call_targets}",
    )
    require(
        field_writes == {0, 8, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38},
        f"replacement constructor field writes changed: {sorted(field_writes)}",
    )
    return constructor_digest, body_digest


def verify_static() -> str:
    data = LIBCP.read_bytes()
    mapping = segments(data)
    expected = {
        0x2277B3: 0x22F0F0,
        0x2277C5: 0x227B00,
        0x3FE505: 0x227380,
        0x3FE538: 0x226240,
        0x3EB72D: 0x3F7040,
        0x22637F: 0x239A90,
        0x3FBCAE: 0x3FE820,
        0x3F7733: 0x22E9F0,
    }
    for call_va, target_va in expected.items():
        actual = call_target(data, mapping, call_va)
        require(
            actual == target_va,
            f"call 0x{call_va:x} -> 0x{actual:x}, expected 0x{target_va:x}",
        )
    require(
        bytes_at(data, mapping, 0x226388, 4) == bytes.fromhex("4d897e28"),
        "finalizer sibling store changed",
    )
    require(
        bytes_at(data, mapping, 0x3FE46F, 4) == bytes.fromhex("4c8b6708")
        and bytes_at(data, mapping, 0x3FE4D8, 8)
        == bytes.fromhex("4d8db42480020000"),
        "processing lambda State-root or finalizer-subobject derivation changed",
    )
    require(
        bytes_at(data, mapping, 0x3EB70F, 13)
        == bytes.fromhex("488b8570feffff488b3041b801"),
        "initResAmp State argument load changed",
    )
    require(
        bytes_at(data, mapping, 0x22EA9C, 12)
        == bytes.fromhex("498b5e2849c7462800000000"),
        "sibling destructor load/zero window changed",
    )
    require(
        u64(bytes_at(data, mapping, 0x65FFF8, 8)) == 0x3FE460,
        "ProcessingState lambda-7 vtable slot changed",
    )
    require(
        u64(bytes_at(data, mapping, 0x660018, 8)) == 0x60A170,
        "ProcessingState lambda-7 typeinfo-name pointer changed",
    )
    typeinfo_offset = file_offset(mapping, 0x60A170)
    typeinfo_name = data[typeinfo_offset : data.index(b"\0", typeinfo_offset)]
    require(
        typeinfo_name
        == b"NSt3__110__function6__funcIZZN2lt14StereoAsyncAPI5startEvENK3$_3clEiEUlvE7_NS_9allocatorIS5_EEFNS3_15ProcessingStateEvEEE",
        f"ProcessingState lambda-7 typeinfo changed: {typeinfo_name!r}",
    )
    window = bytes_at(data, mapping, 0x3FE460, 0xEF)
    digest = hashlib.sha256(window).hexdigest()
    require(
        digest == "7c98ec5f98ee6438614802c0915439fdd0f091dec27ccd03170c6c8ed7b062bd",
        f"processing-state lambda hash changed: {digest}",
    )
    for marker in (b"src_", b".jpg", b"overlay_hi.jpg", b"overlay_lo.jpg"):
        require(marker in data, f"missing installed diagnostic marker {marker!r}")
    constructor_digest, constructor_body_digest = verify_replacement_constructor(
        data, mapping
    )
    print(f"static_replacement_constructor={constructor_digest}")
    print(f"static_replacement_constructor_body={constructor_body_digest}")
    return digest


def pointer(snapshot) -> int:
    require(snapshot["read_ok"], "pointer snapshot read failed")
    return struct.unpack("<Q", bytes.fromhex(snapshot["hex"]))[0]


def verify_case(case: str) -> dict:
    packet = json.loads((RUN_DIR / f"{case}.json").read_text())
    require(packet["process_exit_status"] == 0, f"{case}: process exit")
    require(not packet["drive_hit_step_cap"], f"{case}: step cap")
    require(not packet["errors"], f"{case}: errors {packet['errors']}")
    require(len(packet["terminal_state_returns"]) == 1, f"{case}: state return count")
    terminal = packet["terminal_state_returns"][0]
    require(terminal["overlay_flag"]["hex"] == "00", f"{case}: overlay flag is active")
    require(not packet["overlay_entries"], f"{case}: diagnostic overlay route executed")
    require(
        len(packet["processing_lambda_post_calib"]) == 1,
        f"{case}: processing post-calib count",
    )
    finalizer_entries = [
        item
        for item in packet["finalizer_entries"]
        if len(item["stack"]) > 1
        and item["stack"][1].get("libcp_va") == 0x3FE53D
    ]
    require(len(finalizer_entries) == 1, f"{case}: finalizer entry count")
    require(
        len(packet["processing_lambda_post_finalize"]) == 1,
        f"{case}: processing post-finalize count",
    )
    require(
        len(packet["processing_machine_returns"]) == 1,
        f"{case}: processing machine return count",
    )
    before = packet["processing_lambda_post_calib"][0]
    entry = finalizer_entries[0]
    after = packet["processing_lambda_post_finalize"][0]
    require(
        before["owner"] == entry["owner"] == after["owner"],
        f"{case}: finalizer owner identity",
    )
    state_root = before["state_root"]
    require(
        before["owner"] == state_root + 0x280,
        f"{case}: finalizer subobject is not State+0x280",
    )
    require(entry["overlay_flag"]["hex"] == "00", f"{case}: finalizer flag")
    require(
        before["sibling_before"]["hex"] == entry["sibling_before"]["hex"],
        f"{case}: pre-finalizer sibling identity",
    )
    require(
        after["sibling_after"]["read_ok"],
        f"{case}: post-finalizer sibling read",
    )
    sibling_before = pointer(entry["sibling_before"])
    sibling_after = pointer(after["sibling_after"])
    require(sibling_after != 0, f"{case}: null finalized sibling")
    require(sibling_after != sibling_before, f"{case}: finalizer did not replace sibling")
    armed = packet["sibling_watch_armed"]
    samples = packet["sibling_watch_samples"]
    require(packet["sibling_watchpoint_id"] is not None, f"{case}: no sibling watchpoint")
    require(armed["owner"] == entry["owner"], f"{case}: watched owner identity")
    require(
        pointer(armed["value_at_arm"]) == sibling_after,
        f"{case}: watched finalized pointer identity",
    )
    require(len(samples) == 2, f"{case}: unexpected sibling watch stop count")
    first, second = samples
    require(
        first["libcp_va"] == 0x22EAA0 and first["changed"] is False,
        f"{case}: first sibling touch is not pre-destructor store",
    )
    require(
        first["value_now"]["hex"] == armed["value_at_arm"]["hex"],
        f"{case}: finalized pointer changed before destructor store",
    )
    require(
        second["libcp_va"] == 0x22EAA8 and second["changed"] is True,
        f"{case}: second sibling touch is not post-destructor store",
    )
    require(
        second["value_now"]["hex"] == "0000000000000000",
        f"{case}: destructor did not clear sibling slot",
    )
    require(
        0x3F7738 in {row.get("libcp_va") for row in second["stack"]},
        f"{case}: sibling cleanup caller ancestry",
    )
    matching_joins = [
        item
        for item in packet["initresamp_state_joins"]
        if item["state_root_argument"] == state_root
    ]
    require(matching_joins, f"{case}: no initResAmp join for terminal State root")
    require(
        min(item["sequence"] for item in matching_joins) > after["sequence"],
        f"{case}: initResAmp State use did not follow terminal finalization",
    )
    for item in matching_joins:
        require(
            pointer(item["pipeline_state_slot"]) == state_root,
            f"{case}: PipelineCache+0x180 does not retain terminal State root",
        )
        require(
            item["state_root_argument"] != sibling_after,
            f"{case}: finalized sibling was passed as the record-builder State",
        )
    hdr = RUN_DIR / f"{case}.hdr"
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{case}: invalid HDR")
    return {
        "owner": entry["owner"],
        "state_root": state_root,
        "sibling_before": sibling_before,
        "sibling_after": sibling_after,
        "first_touch": first["libcp_va"],
        "initresamp_join_count": len(matching_joins),
    }


def main() -> int:
    digest = verify_static()
    print(f"static_postterminal_calib_finalize={digest}")
    for case in CASES:
        summary = verify_case(case)
        print(
            f"{case}=OK owner=0x{summary['owner']:x} overlay_hits=0 "
            f"sibling=0x{summary['sibling_before']:x}->0x{summary['sibling_after']:x}"
        )
    print("postterminal_calib_finalize=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
