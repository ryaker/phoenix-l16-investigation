#!/usr/bin/env python3
"""Lane B index-5 public-meaning audit verifier.

This is a tracked, deterministic checker for the evidence notes
`docs/evidence/lldb_index5_depth_public_meaning_gap_audit_four_zoom.md` and
`docs/evidence/lldb_index5_operand_public_origin_audit_four_zoom.md`.

It intentionally verifies only facts that can be checked from repo-local JSON
reports plus the real LRI block payloads. It does not assign public proto field
names to runtime-only fields.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TIERS = {
    "28mm": "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
    "35mm": "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri",
    "70mm": "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
    "150mm": "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
}

EXPECTED_LOOKUP_COUNTS = {
    "28mm": 752,
    "35mm": 752,
    "70mm": 1472,
    "150mm": 1472,
}

CAMERA_NAMES = {
    0: "A1",
    1: "A2",
    2: "A3",
    3: "A4",
    4: "A5",
    5: "B1",
    6: "B2",
    7: "B3",
    8: "B4",
    9: "B5",
    10: "C1",
    11: "C2",
    12: "C3",
    13: "C4",
    14: "C5",
    15: "C6",
}

EXPECTED_FIRED_SETS = {
    "28mm": list(range(0, 10)),
    "35mm": list(range(0, 10)),
    "70mm": list(range(5, 16)),
    "150mm": list(range(5, 16)),
}

EXPECTED_PROJECTION_KEYS = {
    "28mm": [0, 5, 6, 7, 8, 9],
    "35mm": [0, 5, 6, 7, 8, 9],
    "70mm": [8, 10, 11, 12, 13, 14],
    "150mm": [8, 10, 11, 12, 13, 14],
}

EXPECTED_F33D0_DEST_KEYS = {
    "28mm": list(range(0, 10)),
    "35mm": list(range(0, 10)),
    "70mm": list(range(5, 15)),
    "150mm": list(range(5, 15)),
}

PRESENT_PROTO_VALUES = {780, 3120, 4160}
ABSENT_PROTO_VALUES = {2080, 1560, 10432, 7824, 8896, 6672, 4096, 1040, 520, 390}
CALIB_BLOCK_SIZES = (32832, 262968, 35266)
F2770_DEFAULT_STAGE_F32 = [
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0,
    1.0, 0.0, 0.0,
    0.0, 1.0, 0.0,
    0.0, 0.0, 1.0,
    0.0, 0.0, 0.0,
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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


def walk_proto_values(data: bytes, depth: int = 0, max_depth: int = 8) -> set[int]:
    values: set[int] = set()
    if depth > max_depth:
        return values
    for _field_no, wire_type, value in parse_fields(data):
        if wire_type in (0, 1, 5) and isinstance(value, int):
            values.add(value)
        elif wire_type == 2 and isinstance(value, bytes):
            values |= walk_proto_values(value, depth + 1, max_depth)
    return values


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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def field_values(data: bytes, field_no: int, wire_type: int | None = None) -> list:
    return [
        value
        for fn, wt, value in parse_fields(data)
        if fn == field_no and (wire_type is None or wt == wire_type)
    ]


def first_field(data: bytes, field_no: int, wire_type: int | None = None):
    for fn, wt, value in parse_fields(data):
        if fn == field_no and (wire_type is None or wt == wire_type):
            return value
    return None


def validate_process(packet: dict, label: str) -> None:
    require(packet["process"]["state"] == "exited", f"{label}: process did not exit")
    require(packet["process"]["exit_status"] == 0, f"{label}: nonzero exit")
    require(not packet.get("drive_hit_step_cap"), f"{label}: hit drive step cap")
    require(not packet.get("errors"), f"{label}: JSON errors present")


def process_is_success(packet: dict) -> bool:
    process = packet.get("process") or {}
    return (
        process.get("state") == "exited"
        and process.get("exit_status") == 0
        and not packet.get("drive_hit_step_cap")
        and not packet.get("errors")
    )


def validate_lri_static() -> dict:
    summary = {}
    calibration_hashes = {size: set() for size in CALIB_BLOCK_SIZES}
    for tier, lri_path in TIERS.items():
        blocks = scan_lri_blocks(lri_path)
        payload_by_size = {block["payload_size"]: block["payload"] for block in blocks}
        missing = [size for size in CALIB_BLOCK_SIZES if size not in payload_by_size]
        require(not missing, f"{tier}: missing calibration payload sizes {missing}")
        for size in CALIB_BLOCK_SIZES:
            calibration_hashes[size].add(hashlib.sha256(payload_by_size[size]).hexdigest()[:16])

        all_values: set[int] = set()
        for block in blocks:
            all_values |= walk_proto_values(block["payload"])
        require(PRESENT_PROTO_VALUES <= all_values, f"{tier}: missing expected LRI proto values")
        unexpected = sorted(ABSENT_PROTO_VALUES & all_values)
        require(not unexpected, f"{tier}: unexpected computed dims stored as proto values {unexpected}")
        summary[tier] = {"block_count": len(blocks), "present_values": sorted(PRESENT_PROTO_VALUES)}

    for size, hashes in calibration_hashes.items():
        require(len(hashes) == 1, f"calibration payload size {size}: hashes differ {sorted(hashes)}")
    summary["calibration_hashes"] = {
        str(size): sorted(hashes)[0] for size, hashes in calibration_hashes.items()
    }
    return summary


def validate_public_lri_camera_config(tier: str) -> str:
    blocks = scan_lri_blocks(TIERS[tier])
    focal = first_field(blocks[0]["payload"], 4, wire_type=0)
    require(focal is not None, f"{tier}: missing LightHeader.field_4 focal length")

    fired: dict[int, int | None] = {}
    for block in blocks:
        for module in field_values(block["payload"], 12, wire_type=2):
            cam_id = first_field(module, 2, wire_type=0)
            encoder = first_field(module, 4, wire_type=0)
            if isinstance(cam_id, int) and 0 <= cam_id <= 15:
                fired[cam_id] = encoder if isinstance(encoder, int) else None
    fired_keys = sorted(fired)
    require(
        fired_keys == EXPECTED_FIRED_SETS[tier],
        f"{tier}: fired camera set {fired_keys} != {EXPECTED_FIRED_SETS[tier]}",
    )

    warp_payloads = [
        block["payload"] for block in blocks if block["payload_size"] == 262968
    ]
    require(len(warp_payloads) == 1, f"{tier}: expected one 262968-byte warp/calibration block")
    nominals: dict[int, list[int]] = {}
    for entry in field_values(warp_payloads[0], 13, wire_type=2):
        cam_id = first_field(entry, 1, wire_type=0)
        mapping = first_field(entry, 4, wire_type=2)
        if not isinstance(cam_id, int) or not isinstance(mapping, bytes):
            continue
        cam_nominals = []
        for config in field_values(mapping, 2, wire_type=2):
            nominal = first_field(config, 1, wire_type=0)
            if isinstance(nominal, int):
                cam_nominals.append(nominal)
        nominals[cam_id] = cam_nominals

    require(sorted(nominals) == list(range(16)), f"{tier}: warp entries do not cover cams 0..15")
    one_config = sorted(cam_id for cam_id, vals in nominals.items() if len(vals) == 1)
    four_config = sorted(cam_id for cam_id, vals in nominals.items() if len(vals) == 4)
    require(one_config == [0, 1, 2, 3, 4, 8, 11, 12], f"{tier}: fixed-camera set mismatch")
    require(four_config == [5, 6, 7, 9, 10, 13, 14, 15], f"{tier}: movable-camera set mismatch")

    fired_names = ",".join(CAMERA_NAMES[cam_id] for cam_id in fired_keys)
    return f"LRI_focal={focal} fired={fired_names} warp_field13=16"


def public_lightheader_camera_fields(tier: str) -> dict[int, dict[int, int]]:
    modules: dict[int, dict[int, int]] = {}
    for block in scan_lri_blocks(TIERS[tier]):
        for module in field_values(block["payload"], 12, wire_type=2):
            cam_id = first_field(module, 2, wire_type=0)
            if not isinstance(cam_id, int) or not 0 <= cam_id <= 15:
                continue
            fields = {
                field_no: value
                for field_no, wire_type, value in parse_fields(module)
                if wire_type in (0, 5) and isinstance(value, int)
            }
            modules[cam_id] = fields
    require(
        sorted(modules) == EXPECTED_FIRED_SETS[tier],
        f"{tier}: LightHeader.field_12 module set mismatch",
    )
    return modules


def _protobuf_int32(value: int) -> int:
    return struct.unpack("<i", struct.pack("<I", value & 0xFFFFFFFF))[0]


def public_lightheader_bayer_overrides(tier: str) -> dict[int, tuple[int, int]]:
    overrides: dict[int, tuple[int, int]] = {}
    for block in scan_lri_blocks(TIERS[tier]):
        for module in field_values(block["payload"], 12, wire_type=2):
            cam_id = first_field(module, 2, wire_type=0)
            override = first_field(module, 13, wire_type=2)
            if not isinstance(cam_id, int) or not 0 <= cam_id <= 15:
                continue
            require(isinstance(override, bytes), f"{tier}/{cam_id}: missing bayer override")
            x = first_field(override, 1, wire_type=0)
            y = first_field(override, 2, wire_type=0)
            require(isinstance(x, int) and isinstance(y, int), f"{tier}/{cam_id}: invalid bayer override")
            overrides[cam_id] = (_protobuf_int32(x), _protobuf_int32(y))
    require(
        sorted(overrides) == EXPECTED_FIRED_SETS[tier],
        f"{tier}: CameraModule.sensor_bayer_red_override set mismatch",
    )
    return overrides


def pack_f32(values: list[float]) -> bytes:
    return b"".join(struct.pack("<f", float(value)) for value in values)


def _hex_to_bytes(value: str | None) -> bytes | None:
    if not value:
        return None
    return bytes.fromhex(value)


def _payload_contains_any(payloads: list[bytes], needle: bytes) -> bool:
    return any(payload.find(needle) >= 0 for payload in payloads)


def _payload_hit_count(payloads: list[bytes], needle: bytes) -> int:
    return sum(1 for payload in payloads if payload.find(needle) >= 0)


def _f32_list_from_hex(raw_hex: str) -> list[float]:
    data = bytes.fromhex(raw_hex)
    require(len(data) % 4 == 0, "raw f32 span is not a multiple of four bytes")
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def _fixed32_values(data: bytes) -> list[int]:
    return [
        value
        for _field_no, wire_type, value in parse_fields(data)
        if wire_type == 5 and isinstance(value, int)
    ]


def _runtime_f32_raw(values: list[float]) -> list[int]:
    return [struct.unpack("<I", struct.pack("<f", float(value)))[0] for value in values]


def _message_field(data: bytes, field_no: int, index: int = 0) -> bytes:
    values = field_values(data, field_no, wire_type=2)
    require(len(values) > index, f"missing field {field_no}[{index}]")
    value = values[index]
    require(isinstance(value, bytes), f"field {field_no}[{index}] is not bytes")
    return value


def _walk_fixed32_paths(data: bytes, path: tuple[str, ...] = ()):
    seen: dict[int, int] = {}
    for field_no, wire_type, value in parse_fields(data):
        position = seen.get(field_no, 0)
        seen[field_no] = position + 1
        child_path = path + (f"field_{field_no}[{position}]",)
        if wire_type == 5 and isinstance(value, int):
            yield child_path, value
        elif wire_type == 2 and isinstance(value, bytes):
            yield from _walk_fixed32_paths(value, child_path)


def _walk_all_fixed32(data: bytes) -> list[tuple[tuple[str, ...], int]]:
    return list(_walk_fixed32_paths(data))


def _walk_messages(data: bytes, path: tuple[str, ...] = ()):
    yield path, data
    seen: dict[int, int] = {}
    for field_no, wire_type, value in parse_fields(data):
        position = seen.get(field_no, 0)
        seen[field_no] = position + 1
        if wire_type == 2 and isinstance(value, bytes):
            child_path = path + (f"field_{field_no}[{position}]",)
            yield from _walk_messages(value, child_path)


def public_intrinsics_compact_records(tier: str) -> dict[int, dict]:
    blocks = scan_lri_blocks(TIERS[tier])
    payloads = [block["payload"] for block in blocks if block["payload_size"] == 32832]
    require(len(payloads) == 1, f"{tier}: expected one 32832-byte intrinsics payload")

    records: dict[int, dict] = {}
    for entry_index, entry in enumerate(field_values(payloads[0], 13, wire_type=2)):
        cam_id = first_field(entry, 1, wire_type=0)
        body = first_field(entry, 3, wire_type=2)
        if not isinstance(cam_id, int) or not isinstance(body, bytes):
            continue
        try:
            focus_or_range_entries = field_values(body, 2, wire_type=2)
            k_matrix = _message_field(_message_field(focus_or_range_entries[0], 2), 1)
            pose_record = _message_field(_message_field(focus_or_range_entries[2], 3), 1)
            rotation_matrix = _message_field(pose_record, 1)
            translation_vector = _message_field(pose_record, 2)
        except (AssertionError, IndexError):
            continue
        records[cam_id] = {
            "entry_index": entry_index,
            "camera_id": cam_id,
            "k_matrix_raw": _fixed32_values(k_matrix),
            "rotation_raw": _fixed32_values(rotation_matrix),
            "translation_raw": _fixed32_values(translation_vector),
            "path_k": "32832.field_13[camera].field_3.field_2[0].field_2.field_1",
            "path_rotation": "32832.field_13[camera].field_3.field_2[2].field_3.field_1.field_1",
            "path_translation": "32832.field_13[camera].field_3.field_2[2].field_3.field_1.field_2",
        }
    require(
        {0, 1, 2, 3, 4} <= set(records),
        f"{tier}: compact intrinsics records do not cover A-bank cams 0..4",
    )
    return records


def public_calibration_fixed32_index(tier: str) -> dict[int, list[str]]:
    index: dict[int, list[str]] = {}
    for block in scan_lri_blocks(TIERS[tier]):
        if block["payload_size"] not in CALIB_BLOCK_SIZES:
            continue
        for field_no, wire_type, value in parse_fields(block["payload"]):
            if wire_type != 2 or not isinstance(value, bytes):
                continue
            if field_no == 13:
                cam_id = first_field(value, 1, wire_type=0)
                prefix = f"{block['payload_size']}.field_13[camera={cam_id}]"
            else:
                prefix = f"{block['payload_size']}.field_{field_no}"
            for path, raw in _walk_all_fixed32(value):
                index.setdefault(raw, []).append(prefix + "." + ".".join(path))
    return index


def public_calibration_fixed32_sequence_index(tier: str) -> dict[tuple[int, ...], list[str]]:
    index: dict[tuple[int, ...], list[str]] = {}
    for block in scan_lri_blocks(TIERS[tier]):
        if block["payload_size"] not in CALIB_BLOCK_SIZES:
            continue
        for field_no, wire_type, value in parse_fields(block["payload"]):
            if wire_type != 2 or not isinstance(value, bytes):
                continue
            if field_no == 13:
                cam_id = first_field(value, 1, wire_type=0)
                prefix = f"{block['payload_size']}.field_13[camera={cam_id}]"
            else:
                prefix = f"{block['payload_size']}.field_{field_no}"
            for path, message in _walk_messages(value):
                fixed = tuple(_fixed32_values(message))
                if fixed:
                    index.setdefault(fixed, []).append(prefix + "." + ".".join(path))
    return index


def _is_trivial_raw(value: int) -> bool:
    return value in {0, 0x3F800000}


def _calib_record_raw_from_f33d0(event: dict) -> tuple[list[int], list[int], list[int]]:
    f33d0 = event["f33d0"]
    src1_raw = _runtime_f32_raw(f33d0["src1_f32x8"]) + [f33d0["src1_i32_0x20"] & 0xFFFFFFFF]
    src2_raw = _runtime_f32_raw(f33d0["src2_f32x8"]) + [f33d0["src2_i32_0x20"] & 0xFFFFFFFF]
    triple_raw = [value & 0xFFFFFFFF for value in f33d0["triple_i32"]]
    return src1_raw, src2_raw, triple_raw


def validate_f33d0_public_intrinsics_bridge(tier: str) -> str:
    packet = load_json(ROOT / "runs/state_helpers_23c5f0_f33d0_runtime" / f"state_helper_{tier}.json")
    validate_process(packet, f"{tier} state_helpers_23c5f0_f33d0_runtime")
    events = [event for event in packet["events"] if event.get("f33d0")]
    require(events, f"{tier}: no f33d0 events")
    require(packet["counts"]["0xf33d0"] == len(events), f"{tier}: f33d0 event/count mismatch")
    require(
        packet["breakpoint_hit_counts"]["0xf33d0"] == len(events),
        f"{tier}: f33d0 breakpoint/event mismatch",
    )

    dest_keys = sorted({event["f33d0"]["dest_i32_0x60"] for event in events})
    require(dest_keys == EXPECTED_F33D0_DEST_KEYS[tier], f"{tier}: f33d0 destination key set mismatch")
    require(set(dest_keys) <= set(EXPECTED_FIRED_SETS[tier]), f"{tier}: f33d0 keys outside fired set")
    require({event["f33d0"]["dest_i32_0x64"] for event in events} == {0}, f"{tier}: f33d0 dest+0x64")
    require({event["f33d0"]["dest_u8_0x30"] for event in events} == {1}, f"{tier}: f33d0 dest+0x30")
    require({event["f33d0"]["selector_r8d"] for event in events} == {0, 1}, f"{tier}: f33d0 selectors")

    public_records = public_intrinsics_compact_records(tier)
    exact_public_events = []
    exact_components = {"k": [], "rotation": [], "translation": []}
    nontrivial_no_fixed32_hits = 0
    checked_nontrivial_values = 0
    fixed32_index = public_calibration_fixed32_index(tier)
    fixed32_sequence_index = public_calibration_fixed32_sequence_index(tier)
    for event in events:
        key = event["f33d0"]["dest_i32_0x60"]
        selector = event["f33d0"]["selector_r8d"]
        src1_raw, src2_raw, triple_raw = _calib_record_raw_from_f33d0(event)
        if tuple(src1_raw) in fixed32_sequence_index:
            exact_components["k"].append((selector, key))
        if tuple(src2_raw) in fixed32_sequence_index:
            exact_components["rotation"].append((selector, key))
        if tuple(triple_raw) in fixed32_sequence_index:
            exact_components["translation"].append((selector, key))
        public = public_records.get(key)
        if public and (
            src1_raw == public["k_matrix_raw"]
            and src2_raw == public["rotation_raw"]
            and triple_raw == public["translation_raw"]
        ):
            exact_public_events.append((selector, key))
            continue
        for raw in src1_raw + src2_raw + triple_raw:
            if _is_trivial_raw(raw):
                continue
            checked_nontrivial_values += 1
            if raw not in fixed32_index:
                nontrivial_no_fixed32_hits += 1

    exact_selector0_keys = sorted(
        {key for selector, key in exact_public_events if selector == 0}
    )
    exact_selector1_keys = sorted(
        {key for selector, key in exact_public_events if selector == 1}
    )
    expected_exact = [0, 1, 2, 3, 4] if tier in {"28mm", "35mm"} else []
    expected_pose_exact = list(expected_exact)
    if tier in {"28mm", "35mm"}:
        expected_pose_exact += [8]
    else:
        expected_pose_exact += [8, 14]
    exact_k_selector0 = sorted({key for selector, key in exact_components["k"] if selector == 0})
    exact_rotation_selector0 = sorted(
        {key for selector, key in exact_components["rotation"] if selector == 0}
    )
    exact_translation_selector0 = sorted(
        {key for selector, key in exact_components["translation"] if selector == 0}
    )
    require(exact_selector0_keys == expected_exact, f"{tier}: f33d0 selector0 exact public keys")
    require(
        set(exact_selector1_keys) >= set(expected_exact),
        f"{tier}: f33d0 selector1 does not include expected public exact keys",
    )
    require(exact_k_selector0 == expected_exact, f"{tier}: f33d0 selector0 exact K keys")
    require(
        exact_rotation_selector0 == expected_pose_exact,
        f"{tier}: f33d0 selector0 exact rotation keys",
    )
    require(
        exact_translation_selector0 == expected_pose_exact,
        f"{tier}: f33d0 selector0 exact translation keys",
    )
    require(
        nontrivial_no_fixed32_hits > 0 or not checked_nontrivial_values,
        f"{tier}: expected at least one nontrivial non-exact calibration value",
    )
    require(
        not checked_nontrivial_values
        or nontrivial_no_fixed32_hits * 2 > checked_nontrivial_values,
        f"{tier}: non-exact f33d0 values are not mostly absent from public fixed32 fields",
    )

    dest_names = ",".join(CAMERA_NAMES[key] for key in dest_keys)
    exact0_names = ",".join(CAMERA_NAMES[key] for key in exact_selector0_keys) or "none"
    pose0_names = ",".join(CAMERA_NAMES[key] for key in exact_rotation_selector0) or "none"
    no_fixed = f"{nontrivial_no_fixed32_hits}/{checked_nontrivial_values}"
    return (
        f"f33d0_dest_keys={dest_names} selectors=0,1 "
        f"public_intrinsics_exact_selector0={exact0_names} "
        f"public_pose_exact_selector0={pose0_names} "
        f"nontrivial_fixed32_absent={no_fixed}"
    )


def collect_state_record_candidates(packet: dict) -> tuple[int, list[dict]]:
    checked = 0
    hits = []
    for event in packet["events"]:
        post = event.get("post_f33d0")
        if not post:
            continue
        dest = post.get("dest_current_offsets_post") or {}
        raw_candidates = [
            dest.get("raw_0x12c_0x14c"),
            dest.get("raw_0x150_0x170"),
            dest.get("raw_0x12c_0x180"),
            post.get("current_raw_0x12c_0x14c"),
            post.get("current_raw_0x150_0x170"),
            post.get("current_raw_0x12c_0x180"),
            post.get("factory_raw_0x180_0x1a0"),
            post.get("factory_raw_0x1a4_0x1c4"),
            post.get("factory_raw_0x180_0x1d4"),
            post.get("src1_stack_raw_0x00_0x24"),
            post.get("src2_stack_raw_0x00_0x24"),
            post.get("triple_stack_raw_0x00_0x0c"),
        ]
        found_raw = False
        for raw_hex in raw_candidates:
            needle = _hex_to_bytes(raw_hex)
            if needle is None:
                continue
            found_raw = True
            checked += 1
            hits.append({"sequence": event.get("sequence"), "raw_hex": raw_hex, "needle": needle})

        if found_raw:
            continue

        float_candidates = [
            dest.get("0x12c"),
            dest.get("0x150"),
            post.get("current_0x12c_f32x8"),
            post.get("current_0x150_f32x8"),
            post.get("factory_0x180_f32x8"),
            post.get("factory_0x1a4_f32x8"),
            post.get("src1_stack_f32x8"),
            post.get("src2_stack_f32x8"),
        ]
        for values in float_candidates:
            if not isinstance(values, list) or len(values) != 8:
                continue
            checked += 1
            hits.append({"sequence": event.get("sequence"), "values": values, "needle": pack_f32(values)})
    return checked, hits


def validate_state_record_no_direct_lri_copy(tier: str) -> str:
    source = "snapshot"
    packet = load_json(ROOT / "runs/state_helper_23c5f0_exit_snapshot" / f"snapshot_{tier}.json")
    if not process_is_success(packet):
        fallback = load_json(ROOT / "runs/state_helper_f34e0_match_runtime" / f"f34e0_match_{tier}.json")
        validate_process(fallback, f"{tier} state_helper_f34e0_match_runtime")
        source = "f34e0_fallback"
        packet = fallback

    calib_payloads = [
        block["payload"]
        for block in scan_lri_blocks(TIERS[tier])
        if block["payload_size"] in CALIB_BLOCK_SIZES
    ]
    checked, candidates = collect_state_record_candidates(packet)
    hits = [
        {key: value for key, value in candidate.items() if key != "needle"}
        for candidate in candidates
        if _payload_contains_any(calib_payloads, candidate["needle"])
    ]
    require(checked > 0, f"{tier}: no state-helper records checked")
    require(not hits, f"{tier}: exact state-helper records found in LRI calibration blocks")
    return f"state_record_lri_exact_hits=0/{checked} source={source}"


def validate_projection_keys(tier: str) -> str:
    packet = load_json(ROOT / "runs/projection_field_dispatcher" / f"projection_field_dispatcher_{tier}.json")
    validate_process(packet, f"{tier} projection_field_dispatcher")
    by_key = packet["by_key"]
    runtime_keys = sorted(int(key) for key in by_key)
    require(
        runtime_keys == EXPECTED_PROJECTION_KEYS[tier],
        f"{tier}: projection keys {runtime_keys} != {EXPECTED_PROJECTION_KEYS[tier]}",
    )
    fired_set = set(EXPECTED_FIRED_SETS[tier])
    require(set(runtime_keys) <= fired_set, f"{tier}: projection keys are not a subset of public fired cameras")
    key_names = ",".join(CAMERA_NAMES[key] for key in runtime_keys)
    return f"projection_keys={key_names}"


def validate_captured_image_constructor_keys(tier: str) -> str:
    packet = load_json(ROOT / "runs/capturedimage_f2770_origin" / f"f2770_origin_{tier}.json")
    require(not packet.get("errors"), f"{tier}: f2770 constructor errors present")
    require(packet["counts"]["pre"] == packet["counts"]["post"], f"{tier}: f2770 pre/post mismatch")
    require(
        packet["counts"]["pre"] == len(EXPECTED_FIRED_SETS[tier]),
        f"{tier}: f2770 constructor count mismatch",
    )
    require(len(packet["events"]) == len(EXPECTED_FIRED_SETS[tier]), f"{tier}: f2770 event count mismatch")

    keys = []
    groups = set()
    active_values = set()
    stage_raw_packets = 0
    raw_candidates = []
    public_modules = public_lightheader_camera_fields(tier)
    public_bayer_overrides = public_lightheader_bayer_overrides(tier)
    for event in packet["events"]:
        input_fields = event["input_fields"]
        output_fields = event["output_fields"]
        key = output_fields["u32_0x60"]
        module = public_modules[key]
        public_override = public_bayer_overrides[key]
        source_override = input_fields["optional_0x28"]
        public_is_enabled = module.get(3, 1)
        keys.append(key)
        groups.add(output_fields["u32_0x64"])
        active_values.add(output_fields["byte_0x30"])
        require(module[2] == key, f"{tier}: public LightHeader module camera id mismatch")
        require(input_fields["u32_0x30"] == key, f"{tier}: f2770 input camera id != output key")
        require(public_is_enabled in (0, 1), f"{tier}: invalid public is_enabled value")
        require(
            input_fields["byte_0x60"] == public_is_enabled,
            f"{tier}: f2770 input+0x60 != CameraModule.is_enabled",
        )
        require(
            output_fields["byte_0x30"] == public_is_enabled,
            f"{tier}: CapturedImage+0x30 != CameraModule.is_enabled",
        )
        require(
            input_fields["u32_0x34"] == module.get(4, 0),
            f"{tier}: f2770 input+0x34 != LightHeader.field_12.field_4",
        )
        require(
            output_fields["u32_0x50"] == module.get(4, 0),
            f"{tier}: f2770 object+0x50 != LightHeader.field_12.field_4",
        )
        require(
            input_fields["u32_0x38"] == module[5],
            f"{tier}: f2770 input+0x38 != LightHeader.field_12.field_5",
        )
        require(
            output_fields["u32_0x54"] == module[5],
            f"{tier}: f2770 object+0x54 != LightHeader.field_12.field_5",
        )
        require(
            input_fields["u32_0x3c"] == module[7],
            f"{tier}: f2770 input+0x3c != LightHeader.field_12.field_7",
        )
        require(
            output_fields["u32_0x40"] == module[7],
            f"{tier}: CapturedImage+0x40 != LightHeader.field_12.field_7",
        )
        require(
            input_fields["ptr_0x40"] == module[8],
            f"{tier}: f2770 input+0x40 != LightHeader.field_12.field_8",
        )
        require(
            input_fields["u32_0x48"] * 2 == module[10],
            f"{tier}: f2770 input+0x48 * 2 != LightHeader.field_12.field_10",
        )
        require(
            output_fields["u32_0x104"] == input_fields["u32_0x48"],
            f"{tier}: CapturedImage+0x104 != decoded LightHeader.field_12.field_10",
        )
        require(
            input_fields["u32_0x50"] == module[14],
            f"{tier}: f2770 input+0x50 != LightHeader.field_12.field_14",
        )
        require(source_override["read_ok"], f"{tier}: f2770 input+0x28 is unreadable")
        require(
            (source_override["i32_0x18_lo"], source_override["i32_0x1c_hi"]) == public_override,
            f"{tier}: f2770 input+0x28 != CameraModule.sensor_bayer_red_override",
        )
        require(
            (output_fields["i32_0x58"], output_fields["i32_0x5c"]) == public_override,
            f"{tier}: CapturedImage+0x58/+0x5c != CameraModule.sensor_bayer_red_override",
        )
        require(output_fields["i32_0x114"] == 4160, f"{tier}: f2770 object width is not 4160")
        require(output_fields["i32_0x118"] == 3120, f"{tier}: f2770 object height is not 3120")
        require(output_fields["f32_0x124"] == 1.0, f"{tier}: f2770 x scale is not 1.0")
        require(output_fields["f32_0x128"] == 1.0, f"{tier}: f2770 y scale is not 1.0")
        if output_fields.get("stage1_raw_0x12c_0x180") and output_fields.get("stage0_raw_0x180_0x1d4"):
            stage_raw_packets += 1
            require(
                _f32_list_from_hex(output_fields["stage1_raw_0x12c_0x180"]) == F2770_DEFAULT_STAGE_F32,
                f"{tier}: f2770 stage-1 constructor bank is not default identity",
            )
            require(
                _f32_list_from_hex(output_fields["stage0_raw_0x180_0x1d4"]) == F2770_DEFAULT_STAGE_F32,
                f"{tier}: f2770 stage-0 constructor bank is not default identity",
            )
        for name in (
            "raw_0x10c_0x12c",
            "stage1_raw_0x12c_0x14c",
            "stage1_raw_0x150_0x170",
            "stage1_raw_0x12c_0x180",
            "stage0_raw_0x180_0x1a0",
            "stage0_raw_0x1a4_0x1c4",
            "stage0_raw_0x180_0x1d4",
        ):
            raw_hex = output_fields.get(name)
            needle = _hex_to_bytes(raw_hex)
            if needle is not None:
                raw_candidates.append({"key": key, "name": name, "needle": needle})

    require(sorted(keys) == EXPECTED_FIRED_SETS[tier], f"{tier}: f2770 keys do not match fired cameras")
    require(groups == {0}, f"{tier}: f2770 object+0x64 groups differ from observed zero discriminator")
    require(active_values == {1}, f"{tier}: f2770 constructed active bytes differ from 1")
    require(stage_raw_packets == len(keys), f"{tier}: f2770 missing raw CalibStage packets")

    calib_payloads = [
        block["payload"]
        for block in scan_lri_blocks(TIERS[tier])
        if block["payload_size"] in CALIB_BLOCK_SIZES
    ]
    hits = [
        {key: value for key, value in candidate.items() if key != "needle"}
        for candidate in raw_candidates
        if _payload_contains_any(calib_payloads, candidate["needle"])
    ]
    require(not hits, f"{tier}: f2770 raw object-bank spans found in LRI calibration blocks")

    key_names = ",".join(CAMERA_NAMES[key] for key in sorted(keys))
    return (
        f"f2770_keys={key_names} object+0x64=0 is_enabled=1 "
        f"module_fields=field_2,field_3,field_4,field_5,field_7,field_8,field_10,field_13,field_14 "
        f"stage_raw={stage_raw_packets}/{len(keys)} stage_lri_exact_hits=0/{len(raw_candidates)}"
    )


def validate_lookup_origin(tier: str) -> str:
    packet = load_json(
        ROOT / "runs/codex_index5_source_lookup_origin_watch" / f"source_lookup_origin_{tier}.json"
    )
    validate_process(packet, f"{tier} source_lookup_origin")
    for site, count in packet["counts"].items():
        require(count == 6, f"{tier}: lookup-origin site {site} count {count}")
    expected_count = EXPECTED_LOOKUP_COUNTS[tier]
    final_writes = [
        sample
        for sample in packet.get("watchpoint_samples", [])
        if sample.get("libcp_va") == 0xF043E
    ]
    require(final_writes, f"{tier}: no final lookup-vector header write at 0xf043e")
    regs = final_writes[0]["registers"]
    require(regs.get("r12") == expected_count, f"{tier}: r12 lookup count mismatch")
    require(regs.get("r13") == expected_count * 4, f"{tier}: r13 lookup byte span mismatch")
    return f"lookup_count={expected_count}"


def validate_source_object_field(tier: str) -> str:
    packet = load_json(
        ROOT / "runs/codex_index5_source_object_field_origin" / f"source_object_field_{tier}.json"
    )
    validate_process(packet, f"{tier} source_object_field")
    for site, count in packet["target_counts"].items():
        require(count == 1, f"{tier}: source-object target {site} count {count}")
    later = next(sample for sample in packet["samples"] if sample.get("site") == "later_267010_entry")
    require(later["rdx_equals_target_plus_0xe0"], f"{tier}: 0x267010 rdx is not target+0xe0")
    source = later["source_object_0xf8"]
    desc = source["descriptor_0x20"]
    require(source["control_u32_0x00"] == 8, f"{tier}: source object control != 8")
    require(desc["width_0x10"] == 2080, f"{tier}: source object width mismatch")
    require(desc["height_0x14"] == 1560, f"{tier}: source object height mismatch")
    require(desc["stride_0x18"] == 2080, f"{tier}: source object stride mismatch")
    return "source_object=this+0xf8 control=8 desc=2080x1560"


def validate_source_local(tier: str) -> str:
    packet = load_json(
        ROOT / "runs/codex_29a140_source_local_producer" / f"source_local_{tier}.json"
    )
    validate_process(packet, f"{tier} source_local")
    for site, count in packet["target_counts"].items():
        require(count == 1, f"{tier}: source-local target {site} count {count}")
    formula = packet["record_formula_299eb0"]
    require(formula["available"], f"{tier}: record formula unavailable")
    require(formula["control"] == 8, f"{tier}: formula control mismatch")
    require(formula["width"] == 2080 and formula["height"] == 1560, f"{tier}: formula dims mismatch")
    require(formula["input_stride"] == 2080, f"{tier}: formula stride mismatch")
    require(formula["return_matches_computed"], f"{tier}: 0x299eb0 return mismatch")
    require(
        formula["zero_mask_count"] + formula["nonzero_mask_count"] == 2080 * 1560,
        f"{tier}: mask census mismatch",
    )
    after = next(sample for sample in packet["samples"] if sample.get("site") == "maker_after_299fd0")
    desc = after["output_local"]["descriptor_0x20"]
    require(desc["width_0x10"] == 2080, f"{tier}: output desc width mismatch")
    require(desc["height_0x14"] == 1560, f"{tier}: output desc height mismatch")
    after_299eb0 = next(sample for sample in packet["samples"] if sample.get("site") == "maker_after_299eb0")
    dumps = packet.get("bulk_dumps") or after_299eb0.get("bulk_dumps") or {}
    require(dumps, f"{tier}: missing full source-local input/mask dumps")
    expected_dump_sizes = {
        "input_descriptor": formula["input_stride"] * formula["height"] * 4,
        "mask_descriptor": formula["mask_stride"] * formula["height"],
    }
    full_dump_bytes = {}
    for dump_name, expected_size in expected_dump_sizes.items():
        dump = dumps.get(dump_name) or {}
        path = Path(dump.get("path", ""))
        require(path.exists(), f"{tier}: missing {dump_name} dump {path}")
        raw = path.read_bytes()
        require(len(raw) == expected_size, f"{tier}: {dump_name} dump size mismatch")
        require(dump.get("bytes") == expected_size, f"{tier}: {dump_name} metadata size mismatch")
        require(
            hashlib.sha256(raw).hexdigest() == dump.get("sha256"),
            f"{tier}: {dump_name} SHA-256 mismatch",
        )
        full_dump_bytes[dump_name] = raw

    input_u16 = after_299eb0["input_descriptor"]["first_u16_values"]
    input_first32 = struct.pack("<" + "H" * len(input_u16), *input_u16)
    mask_first16 = bytes(after_299eb0["mask_descriptor_target_plus_0x208"]["first_bytes"])
    record_headers = b"".join(
        struct.pack(
            "<HHHH",
            record["u16_0x00"],
            record["u16_0x02"],
            record["u16_0x04"],
            record["u16_0x06"],
        )
        for record in formula["first_records"]
    )
    blocks = scan_lri_blocks(TIERS[tier])
    all_payloads = [block["payload"] for block in blocks]
    calib_payloads = [
        block["payload"] for block in blocks if block["payload_size"] in CALIB_BLOCK_SIZES
    ]
    sampled_hits = {
        "input_first32": _payload_hit_count(all_payloads, input_first32),
        "mask_first16": _payload_hit_count(all_payloads, mask_first16),
        "record_headers64": _payload_hit_count(all_payloads, record_headers),
    }
    sampled_calib_hits = {
        "input_first32": _payload_hit_count(calib_payloads, input_first32),
        "mask_first16": _payload_hit_count(calib_payloads, mask_first16),
        "record_headers64": _payload_hit_count(calib_payloads, record_headers),
    }
    full_lri_hits = {
        "input_descriptor": _payload_hit_count(all_payloads, full_dump_bytes["input_descriptor"]),
        "mask_descriptor": _payload_hit_count(all_payloads, full_dump_bytes["mask_descriptor"]),
    }
    full_calib_hits = {
        "input_descriptor": _payload_hit_count(calib_payloads, full_dump_bytes["input_descriptor"]),
        "mask_descriptor": _payload_hit_count(calib_payloads, full_dump_bytes["mask_descriptor"]),
    }
    require(
        not any(sampled_hits.values()),
        f"{tier}: sampled source-local slice found in LRI payloads {sampled_hits}",
    )
    require(
        not any(sampled_calib_hits.values()),
        f"{tier}: sampled source-local slice found in calibration payloads {sampled_calib_hits}",
    )
    require(
        not any(full_lri_hits.values()),
        f"{tier}: full source-local dump found in LRI payloads {full_lri_hits}",
    )
    require(
        not any(full_calib_hits.values()),
        f"{tier}: full source-local dump found in calibration payloads {full_calib_hits}",
    )
    return (
        f"source_local_bytes={formula['computed_total_bytes']} "
        f"source_local_sample_lri_hits=input_first32:0,mask_first16:0,record_headers64:0 "
        f"source_local_full_lri_hits=input_descriptor:0,mask_descriptor:0 "
        f"source_local_full_calib_hits=input_descriptor:0,mask_descriptor:0 "
        f"input_sha={dumps['input_descriptor']['sha256'][:16]} "
        f"mask_sha={dumps['mask_descriptor']['sha256'][:16]}"
    )


_XMM4_VALIDATOR = None
_OPERAND_SOURCE_VALIDATOR = None


def _load_xmm4_validator():
    global _XMM4_VALIDATOR
    if _XMM4_VALIDATOR is not None:
        return _XMM4_VALIDATOR
    path = ROOT / "tools/lldb_probes/codex_276860_xmm4_origin/validate_xmm4_origin.py"
    spec = importlib.util.spec_from_file_location("validate_xmm4_origin", path)
    require(spec is not None and spec.loader is not None, "could not load xmm4 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _XMM4_VALIDATOR = module
    return module


def validate_xmm4_origin(tier: str) -> str:
    validator = _load_xmm4_validator()
    path = ROOT / "runs/codex_276860_xmm4_origin" / f"xmm4_origin_{tier}.json"
    result = validator.validate_packet(path)
    absence = result["scale_lri_absence"]
    return (
        f"xmm4_low={result['xmm4_low']:.9f} "
        f"object+0x60_lri_full_hits={absence['full_hits']} "
        f"object+0x60_lri_nonzero_scalar_hits={absence['nonzero_scalar_hits']}/"
        f"{absence['nonzero_scalar_count']}"
    )


def _load_operand_source_validator():
    global _OPERAND_SOURCE_VALIDATOR
    if _OPERAND_SOURCE_VALIDATOR is not None:
        return _OPERAND_SOURCE_VALIDATOR
    path = ROOT / "tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py"
    spec = importlib.util.spec_from_file_location("verify_operand_source", path)
    require(spec is not None and spec.loader is not None, "could not load operand source validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _OPERAND_SOURCE_VALIDATOR = module
    return module


def validate_operand_source_context(tier: str) -> str:
    validator = _load_operand_source_validator()
    path = ROOT / "runs/codex_276860_operand_source_context" / f"operand_source_{tier}.json"
    result = validator.validate_packet(path)
    packet = load_json(path)
    table = packet["packet"]["table"]
    object_fields = table["target_stack_context"]["object_fields"]
    operand_sources = table["operand_sources"]
    matched_store = operand_sources["xmm8_latest_load"]["xmm8_vector_load"]["matched_store_sample"]
    guide_source = matched_store["xmm8_vector_store"]["latest_guide_sample"]["guide_source"]

    guide_first16 = bytes.fromhex(
        object_fields["guide_descriptor_from_0x288"]["first_data_u8x16_hex"]
    )
    guide_sample16 = bytes.fromhex(guide_source["source_u8x16_hex"])
    subvec16 = bytes.fromhex(operand_sources["sub_vector16_hex"])
    table_u16 = struct.pack("<H", table["table_load"]["table_value_u16"])

    blocks = scan_lri_blocks(TIERS[tier])
    all_payloads = [block["payload"] for block in blocks]
    calib_payloads = [
        block["payload"] for block in blocks if block["payload_size"] in CALIB_BLOCK_SIZES
    ]
    exact_checks = {
        "guide_first16": guide_first16,
        "guide_sample16": guide_sample16,
        "subvec16": subvec16,
    }
    all_hits = {
        name: _payload_hit_count(all_payloads, needle) for name, needle in exact_checks.items()
    }
    calib_hits = {
        name: _payload_hit_count(calib_payloads, needle) for name, needle in exact_checks.items()
    }
    require(not any(all_hits.values()), f"{tier}: operand 16-byte slice found in LRI payloads")
    require(
        not any(calib_hits.values()),
        f"{tier}: operand 16-byte slice found in LRI calibration payloads",
    )

    fixed32_sequence_index = public_calibration_fixed32_sequence_index(tier)
    subvec_raw = tuple(struct.unpack("<IIII", subvec16))
    require(
        subvec_raw not in fixed32_sequence_index,
        f"{tier}: subtraction vector is an exact public calibration fixed32 sequence",
    )
    table_u16_lri_hits = _payload_hit_count(all_payloads, table_u16)
    return (
        f"xmm8_source=target+0x200/0x288 "
        f"sub_source=target+0x1e8 "
        f"table_source=target+0x198 "
        f"field_origins={result['field_origins']} "
        f"field_layout={result['field_layout']} "
        f"guide_u8x4={result['guide_u8x4_hex']} "
        f"operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 "
        f"subvec_public_fixed32_sequence_hits=0 "
        f"table_u16_lri_hits={table_u16_lri_hits}"
    )


def validate_map_provider(tier: str) -> str:
    packet = load_json(ROOT / "runs/iramp_map_provider_runtime" / f"map_provider_{tier}.json")
    validate_process(packet, f"{tier} map_provider")
    counts = packet["counts"]
    require(counts["entry_0x3f7040"] == 5, f"{tier}: dispatcher count mismatch")
    require(counts["cross_call_0x268480"] == 5, f"{tier}: cross provider count mismatch")
    require(counts["same_call_0x268480"] == 0, f"{tier}: same provider unexpectedly hit")
    require(packet["provider_target_counts"] == {str(0x26B590): 5}, f"{tier}: provider target mismatch")
    require(packet["map_return_counts"] == packet["record_map_counts"], f"{tier}: record map mismatch")
    return "record+0x40=UpsampleLayer+0x90 provider target 0x26b590"


def main() -> None:
    lri_summary = validate_lri_static()
    print("LRI static check: OK", lri_summary["calibration_hashes"])
    for tier in TIERS:
        print(
            f"{tier}: OK; "
            f"{validate_public_lri_camera_config(tier)}; "
            f"{validate_captured_image_constructor_keys(tier)}; "
            f"{validate_f33d0_public_intrinsics_bridge(tier)}; "
            f"{validate_projection_keys(tier)}; "
            f"{validate_state_record_no_direct_lri_copy(tier)}; "
            f"{validate_map_provider(tier)}; "
            f"{validate_lookup_origin(tier)}; "
            f"{validate_source_object_field(tier)}; "
            f"{validate_source_local(tier)}; "
            f"{validate_xmm4_origin(tier)}; "
            f"{validate_operand_source_context(tier)}"
        )


if __name__ == "__main__":
    main()
