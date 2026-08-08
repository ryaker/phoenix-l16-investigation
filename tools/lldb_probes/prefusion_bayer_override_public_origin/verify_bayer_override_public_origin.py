#!/usr/bin/env python3
"""Verify the public origin of CapturedImage +0x58/+0x5c."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT_PATH = ROOT / "tools/lane_b_index5_public_meaning_audit.py"
SCHEMA_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
UNIT2_LRIS = {
    "28mm": Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
    "70mm": Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
}
EXPECTED_UNIT2_CALIB_SHA = (
    "223961c6bce6153e52aa20298ab7eae7a6edb3f2824950a433fdc49df0d4ade1"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_module("bayer_override_audit", AUDIT_PATH)
SCHEMA = load_module("bayer_override_schema", SCHEMA_PATH)
STATIC = load_module("bayer_override_static", STATIC_PATH)


def int32(value: int) -> int:
    return struct.unpack("<i", struct.pack("<I", value & 0xFFFFFFFF))[0]


def modules_for_lri(path: Path) -> dict[int, tuple[int, int]]:
    modules: dict[int, tuple[int, int]] = {}
    for block in AUDIT.scan_lri_blocks(str(path)):
        for module in AUDIT.field_values(block["payload"], 12, wire_type=2):
            camera_id = AUDIT.first_field(module, 2, wire_type=0)
            override = AUDIT.first_field(module, 13, wire_type=2)
            if not isinstance(camera_id, int) or not isinstance(override, bytes):
                continue
            x = AUDIT.first_field(override, 1, wire_type=0)
            y = AUDIT.first_field(override, 2, wire_type=0)
            require(isinstance(x, int) and isinstance(y, int), f"{path}: invalid Point2I")
            modules[camera_id] = (int32(x), int32(y))
    require(modules, f"{path}: no CameraModule override records")
    return modules


def verify_schema(data: bytes) -> str:
    camera = SCHEMA.decode_file_descriptor(
        data, SCHEMA.locate_descriptor(data, "camera_module.proto")
    )
    point = SCHEMA.decode_file_descriptor(
        data, SCHEMA.locate_descriptor(data, "point2i.proto")
    )
    fields = SCHEMA.field_map([camera, point])

    override = fields[".ltpb.CameraModule"][13]
    require(override["name"] == "sensor_bayer_red_override", "CameraModule field 13 name")
    require(override["type"] == "message", "CameraModule field 13 type")
    require(override["type_name"] == ".ltpb.Point2I", "CameraModule field 13 message")
    for number, name in ((1, "x"), (2, "y")):
        field = fields[".ltpb.Point2I"][number]
        require(field["name"] == name and field["type"] == "int32", f"Point2I.{name}")
    return point["serialized_sha256"]


def verify_static(data: bytes) -> None:
    mapping = STATIC.segments(data)
    raw = STATIC.bytes_at(data, mapping, 0xF2D40, 0x40)
    require(
        hashlib.sha256(raw).hexdigest()
        == "980989cf69ffec2e68d26e60cc60965bdf34a0d8604e8b2577539a37b2e09b85",
        "0xf2d40 copy window changed",
    )
    guards = {
        0xF2D4C: "41f6461004",    # source presence bit for optional Point2I
        0xF2D53: "498b4628",      # source+0x28 optional Point2I holder
        0xF2D62: "488b4818",      # holder+0x18 packed x/y
        0xF2D6D: "41894d58",      # x -> CapturedImage+0x58
        0xF2D71: "4189455c",      # y -> CapturedImage+0x5c
    }
    for va, expected_hex in guards.items():
        expected = bytes.fromhex(expected_hex)
        require(
            STATIC.bytes_at(data, mapping, va, len(expected)) == expected,
            f"copy opcode changed at 0x{va:x}",
        )


def verify_runtime() -> int:
    event_count = 0
    for tier, lri_path in AUDIT.TIERS.items():
        public = modules_for_lri(Path(lri_path))
        packet = json.loads(
            (
                ROOT
                / "runs/capturedimage_f2770_origin"
                / f"f2770_origin_{tier}.json"
            ).read_text()
        )
        require(not packet.get("errors"), f"{tier}: runtime errors")
        for event in packet["events"]:
            key = event["output_fields"]["u32_0x60"]
            source = event["input_fields"]["optional_0x28"]
            output = event["output_fields"]
            expected = public[key]
            require(source["read_ok"], f"{tier}/{key}: unreadable source override")
            require(
                (source["i32_0x18_lo"], source["i32_0x1c_hi"]) == expected,
                f"{tier}/{key}: source override mismatch",
            )
            require(
                (output["i32_0x58"], output["i32_0x5c"]) == expected,
                f"{tier}/{key}: CapturedImage override mismatch",
            )
            event_count += 1
    require(event_count == 42, f"expected 42 runtime events, got {event_count}")
    return event_count


def calibration_sha(path: Path) -> str:
    payloads = [
        block["payload"]
        for block in AUDIT.scan_lri_blocks(str(path))
        if block["payload_size"] == 32833
    ]
    require(len(payloads) == 1, f"{path}: missing Unit-2 calibration payload")
    return hashlib.sha256(payloads[0]).hexdigest()


def verify_unit2() -> None:
    expected_sign_key = {"28mm": 1, "70mm": 15}
    for tier, path in UNIT2_LRIS.items():
        require(calibration_sha(path) == EXPECTED_UNIT2_CALIB_SHA, f"{path}: body hash")
        modules = modules_for_lri(path)
        sign_keys = [key for key, pair in modules.items() if pair == (-1, -1)]
        require(sign_keys == [expected_sign_key[tier]], f"{path}: sign override key")
        expected_count = 10 if tier == "28mm" else 11
        require(len(modules) == expected_count, f"{path}: module count")


def main() -> None:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    point_sha = verify_schema(data)
    verify_static(data)
    event_count = verify_runtime()
    verify_unit2()
    print(f"static_bayer_override_public_origin=OK libcp={digest}")
    print(f"point2i_proto={point_sha}")
    print("public_field=CameraModule.sensor_bayer_red_override Point2I{x,y}")
    print(f"runtime_events={event_count} scope=28mm,35mm,70mm,150mm")
    print("sign_override_keys=A2-wide,C6-tele")
    print("unit2_public_carriers=28mm,70mm")
    print("bayer_override_public_origin=OK")


if __name__ == "__main__":
    main()
