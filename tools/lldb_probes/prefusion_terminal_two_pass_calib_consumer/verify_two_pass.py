#!/usr/bin/env python3
"""Verify terminal helper pass 2 consumes pass-1 normalized CalibStage banks."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs/prefusion_terminal_two_pass_calib_consumer"
CASES = ("unit1_35mm", "unit2_35mm")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u32(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def segments(data: bytes) -> list[tuple[int, int, int, int]]:
    require(u32(data) == 0xFEEDFACF, "libcp is not the pinned 64-bit Mach-O")
    out = []
    offset = 32
    for _ in range(u32(data, 16)):
        command = u32(data, offset)
        size = u32(data, offset + 4)
        if command == 0x19:
            out.append(
                (
                    u64(data, offset + 24),
                    u64(data, offset + 32),
                    u64(data, offset + 40),
                    u64(data, offset + 48),
                )
            )
        offset += size
    require(out, "no Mach-O segments found")
    return out


def file_offset(mapping, va: int) -> int:
    for vmaddr, vmsize, fileoff, filesize in mapping:
        if vmaddr <= va < vmaddr + vmsize:
            delta = va - vmaddr
            require(delta < filesize, f"VA 0x{va:x} is outside file bytes")
            return fileoff + delta
    raise AssertionError(f"VA 0x{va:x} is unmapped")


def bytes_at(data: bytes, mapping, va: int, size: int) -> bytes:
    offset = file_offset(mapping, va)
    result = data[offset : offset + size]
    require(len(result) == size, f"short read at 0x{va:x}")
    return result


def call_target(data: bytes, mapping, va: int) -> int:
    raw = bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify_static() -> str:
    data = LIBCP.read_bytes()
    mapping = segments(data)
    expected_calls = {
        0x22E244: 0x23C5F0,
        0x22E283: 0x23C5F0,
        0x23C6C0: 0x264440,
        0x23CBA6: 0x264440,
        0x23D226: 0x264440,
        0x23D38D: 0x0F33D0,
    }
    for call_va, expected in expected_calls.items():
        actual = call_target(data, mapping, call_va)
        require(
            actual == expected,
            f"call 0x{call_va:x} -> 0x{actual:x}, expected 0x{expected:x}",
        )
    window = bytes_at(data, mapping, 0x22E20E, 0x7A)
    digest = hashlib.sha256(window).hexdigest()
    require(
        digest == "8cbfdfb06337fa3a47975a4c72e2fa42149d04729aa2d4567afa2e589ea2a171",
        f"terminal two-call window hash changed: {digest}",
    )
    require(
        bytes_at(data, mapping, 0x264440, 14)
        == bytes.fromhex("554889e5ba010000005de921feff"),
        "0x264440 selector-1 tail-wrapper bytes changed",
    )
    return digest


def decode_key(snapshot) -> int:
    require(snapshot["read_ok"], "key snapshot read failed")
    return struct.unpack("<I", bytes.fromhex(snapshot["hex"]))[0]


def verify_case(case: str) -> dict:
    path = RUN_DIR / f"{case}.json"
    require(path.exists(), f"{case}: missing {path}")
    packet = json.loads(path.read_text())
    require(packet["process_exit_status"] == 0, f"{case}: process did not exit 0")
    require(not packet["drive_hit_step_cap"], f"{case}: drive hit step cap")
    require(not packet["errors"], f"{case}: probe errors: {packet['errors']}")
    require(not packet["active_by_thread"], f"{case}: active helper left at exit")
    require(
        not packet["pending_write_by_thread"],
        f"{case}: pending normalized write left at exit",
    )

    entries = packet["helper_entries"]
    returns = packet["helper_returns"]
    require(
        [item["call_ordinal"] for item in entries] == [1, 2],
        f"{case}: terminal helper entry order/count changed",
    )
    require(
        [item["call_ordinal"] for item in returns] == [1, 2],
        f"{case}: terminal helper return order/count changed",
    )
    first, second = entries
    for register in ("arg_rdi", "arg_rsi", "arg_rdx", "arg_rcx", "arg_r8", "arg_r9"):
        require(
            first[register] == second[register],
            f"{case}: helper argument {register} differs between passes",
        )
    require(first["arg_r8"] == 1 and first["arg_r9"] == 11, f"{case}: constants changed")

    reads = packet["assembly_reads"]
    first_reads = [item for item in reads if item["call_ordinal"] == 1]
    second_reads = [item for item in reads if item["call_ordinal"] == 2]
    require(
        len(first_reads) == len(second_reads) == 19,
        f"{case}: expected 19 assembly reads in each terminal pass",
    )
    expected_route = (
        [(0x23C6C0, 0)]
        + [(0x23CBA6, key) for key in range(1, 10)]
        + [(0x23D226, key) for key in range(1, 10)]
    )
    actual_route = [
        (item["callsite_libcp_va"], decode_key(item["source_key"]))
        for item in first_reads
    ]
    require(actual_route == expected_route, f"{case}: pass-1 keyed route changed")
    changed_bank_count = 0
    for first_read, second_read in zip(first_reads, second_reads):
        require(
            first_read["callsite_libcp_va"] == second_read["callsite_libcp_va"],
            f"{case}: assembly callsite order differs between passes",
        )
        require(
            first_read["source_object"] == second_read["source_object"],
            f"{case}: source object identity differs between passes",
        )
        require(
            first_read["source_key"]["hex"] == second_read["source_key"]["hex"],
            f"{case}: source key differs between passes",
        )
        require(
            first_read["selector"] == second_read["selector"] == 1,
            f"{case}: selector-1 wrapper changed",
        )
        changed_bank_count += (
            first_read["source_bank"]["hex"] != second_read["source_bank"]["hex"]
        )

    writes = packet["normalized_writes"]
    first_writes = [item for item in writes if item["call_ordinal"] == 1]
    second_writes = [item for item in writes if item["call_ordinal"] == 2]
    for item in writes:
        require(item["selector"] == 1, f"{case}: normalized selector is not 1")
        require(item["exact_source_copy"], f"{case}: f33d0 source-copy mismatch")
        require(
            decode_key(item["destination_key"]) == decode_key(item["local_key"]),
            f"{case}: destination/local key mismatch",
        )

    matching_reads = []
    if first_writes:
        snapshots = packet["second_entry_snapshots"]
        require(
            len(snapshots) == len(first_writes),
            f"{case}: incomplete second-entry snapshot census",
        )
        require(
            all(item["exact_match"] for item in snapshots),
            f"{case}: pass-1 bank changed before pass 2",
        )
        matching_reads = [
            item
            for item in reads
            if item["call_ordinal"] == 2 and item["matches_first_write"]
        ]
        matched_objects = {item["source_object"] for item in matching_reads}
        first_objects = {item["destination_object"] for item in first_writes}
        require(
            matched_objects == first_objects,
            f"{case}: pass-2 read coverage does not equal pass-1 write objects",
        )

    hdr = RUN_DIR / f"{case}.hdr"
    require(hdr.exists(), f"{case}: missing HDR output")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{case}: invalid HDR output")
    keys = sorted(decode_key(item["destination_key"]) for item in first_writes)
    return {
        "first_write_count": len(first_writes),
        "second_write_count": len(second_writes),
        "matching_read_count": len(matching_reads),
        "keys": keys,
        "changed_bank_count": changed_bank_count,
    }


def main() -> int:
    digest = verify_static()
    summaries = {case: verify_case(case) for case in CASES}
    print(f"static_terminal_two_pass={digest}")
    for case, summary in summaries.items():
        print(
            f"{case}=OK first_writes={summary['first_write_count']} "
            f"second_writes={summary['second_write_count']} "
            f"pass2_exact_reads={summary['matching_read_count']} "
            f"changed_banks_between_passes={summary['changed_bank_count']} "
            f"write_keys={summary['keys']}"
        )
    print("terminal_two_pass_calib_consumer=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
