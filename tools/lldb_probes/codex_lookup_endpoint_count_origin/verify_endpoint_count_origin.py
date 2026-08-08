#!/usr/bin/env python3
"""Validate lookup endpoint/count origin reports."""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/codex_lookup_endpoint_count_origin"

TIERS = ("28mm", "35mm", "70mm", "150mm")
EXPECTED_COUNTS = {"28mm": 752, "35mm": 752, "70mm": 1472, "150mm": 1472}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier: str) -> None:
    hdr = RUN_ROOT / f"endpoint_count_origin_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_at(raw: bytes, offset: int) -> float:
    return struct.unpack_from("<f", raw, offset)[0]


def vector_raw(vector: dict) -> bytes:
    raw_hex = vector.get("raw_hex")
    return bytes.fromhex(raw_hex) if raw_hex else b""


def source_point(raw: bytes, base: int) -> tuple[float, float, float]:
    a = f32_at(raw, base + 0x24)
    b = f32_at(raw, base + 0x28)
    c = f32_at(raw, base + 0x2C)
    z = f32(f32(f32_at(raw, base + 0x30) * a) + f32(f32_at(raw, base + 0x3C) * b))
    z = f32(z + f32(f32_at(raw, base + 0x48) * c))
    y = f32(f32(f32_at(raw, base + 0x34) * a) + f32(f32_at(raw, base + 0x40) * b))
    y = f32(y + f32(f32_at(raw, base + 0x4C) * c))
    x = f32(f32(f32_at(raw, base + 0x38) * a) + f32(f32_at(raw, base + 0x44) * b))
    x = f32(x + f32(f32_at(raw, base + 0x50) * c))
    return x, y, z


def setup_count(fields: dict) -> dict:
    raw = vector_raw(fields["source_record_vector_0x258"])
    require(raw and len(raw) % 0xA8 == 0, "source-record vector is not 0xa8-aligned")
    record_count = len(raw) // 0xA8
    first = source_point(raw, 0)
    max_distance = f32(0.0)
    for index in range(record_count):
        point = source_point(raw, index * 0xA8)
        dx = f32(first[0] - point[0])
        dy = f32(first[1] - point[1])
        dz = f32(first[2] - point[2])
        dist = f32(math.sqrt(f32(f32(dx * dx) + f32(dy * dy)) + f32(dz * dz)))
        if dist > max_distance:
            max_distance = dist

    near, far = fields["near_far_0x298_0x29c_f32"]
    mode = int(fields["mode_0xc"])
    scalar = f32(fields["scalar_0x18_f32"])
    first_scalar = f32_at(raw, 0)
    reciprocal_span = f32(f32(1.0 / near) - f32(1.0 / far))
    scaled = f32(f32(f32(max_distance * scalar) * first_scalar) * reciprocal_span)
    unclamped = int(scaled)
    clamped = min(unclamped, 0x1000)
    rounded = clamped
    if mode:
        rounded = (clamped + mode - 1) // mode * mode
    return {
        "record_count": record_count,
        "first_record_scalar_0x00": first_scalar,
        "max_distance": max_distance,
        "scalar_0x18": scalar,
        "near": near,
        "far": far,
        "reciprocal_span": reciprocal_span,
        "unclamped": unclamped,
        "clamped": clamped,
        "mode": mode,
        "rounded_count": rounded,
    }


def load_packet(tier: str) -> dict:
    return json.loads((RUN_ROOT / f"endpoint_count_origin_{tier}.json").read_text())


def target_entry(packet: dict) -> dict:
    obj = packet.get("target_object")
    require(obj, f"{packet['label']}: missing target object")
    entry = packet["objects"].get(hex(obj))
    require(entry, f"{packet['label']}: missing target object entry")
    return entry


def validate(tier: str) -> dict:
    packet = load_packet(tier)
    process = packet["process"]
    require(process["state"] == "exited", f"{tier}: process did not exit")
    require(process["exit_status"] == 0, f"{tier}: nonzero process exit")
    require(not packet.get("drive_hit_step_cap"), f"{tier}: hit step cap")
    require(not packet.get("errors"), f"{tier}: probe errors present")
    require_hdr_output(tier)

    entry = target_entry(packet)
    require("setup_entry" in entry, f"{tier}: missing setup entry")
    require("setup_after_endpoint_store" in entry, f"{tier}: missing setup after-store")
    require("index_setter" in entry, f"{tier}: missing index setter")
    require("lookup_copy_after" in entry, f"{tier}: missing lookup copy")

    setup_fields = entry["setup_after_endpoint_store"]["object_fields_after_setup"]
    copy_fields = entry["lookup_copy_after"]["target_fields_at_lookup_copy"]
    require(setup_fields["near_far_0x298_0x29c_f32"] == [200.0, 640000.0], f"{tier}: endpoint mismatch")
    require(copy_fields["near_far_0x298_0x29c_f32"] == [200.0, 640000.0], f"{tier}: copy endpoint mismatch")
    require(setup_fields["scalar_0x18_f32"] == 2.0, f"{tier}: scalar mismatch")
    require(setup_fields["mode_0xc"] == 8, f"{tier}: mode mismatch")
    require(setup_fields["source_record_vector_0x258"]["byte_size"] == 840, f"{tier}: source record bytes")

    count_info = setup_count(setup_fields)
    require(count_info["rounded_count"] == EXPECTED_COUNTS[tier], f"{tier}: computed count mismatch")
    lookup_count = copy_fields["lookup_vector_0xe0"]["byte_size"] // 4
    require(lookup_count == EXPECTED_COUNTS[tier], f"{tier}: lookup vector count mismatch")
    return count_info


def main() -> int:
    for tier in TIERS:
        info = validate(tier)
        print(
            f"{tier}: OK records={info['record_count']} "
            f"max_distance={info['max_distance']:.6f} "
            f"first_scalar={info['first_record_scalar_0x00']:.6f} "
            f"scalar_0x18={info['scalar_0x18']:.6f} "
            f"rounded_count={info['rounded_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
