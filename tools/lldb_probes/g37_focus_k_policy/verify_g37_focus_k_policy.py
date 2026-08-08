#!/usr/bin/env python3
"""Verify the installed focus-dependent K record-selection policy."""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/lldb_probes/codex_1f0ce0_k_source_trace"))
sys.path.insert(0, str(ROOT / "tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime"))

import lane_b_crossunit_lri_public_carriers as corpus  # noqa: E402
import lane_b_index5_public_meaning_audit as audit  # noqa: E402
import verify_1f0ce0_producer as producer  # noqa: E402
import verify_k_source_trace as runtime  # noqa: E402


LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
POLICY_SHA256 = "d9782d0824cb3a8ce5ce2d10ed6fb5bbe9d013c2da92f1ddcd0d207912974e5d"
SORT_SHA256 = "7f879de9769967612adb17ddd76cbf76f16546d41cb63b750e03c8f41ffa12dc"
TWO_RECORD_SHA256 = "e5269a4f159955072e89e9ac93fc2cb53e2abc851b3d2dc02e17c18908ab8dc6"
THREE_RECORD_SHA256 = "8bb0b944c82fed17ad5113ceb1d33ed70b5c3a02411612bc7129584b6b36d1ed"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def instruction(data, segments, address):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    item = next(decoder.disasm(producer.bytes_at(data, segments, address, 16), address))
    return item.mnemonic, item.op_str


def verify_static_policy():
    data = producer.LIBCP_DYLIB.read_bytes()
    require(hashlib.sha256(data).hexdigest() == LIBCP_SHA256, "installed libcp digest changed")
    segments = producer.macho_segments(data)

    windows = {
        (0x1F96E0, 0x1F9FB2): POLICY_SHA256,
        (0x1F995D, 0x1F99ED): SORT_SHA256,
        (0x1F9A33, 0x1F9C3D): TWO_RECORD_SHA256,
        (0x1F9C3D, 0x1F9FB2): THREE_RECORD_SHA256,
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(producer.bytes_at(data, segments, start, end - start)).hexdigest()
        require(actual == expected, f"0x{start:x}..0x{end:x} digest changed")

    expected_instructions = {
        0x1F99D9: ("ucomiss", "xmm0, xmm1"),
        0x1F99DC: ("jbe", "0x1f99c0"),
        0x1F9A57: ("cmp", "rcx, 0x90"),
        0x1F9B19: ("subss", "xmm8, xmm2"),
        0x1F9B1E: ("divss", "xmm8, xmm1"),
        0x1F9B2C: ("mulss", "xmm8, xmm5"),
        0x1F9B31: ("addss", "xmm8, xmm2"),
        0x1F9C46: ("ucomiss", "xmm3, xmm0"),
        0x1F9C54: ("ucomiss", "xmm0, xmm4"),
        0x1F9C67: ("ucomiss", "xmm1, xmm0"),
        0x1F9C6A: ("jae", "0x1f9ca6"),
        0x1F9C8C: ("subss", "xmm8, xmm2"),
        0x1F9C91: ("divss", "xmm8, xmm0"),
        0x1F9C9F: ("mulss", "xmm8, xmm1"),
        0x1F9CC6: ("movsxd", "rcx, dword ptr [r12 + 8]"),
        0x1F9CD8: ("subss", "xmm2, xmm8"),
        0x1F9CDD: ("divss", "xmm2, xmm4"),
        0x1F9CEA: ("mulss", "xmm2, xmm1"),
        0x1F9CEE: ("addss", "xmm8, xmm2"),
        0x1F9F60: ("mov", "rcx, qword ptr [rax + 0x40]"),
    }
    for address, expected in expected_instructions.items():
        actual = instruction(data, segments, address)
        require(actual == expected, f"0x{address:x}: {actual} != {expected}")

    epsilon = struct.unpack("<d", producer.bytes_at(data, segments, 0x5D42C8, 8))[0]
    require(epsilon == 0.001, f"unexpected focus-axis epsilon {epsilon}")
    return "installed_policy=OK one/two/three records epsilon=0.001"


def public_focus_records(path):
    blocks = audit.scan_lri_blocks(path)
    block = corpus.intrinsics_block(blocks)
    result = {}
    for entry in audit.field_values(block["payload"], 13, wire_type=2):
        camera_id = audit.first_field(entry, 1, wire_type=0)
        body = audit.first_field(entry, 3, wire_type=2)
        require(isinstance(camera_id, int) and isinstance(body, bytes), f"{path}: malformed camera record")
        records = []
        for config in audit.field_values(body, 2, wire_type=2):
            hall_raw = audit.first_field(config, 6, wire_type=5)
            intrinsics = audit.first_field(config, 2, wire_type=2)
            k_message = audit.first_field(intrinsics, 1, wire_type=2) if isinstance(intrinsics, bytes) else None
            if isinstance(hall_raw, int) and isinstance(k_message, bytes):
                k_raw = tuple(audit._fixed32_values(k_message))
                if len(k_raw) == 9:
                    records.append((struct.unpack("<f", struct.pack("<I", hall_raw))[0], k_raw))
        result[camera_id] = records
    return block, result


def verify_two_body_corpus():
    digests = set()
    rows = []
    for seed in corpus.EXACT_FOCAL_SEEDS:
        block, cameras = public_focus_records(seed["path"])
        require(sorted(cameras) == list(range(16)), f"{seed['role']} {seed['tier']}: camera set")
        require(all(len(records) == 2 for records in cameras.values()), f"{seed['role']} {seed['tier']}: record count")
        digest = hashlib.sha256(block["payload"]).hexdigest()[:16]
        require(digest == seed["unit_sig"], f"{seed['role']} {seed['tier']}: calibration digest")
        digests.add(digest)
        rows.append(f"{seed['role']}:{seed['tier']}:{block['payload_size']}B:{digest}")
    require(digests == {corpus.UNIT1_SIG, corpus.UNIT2_SIG}, f"physical-unit digests {digests}")
    return rows


def verify_retained_runtime():
    results = {}
    for tier in audit.TIERS:
        results[tier] = runtime.validate_tier(tier)
    runtime.validate_cross_tier(results)
    return "runtime_two_record=OK Unit-1 28/35/70/150mm"


def main():
    print(verify_static_policy())
    for row in verify_two_body_corpus():
        print(row)
    print(verify_retained_runtime())
    print("g37_focus_k_policy=OK")


if __name__ == "__main__":
    main()
