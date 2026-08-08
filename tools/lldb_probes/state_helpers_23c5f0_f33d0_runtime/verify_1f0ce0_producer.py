#!/usr/bin/env python3
"""Verify the constructor-side 0x1f0ce0 -> 0xf33d0 producer edge.

This checker keeps the result intentionally narrow:

- static installed-bundle bytes show 0x1f0ce0 calls 0xf33d0 twice with
  selector 0 then selector 1 after a f3350 scale-field access window;
- existing four-zoom runtime packets show those two calls copy the same
  source records into both CalibStage banks for each captured key;
- public fixed32 sequence indexing admits direct A-bank K/pose copies and
  B4/C5 pose copies, while B4/C5 K packets are zoom-variant and not exact
  public fixed32-sequence copies.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import lane_b_index5_public_meaning_audit as audit  # noqa: E402


LIBCP_DYLIB = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)

PRODUCER_RETURNS = {
    0x1F132D: 0,
    0x1F1350: 1,
}

EXPECTED_PRODUCER_KEYS = {
    "28mm": list(range(0, 10)),
    "35mm": list(range(0, 10)),
    "70mm": list(range(5, 15)),
    "150mm": list(range(5, 15)),
}

EXPECTED_FULL_PUBLIC_KEYS = {
    "28mm": set(range(0, 5)),
    "35mm": set(range(0, 5)),
    "70mm": set(),
    "150mm": set(),
}

EXPECTED_POSE_ONLY_KEYS = {
    "28mm": {8},
    "35mm": {8},
    "70mm": {8, 14},
    "150mm": {8, 14},
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier: str) -> None:
    hdr = ROOT / "runs/state_helpers_23c5f0_f33d0_runtime" / f"state_helper_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def camera_names(keys) -> str:
    return ",".join(audit.CAMERA_NAMES[key] for key in sorted(keys)) or "none"


def read_u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def read_u64(data: bytes, off: int) -> int:
    return struct.unpack_from("<Q", data, off)[0]


def macho_segments(data: bytes) -> list[tuple[int, int, int, int]]:
    magic = read_u32(data, 0)
    require(magic == 0xFEEDFACF, "libcp is not a 64-bit little-endian Mach-O")
    ncmds = read_u32(data, 16)
    off = 32
    segments = []
    for _ in range(ncmds):
        cmd = read_u32(data, off)
        cmdsize = read_u32(data, off + 4)
        if cmd == 0x19:  # LC_SEGMENT_64
            vmaddr = read_u64(data, off + 24)
            vmsize = read_u64(data, off + 32)
            fileoff = read_u64(data, off + 40)
            filesize = read_u64(data, off + 48)
            segments.append((vmaddr, vmsize, fileoff, filesize))
        off += cmdsize
    require(segments, "no LC_SEGMENT_64 commands found")
    return segments


def va_to_fileoff(segments: list[tuple[int, int, int, int]], va: int) -> int:
    for vmaddr, vmsize, fileoff, filesize in segments:
        if vmaddr <= va < vmaddr + vmsize:
            delta = va - vmaddr
            require(delta < filesize, f"VA 0x{va:x} falls outside segment file bytes")
            return fileoff + delta
    raise AssertionError(f"VA 0x{va:x} not mapped by Mach-O segments")


def bytes_at(data: bytes, segments: list[tuple[int, int, int, int]], va: int, size: int) -> bytes:
    off = va_to_fileoff(segments, va)
    out = data[off : off + size]
    require(len(out) == size, f"short read at VA 0x{va:x}")
    return out


def call_target(data: bytes, segments: list[tuple[int, int, int, int]], va: int) -> int:
    raw = bytes_at(data, segments, va, 5)
    require(raw[0] == 0xE8, f"VA 0x{va:x} is not a direct call")
    disp = struct.unpack_from("<i", raw, 1)[0]
    return (va + 5 + disp) & 0xFFFFFFFFFFFFFFFF


def validate_static_producer_edge() -> str:
    data = LIBCP_DYLIB.read_bytes()
    segments = macho_segments(data)
    expected_calls = {
        0x1F0CF3: 0x0F3360,
        0x1F0D31: 0x1F0B00,
        0x1F0E15: 0x0F3300,
        0x1F0E2A: 0x1F96E0,
        0x1F0FF0: 0x0F3350,
        0x1F1072: 0x1F0A00,
        0x1F1090: 0x0F32F0,
        0x1F109C: 0x1C1860,
        0x1F10B2: 0x1C79E0,
        0x1F1328: 0x0F33D0,
        0x1F134B: 0x0F33D0,
    }
    for call_va, target_va in expected_calls.items():
        actual = call_target(data, segments, call_va)
        require(actual == target_va, f"call 0x{call_va:x} -> 0x{actual:x}, expected 0x{target_va:x}")

    require(bytes_at(data, segments, 0x1F1322, 3) == b"\x45\x31\xc0", "selector-0 r8d setup changed")
    require(
        bytes_at(data, segments, 0x1F1342, 6) == b"\x41\xb8\x01\x00\x00\x00",
        "selector-1 r8d setup changed",
    )
    require(
        bytes_at(data, segments, 0x1F0FF5, 5) == b"\xf3\x0f\x10\x40\x18",
        "f3350 scale-x load window changed",
    )
    require(
        bytes_at(data, segments, 0x1F0FFA, 5) == b"\xf3\x0f\x10\x48\x1c",
        "f3350 scale-y load window changed",
    )
    expected_byte_windows = {
        0x1F0FFF: (bytes.fromhex("f30f109548ffffff"), "load K[0] from rbp-0xb8"),
        0x1F1007: (bytes.fromhex("f30f59d0"), "multiply K[0] by scale x"),
        0x1F100B: (bytes.fromhex("f30f119548ffffff"), "store scaled K[0] to rbp-0xb8"),
        0x1F1013: (bytes.fromhex("f30f109558ffffff"), "load K[4] from rbp-0xa8"),
        0x1F101B: (bytes.fromhex("f30f59d1"), "multiply K[4] by scale y"),
        0x1F101F: (bytes.fromhex("f30f119558ffffff"), "store scaled K[4] to rbp-0xa8"),
        0x1F1027: (bytes.fromhex("f30f598550ffffff"), "multiply K[2] by scale x"),
        0x1F102F: (bytes.fromhex("f30f118550ffffff"), "store scaled K[2] to rbp-0xb0"),
        0x1F1037: (bytes.fromhex("f30f598d5cffffff"), "multiply K[5] by scale y"),
        0x1F103F: (bytes.fromhex("f30f118d5cffffff"), "store scaled K[5] to rbp-0xa4"),
        0x1F130D: (bytes.fromhex("488db548ffffff"), "selector-0 K source is rbp-0xb8"),
        0x1F1314: (bytes.fromhex("488d9588fdffff"), "selector-0 pose source is rbp-0x278"),
        0x1F131B: (bytes.fromhex("488d8d78fdffff"), "selector-0 triple source is rbp-0x288"),
        0x1F132D: (bytes.fromhex("488db548ffffff"), "selector-1 K source is rbp-0xb8"),
        0x1F1334: (bytes.fromhex("488d9588fdffff"), "selector-1 pose source is rbp-0x278"),
        0x1F133B: (bytes.fromhex("488d8d78fdffff"), "selector-1 triple source is rbp-0x288"),
    }
    for va, (expected, label) in expected_byte_windows.items():
        actual = bytes_at(data, segments, va, len(expected))
        require(actual == expected, f"{label} window changed at 0x{va:x}")
    return "static_1f0ce0_calls_and_selector_setup=OK"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def process_ok(packet: dict, label: str) -> None:
    audit.validate_process(packet, label)


def caller_return(event: dict) -> int | None:
    stack = event.get("stack") or []
    if len(stack) < 2:
        return None
    return stack[1].get("libcp_va")


def raw_records(event: dict) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    src1, src2, triple = audit._calib_record_raw_from_f33d0(event)
    return tuple(src1), tuple(src2), tuple(triple)


def raw_to_floats(raw_values: tuple[int, ...]) -> list[float]:
    return [struct.unpack("<f", struct.pack("<I", raw & 0xFFFFFFFF))[0] for raw in raw_values]


def validate_k_shape(raw_values: tuple[int, ...], tier: str, key: int) -> None:
    require(len(raw_values) == 9, f"{tier} {audit.CAMERA_NAMES[key]}: K record length")
    floats = raw_to_floats(raw_values)
    for index in (1, 3, 6, 7):
        require(raw_values[index] == 0, f"{tier} {audit.CAMERA_NAMES[key]}: K off-axis field {index} not zero")
    require(raw_values[8] == 0x3F800000, f"{tier} {audit.CAMERA_NAMES[key]}: K homogeneous field not 1.0")
    require(raw_values[0] == raw_values[4], f"{tier} {audit.CAMERA_NAMES[key]}: fx/fy raw fields differ")
    require(all(math.isfinite(value) for value in floats), f"{tier} {audit.CAMERA_NAMES[key]}: non-finite K")
    require(floats[0] > 0 and floats[2] > 0 and floats[5] > 0, f"{tier} {audit.CAMERA_NAMES[key]}: nonpositive K")


def validate_tier(tier: str):
    packet = load_json(
        ROOT / "runs/state_helpers_23c5f0_f33d0_runtime" / f"state_helper_{tier}.json"
    )
    process_ok(packet, f"{tier} state_helpers_23c5f0_f33d0_runtime")
    require_hdr_output(tier)
    events = [
        event
        for event in packet["events"]
        if event.get("site_va") == 0x0F33D0 and caller_return(event) in PRODUCER_RETURNS
    ]
    require(len(events) == 20, f"{tier}: expected 20 producer f33d0 events")

    by_selector = {0: {}, 1: {}}
    for event in events:
        ret = caller_return(event)
        expected_selector = PRODUCER_RETURNS[ret]
        selector = event["f33d0"]["selector_r8d"]
        require(selector == expected_selector, f"{tier}: selector/caller mismatch")
        key = event["f33d0"]["dest_i32_0x60"]
        require(event["f33d0"]["dest_i32_0x64"] == 0, f"{tier}: dest+0x64 changed")
        require(event["f33d0"]["dest_u8_0x30"] == 1, f"{tier}: dest+0x30 changed")
        require(key not in by_selector[selector], f"{tier}: duplicate key in selector {selector}")
        by_selector[selector][key] = raw_records(event)
        validate_k_shape(by_selector[selector][key][0], tier, key)

    expected_keys = EXPECTED_PRODUCER_KEYS[tier]
    for selector in (0, 1):
        require(sorted(by_selector[selector]) == expected_keys, f"{tier}: selector {selector} key set mismatch")

    same_source_pairs = 0
    for key in expected_keys:
        require(by_selector[0][key] == by_selector[1][key], f"{tier}: selector records differ for key {key}")
        same_source_pairs += 1

    seq_index = audit.public_calibration_fixed32_sequence_index(tier)
    full_public = set()
    pose_public = set()
    k_public = set()
    for key, records in by_selector[0].items():
        k_raw, rotation_raw, translation_raw = records
        if k_raw in seq_index:
            k_public.add(key)
        if rotation_raw in seq_index and translation_raw in seq_index:
            pose_public.add(key)
        if k_raw in seq_index and rotation_raw in seq_index and translation_raw in seq_index:
            full_public.add(key)

    require(full_public == EXPECTED_FULL_PUBLIC_KEYS[tier], f"{tier}: full-public key set mismatch")
    require(k_public == EXPECTED_FULL_PUBLIC_KEYS[tier], f"{tier}: K-public key set mismatch")
    require(
        EXPECTED_POSE_ONLY_KEYS[tier] <= (pose_public - k_public),
        f"{tier}: expected pose-only keys missing",
    )

    return {
        "tier": tier,
        "selector_pair_source_equal": same_source_pairs,
        "records": by_selector[0],
        "full_public": full_public,
        "pose_only": pose_public - k_public,
        "k_not_public": set(expected_keys) - k_public,
    }


def validate_cross_tier(results: dict[str, dict]) -> str:
    b4 = {
        tier: results[tier]["records"][8]
        for tier in ("28mm", "35mm", "70mm", "150mm")
    }
    b4_k_variants = {records[0] for records in b4.values()}
    b4_pose_variants = {(records[1], records[2]) for records in b4.values()}
    require(len(b4_k_variants) == 4, "B4 K should vary across the four focal tiers")
    require(len(b4_pose_variants) == 1, "B4 pose should be stable across the four focal tiers")

    c5 = {
        tier: results[tier]["records"][14]
        for tier in ("70mm", "150mm")
    }
    c5_k_variants = {records[0] for records in c5.values()}
    c5_pose_variants = {(records[1], records[2]) for records in c5.values()}
    require(len(c5_k_variants) == 2, "C5 K should vary across tele focal tiers")
    require(len(c5_pose_variants) == 1, "C5 pose should be stable across tele focal tiers")

    for key in range(0, 5):
        wide_records = {
            tier: results[tier]["records"][key]
            for tier in ("28mm", "35mm")
        }
        require(len(set(wide_records.values())) == 1, f"{audit.CAMERA_NAMES[key]} wide records changed")

    return "cross_tier=B4_pose_stable_K_variants4,C5_pose_stable_K_variants2,A1-A5_wide_stable"


def main() -> None:
    print(validate_static_producer_edge())
    results = {}
    for tier in audit.TIERS:
        result = validate_tier(tier)
        results[tier] = result
        print(
            f"{tier}: OK "
            f"producer_keys={camera_names(EXPECTED_PRODUCER_KEYS[tier])} "
            f"selector_pair_source_equal={result['selector_pair_source_equal']}/10 "
            f"full_public={camera_names(result['full_public'])} "
            f"pose_only_public={camera_names(result['pose_only'])} "
            f"k_not_public={camera_names(result['k_not_public'])}"
        )
    print(validate_cross_tier(results))


if __name__ == "__main__":
    main()
