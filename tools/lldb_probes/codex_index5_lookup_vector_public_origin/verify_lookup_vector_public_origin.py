#!/usr/bin/env python3
"""Validate index-5 lookup-vector public-origin reports.

This verifier intentionally admits only reproducible facts:

- the target `StereoLayer<false>+0xe0` vector is copied from the immediate
  `0x28f5a0`/`0x28f860` generator span by `0xf02d0`;
- the full vector exactly matches the static reciprocal near/far ramp formula;
- no full vector byte sequence is present in the LRI block payloads, and no
  full vector fixed32 sequence is present in public calibration messages.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/codex_index5_lookup_vector_public_origin"

TIERS = {
    "28mm": "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
    "35mm": "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri",
    "70mm": "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
    "150mm": "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
}

EXPECTED_COUNTS = {
    "28mm": 752,
    "35mm": 752,
    "70mm": 1472,
    "150mm": 1472,
}

EXPECTED_STACK_PREFIX = [0xF043E, 0x26C4DC, 0x26BDF8, 0x26895A, 0x2687AB, 0x3FCB86]
CALIB_BLOCK_SIZES = {32832, 262968, 35266}
NEAR_ENDPOINT = 200.0
FAR_ENDPOINT = 640000.0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier: str) -> None:
    hdr = RUN_ROOT / f"lookup_vector_public_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_words(raw: bytes) -> list[int]:
    return list(struct.unpack("<" + "I" * (len(raw) // 4), raw))


def f32_values(raw: bytes) -> list[float]:
    return list(struct.unpack("<" + "f" * (len(raw) // 4), raw))


def expected_reciprocal_ramp(count: int) -> list[float]:
    """Mirror `0x28f860` scalar float32 operations."""
    require(count > 0, "count must be positive")
    values = [0.0] * count
    one = f32(1.0)
    near = f32(NEAR_ENDPOINT)
    far = f32(FAR_ENDPOINT)
    denom_near = f32(one / near)
    denom = f32(one / far)
    step = f32(f32(denom_near - denom) / f32(count - 1))

    index = 0
    if count & 1 == 0:
        values[0] = far
        denom = f32(denom + step)
        index = 1

    if count != 2:
        remaining = (count - 1) - index
        pos = index
        while remaining:
            values[pos] = f32(one / denom)
            denom = f32(denom + step)
            if pos + 1 < count:
                values[pos + 1] = f32(one / denom)
                denom = f32(denom + step)
            pos += 2
            remaining -= 2

    values[count - 1] = near
    return values


def read_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7
    raise ValueError("truncated varint")


def parse_fields(data: bytes):
    pos = 0
    while pos < len(data):
        try:
            tag, pos = read_varint(data, pos)
        except ValueError:
            break
        field_no = tag >> 3
        wire_type = tag & 7
        if field_no == 0:
            break
        if wire_type == 0:
            try:
                value, pos = read_varint(data, pos)
            except ValueError:
                break
            yield field_no, wire_type, value
        elif wire_type == 1:
            if pos + 8 > len(data):
                break
            value = struct.unpack_from("<Q", data, pos)[0]
            pos += 8
            yield field_no, wire_type, value
        elif wire_type == 2:
            try:
                length, pos = read_varint(data, pos)
            except ValueError:
                break
            if pos + length > len(data):
                break
            value = data[pos : pos + length]
            pos += length
            yield field_no, wire_type, value
        elif wire_type == 5:
            if pos + 4 > len(data):
                break
            value = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            yield field_no, wire_type, value
        else:
            break


def walk_messages(data: bytes):
    yield data
    for _field_no, wire_type, value in parse_fields(data):
        if wire_type == 2 and isinstance(value, bytes):
            yield from walk_messages(value)


def fixed32_values(data: bytes) -> list[int]:
    return [
        value
        for _field_no, wire_type, value in parse_fields(data)
        if wire_type == 5 and isinstance(value, int)
    ]


def scan_lri_blocks(path: str) -> list[dict]:
    blocks = []
    lri = Path(path)
    with lri.open("rb") as handle:
        offset = 0
        index = 0
        file_size = lri.stat().st_size
        while offset < file_size:
            handle.seek(offset)
            header = handle.read(32)
            if len(header) < 32 or header[:4] != b"LELR":
                break
            total_len = struct.unpack_from("<Q", header, 4)[0]
            msg_offset = struct.unpack_from("<Q", header, 12)[0]
            msg_len = struct.unpack_from("<I", header, 20)[0]
            if total_len == 0:
                break
            handle.seek(offset + msg_offset)
            payload = handle.read(msg_len)
            blocks.append({"index": index, "payload_size": msg_len, "payload": payload})
            offset += total_len
            index += 1
    return blocks


def load_packet(tier: str) -> dict:
    return json.loads((RUN_ROOT / f"lookup_vector_public_{tier}.json").read_text())


def target_sample(packet: dict, site: str, key: str) -> dict:
    matches = [
        sample
        for sample in packet.get("target_samples", [])
        if sample.get("site") == site and sample.get(key)
    ]
    require(len(matches) == 1, f"{packet.get('label')}: expected one target {site}")
    return matches[0]


def validate_packet(tier: str) -> dict:
    packet = load_packet(tier)
    process = packet["process"]
    require(process["state"] == "exited", f"{tier}: process did not exit")
    require(process["exit_status"] == 0, f"{tier}: nonzero exit")
    require(not packet.get("drive_hit_step_cap"), f"{tier}: hit step cap")
    require(not packet.get("errors"), f"{tier}: probe errors present")
    require_hdr_output(tier)
    for site in ("index_setter_26bbd0", "lookup_vector_after_copy_f043e", "descriptor_build_267010_entry"):
        require(packet["target_counts"].get(site) == 1, f"{tier}: target count mismatch for {site}")

    vector_sample = target_sample(
        packet, "lookup_vector_after_copy_f043e", "r14_equals_target_plus_0xe0"
    )
    vector = vector_sample["target_lookup_vector_0xe0"]
    source = vector_sample["source_span_copied_by_f02d0"]
    fields = vector_sample["target_object_fields"]
    count = EXPECTED_COUNTS[tier]
    require(fields["index_0x8"] == 5, f"{tier}: target object index mismatch")
    require(fields["mode_0xc"] == 8, f"{tier}: target object mode mismatch")
    require(fields["near_far_0x298_0x29c_f32"] == [NEAR_ENDPOINT, FAR_ENDPOINT], f"{tier}: near/far fields mismatch")
    require(fields["depth_width_0x2a0"] == 2080, f"{tier}: target object width mismatch")
    require(fields["depth_height_0x2a4"] == 1560, f"{tier}: target object height mismatch")
    require(vector["count_f32"] == count, f"{tier}: vector count mismatch")
    require(vector["byte_size"] == count * 4, f"{tier}: vector byte size mismatch")
    require(source["byte_size"] == count * 4, f"{tier}: source span size mismatch")
    require(source["raw_hex"] == vector["raw_hex"], f"{tier}: source span != destination vector")
    require(source["raw_sha256"] == vector["raw_sha256"], f"{tier}: source hash mismatch")

    stack_prefix = [frame.get("libcp_va") for frame in vector_sample["stack"][: len(EXPECTED_STACK_PREFIX)]]
    require(stack_prefix == EXPECTED_STACK_PREFIX, f"{tier}: stack prefix mismatch {stack_prefix}")
    regs = vector_sample["registers"]
    require(regs["r12"] == count, f"{tier}: f02d0 r12 count mismatch")
    require(regs["r13"] == count * 4, f"{tier}: f02d0 r13 byte span mismatch")

    raw = bytes.fromhex(vector["raw_hex"])
    values = f32_values(raw)
    expected_values = expected_reciprocal_ramp(count)
    require(values == expected_values, f"{tier}: reciprocal near/far ramp mismatch")

    continuity = target_sample(packet, "descriptor_build_267010_entry", "rdx_equals_target_plus_0xe0")
    cont_vector = continuity["target_lookup_vector_0xe0"]
    require(cont_vector["raw_sha256"] == vector["raw_sha256"], f"{tier}: 0x267010 vector changed")
    require(cont_vector["count_f32"] == count, f"{tier}: 0x267010 vector count mismatch")

    return {
        "tier": tier,
        "count": count,
        "raw": raw,
        "raw_sha256": vector["raw_sha256"],
        "first4": values[:4],
        "last4": values[-4:],
    }


def validate_lri_non_origin(tier: str, raw: bytes) -> dict:
    blocks = scan_lri_blocks(TIERS[tier])
    full_block_hits = [
        (block["index"], block["payload_size"])
        for block in blocks
        if block["payload"].find(raw) >= 0
    ]
    require(not full_block_hits, f"{tier}: full lookup vector found in LRI block payload")

    raw_words = tuple(f32_words(raw))
    fixed_sequence_hits = []
    scalar_hits = 0
    scalar_checked = 0
    for block in blocks:
        if block["payload_size"] not in CALIB_BLOCK_SIZES:
            continue
        for message in walk_messages(block["payload"]):
            fixed = tuple(fixed32_values(message))
            if fixed == raw_words:
                fixed_sequence_hits.append(block["payload_size"])
            if fixed:
                fixed_set = set(fixed)
                for word in raw_words:
                    scalar_checked += 1
                    if word in fixed_set:
                        scalar_hits += 1
    require(not fixed_sequence_hits, f"{tier}: full lookup vector appears as calibration fixed32 sequence")
    return {
        "lri_blocks": len(blocks),
        "full_block_hits": 0,
        "calib_fixed32_full_sequence_hits": 0,
        "calib_fixed32_scalar_hits": scalar_hits,
        "calib_fixed32_scalar_checks": scalar_checked,
    }


def main() -> None:
    summaries = {tier: validate_packet(tier) for tier in TIERS}
    require(
        summaries["28mm"]["raw_sha256"] == summaries["35mm"]["raw_sha256"],
        "28mm/35mm lookup vectors differ",
    )
    require(
        summaries["70mm"]["raw_sha256"] == summaries["150mm"]["raw_sha256"],
        "70mm/150mm lookup vectors differ",
    )
    require(
        summaries["28mm"]["raw_sha256"] != summaries["70mm"]["raw_sha256"],
        "wide and tele lookup vectors unexpectedly match",
    )

    for tier, summary in summaries.items():
        lri = validate_lri_non_origin(tier, summary["raw"])
        first = ", ".join(f"{value:.3f}" for value in summary["first4"])
        last = ", ".join(f"{value:.6f}" for value in summary["last4"])
        print(
            f"{tier}: OK count={summary['count']} sha={summary['raw_sha256'][:16]} "
            f"reciprocal_ramp={FAR_ENDPOINT:.1f}->{NEAR_ENDPOINT:.1f} "
            f"first4=[{first}] last4=[{last}] "
            f"lri_full_hits={lri['full_block_hits']} "
            f"calib_fixed32_sequence_hits={lri['calib_fixed32_full_sequence_hits']} "
            f"calib_scalar_hits={lri['calib_fixed32_scalar_hits']}/"
            f"{lri['calib_fixed32_scalar_checks']}"
        )


if __name__ == "__main__":
    main()
