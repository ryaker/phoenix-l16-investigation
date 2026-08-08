#!/usr/bin/env python3
"""Extract selected serialized protobuf schemas embedded in libcp.dylib.

This verifier has no protobuf-runtime dependency.  It decodes the generated
FileDescriptorProto byte strings directly and prints the exact field number,
name, label, type, and referenced message/enum name for selected schemas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any


DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)

LABELS = {1: "optional", 2: "required", 3: "repeated"}
TYPES = {
    1: "double",
    2: "float",
    3: "int64",
    4: "uint64",
    5: "int32",
    6: "fixed64",
    7: "fixed32",
    8: "bool",
    9: "string",
    10: "group",
    11: "message",
    12: "bytes",
    13: "uint32",
    14: "enum",
    15: "sfixed32",
    16: "sfixed64",
    17: "sint32",
    18: "sint64",
}

TARGET_FILES = (
    "camera_module.proto",
    "geometric_calibration.proto",
    "lightheader.proto",
)


def read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data) and shift <= 63:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
    raise ValueError("truncated or oversized varint")


def parse_fields(data: bytes, offset: int = 0, end: int | None = None) -> tuple[list[tuple[int, int, Any]], int]:
    if end is None:
        end = len(data)
    fields: list[tuple[int, int, Any]] = []
    cursor = offset
    while cursor < end:
        tag, after_tag = read_varint(data, cursor)
        number = tag >> 3
        wire_type = tag & 7
        if number == 0 or wire_type in (3, 4, 6, 7):
            break
        cursor = after_tag
        if wire_type == 0:
            value, cursor = read_varint(data, cursor)
        elif wire_type == 1:
            if cursor + 8 > end:
                raise ValueError("truncated fixed64")
            value = data[cursor : cursor + 8]
            cursor += 8
        elif wire_type == 2:
            size, cursor = read_varint(data, cursor)
            if cursor + size > end:
                raise ValueError("truncated length-delimited field")
            value = data[cursor : cursor + size]
            cursor += size
        elif wire_type == 5:
            if cursor + 4 > end:
                raise ValueError("truncated fixed32")
            value = data[cursor : cursor + 4]
            cursor += 4
        fields.append((number, wire_type, value))
    return fields, cursor


def first(fields: list[tuple[int, int, Any]], number: int, default: Any = None) -> Any:
    for field_number, _wire_type, value in fields:
        if field_number == number:
            return value
    return default


def all_values(fields: list[tuple[int, int, Any]], number: int) -> list[Any]:
    return [value for field_number, _wire_type, value in fields if field_number == number]


def text_value(value: bytes | None) -> str | None:
    return value.decode("utf-8") if value is not None else None


def decode_field(data: bytes) -> dict[str, Any]:
    fields, consumed = parse_fields(data)
    if consumed != len(data):
        raise ValueError("FieldDescriptorProto did not decode completely")
    type_id = first(fields, 5)
    raw_options = first(fields, 8)
    packed = None
    if raw_options is not None:
        options, options_consumed = parse_fields(raw_options)
        if options_consumed != len(raw_options):
            raise ValueError("FieldOptions did not decode completely")
        packed_value = first(options, 2)
        if packed_value is not None:
            packed = bool(packed_value)
    return {
        "name": text_value(first(fields, 1)),
        "number": first(fields, 3),
        "label": LABELS.get(first(fields, 4), f"label_{first(fields, 4)}"),
        "type": TYPES.get(type_id, f"type_{type_id}"),
        "type_name": text_value(first(fields, 6)),
        "default_value": text_value(first(fields, 7)),
        "packed": packed,
    }


def decode_enum(data: bytes, prefix: str) -> dict[str, Any]:
    fields, consumed = parse_fields(data)
    if consumed != len(data):
        raise ValueError("EnumDescriptorProto did not decode completely")
    name = text_value(first(fields, 1))
    values = []
    for raw_value in all_values(fields, 2):
        value_fields, value_consumed = parse_fields(raw_value)
        if value_consumed != len(raw_value):
            raise ValueError("EnumValueDescriptorProto did not decode completely")
        values.append({"name": text_value(first(value_fields, 1)), "number": first(value_fields, 2)})
    return {"full_name": f"{prefix}.{name}", "values": values}


def decode_message(data: bytes, prefix: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fields, consumed = parse_fields(data)
    if consumed != len(data):
        raise ValueError("DescriptorProto did not decode completely")
    name = text_value(first(fields, 1))
    full_name = f"{prefix}.{name}"
    messages = [{"full_name": full_name, "fields": [decode_field(raw) for raw in all_values(fields, 2)]}]
    enums = [decode_enum(raw, full_name) for raw in all_values(fields, 4)]
    for nested in all_values(fields, 3):
        nested_messages, nested_enums = decode_message(nested, full_name)
        messages.extend(nested_messages)
        enums.extend(nested_enums)
    return messages, enums


def decode_file_descriptor(data: bytes, start: int) -> dict[str, Any]:
    fields, end = parse_fields(data, start)
    name = text_value(first(fields, 1))
    package = text_value(first(fields, 2)) or ""
    prefix = f".{package}" if package else ""
    messages: list[dict[str, Any]] = []
    enums: list[dict[str, Any]] = []
    for raw_message in all_values(fields, 4):
        decoded_messages, decoded_enums = decode_message(raw_message, prefix)
        messages.extend(decoded_messages)
        enums.extend(decoded_enums)
    for raw_enum in all_values(fields, 5):
        enums.append(decode_enum(raw_enum, prefix))
    return {
        "name": name,
        "package": package,
        "dependencies": [text_value(value) for value in all_values(fields, 3)],
        "file_offset": start,
        "serialized_size": end - start,
        "serialized_sha256": hashlib.sha256(data[start:end]).hexdigest(),
        "messages": messages,
        "enums": enums,
    }


def locate_descriptor(data: bytes, filename: str) -> int:
    encoded = filename.encode("utf-8")
    if len(encoded) >= 0x80:
        raise ValueError("filename signature requires multi-byte length")
    signature = bytes((0x0A, len(encoded))) + encoded
    starts = []
    cursor = 0
    while True:
        found = data.find(signature, cursor)
        if found < 0:
            break
        starts.append(found)
        cursor = found + 1
    if not starts:
        raise AssertionError(f"missing embedded descriptor for {filename}")
    for start in starts:
        try:
            descriptor = decode_file_descriptor(data, start)
        except (UnicodeDecodeError, ValueError):
            continue
        if descriptor["name"] == filename and descriptor["messages"]:
            return start
    raise AssertionError(f"no decodable embedded descriptor for {filename}; candidates={starts}")


def locate_all_descriptors(data: bytes) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    pattern = re.compile(rb"\x0a([\x01-\x7f])([A-Za-z0-9_./-]+\.proto)")
    for match in pattern.finditer(data):
        filename_bytes = match.group(2)
        if match.group(1)[0] != len(filename_bytes):
            continue
        try:
            descriptor = decode_file_descriptor(data, match.start())
        except (UnicodeDecodeError, ValueError):
            continue
        filename = filename_bytes.decode("utf-8")
        if descriptor["name"] == filename and descriptor["messages"]:
            found[filename] = descriptor
    return [found[name] for name in sorted(found)]


def verify_depth_public_boundary(data: bytes, descriptors: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {descriptor["name"]: descriptor for descriptor in descriptors}
    stereo = by_name.get("stereo_state.proto")
    if not stereo:
        raise AssertionError("missing stereo_state.proto descriptor")
    fields = field_map([stereo])
    require_field(fields, ".ltpb.Stereo", 1, "depth_format", "enum")
    require_field(fields, ".ltpb.Stereo", 2, "depth_offset", "uint64")
    require_field(fields, ".ltpb.Stereo", 3, "depth_level", "uint32")
    depth_format = next(
        (enum for enum in stereo["enums"] if enum["full_name"] == ".ltpb.DepthFormat"),
        None,
    )
    if not depth_format or depth_format["values"] != [{"name": "Float32", "number": 0}]:
        raise AssertionError(f"unexpected DepthFormat enum: {depth_format}")

    public_field_names = [
        field["name"]
        for descriptor in descriptors
        for message in descriptor["messages"]
        for field in message["fields"]
    ]
    near_far_names = sorted(
        name for name in public_field_names if re.search(r"(^|_)(near|far)($|_)", name, re.IGNORECASE)
    )
    range_inverse = b'GDepth:Format="RangeInverse"' in data
    units_mm = b'GDepth:Units="mm"' in data
    if not range_inverse or not units_mm:
        raise AssertionError("installed GDepth RangeInverse/mm export metadata missing")
    return {
        "embedded_descriptor_count": len(descriptors),
        "stereo_descriptor_sha256": stereo["serialized_sha256"],
        "stereo_fields": fields[".ltpb.Stereo"],
        "depth_format_values": depth_format["values"],
        "protobuf_near_far_field_names": near_far_names,
        "gdepth_range_inverse_string": range_inverse,
        "gdepth_units_mm_string": units_mm,
    }


def field_map(descriptors: list[dict[str, Any]]) -> dict[str, dict[int, dict[str, Any]]]:
    result: dict[str, dict[int, dict[str, Any]]] = {}
    for descriptor in descriptors:
        for message in descriptor["messages"]:
            result[message["full_name"]] = {field["number"]: field for field in message["fields"]}
    return result


def require_field(
    fields: dict[str, dict[int, dict[str, Any]]],
    message: str,
    number: int,
    name: str,
    type_name: str,
) -> None:
    field = fields.get(message, {}).get(number)
    if not field:
        raise AssertionError(f"missing {message} field {number}")
    if field["name"] != name or field["type"] != type_name:
        raise AssertionError(f"unexpected {message} field {number}: {field}")


def verify(descriptors: list[dict[str, Any]]) -> None:
    fields = field_map(descriptors)
    require_field(fields, ".ltpb.CameraModule", 2, "id", "enum")
    require_field(fields, ".ltpb.CameraModule", 3, "is_enabled", "bool")
    if fields[".ltpb.CameraModule"][3]["default_value"] != "true":
        raise AssertionError("unexpected CameraModule.is_enabled default")
    require_field(fields, ".ltpb.CameraModule", 4, "mirror_position", "int32")
    require_field(fields, ".ltpb.CameraModule", 5, "lens_position", "int32")
    require_field(fields, ".ltpb.CameraModule", 8, "sensor_exposure", "uint64")
    require_field(fields, ".ltpb.CameraModule", 9, "sensor_data_surface", "message")
    require_field(fields, ".ltpb.CameraModule", 10, "sensor_temparature", "sint32")
    require_field(fields, ".ltpb.CameraModule.Surface", 2, "size", "message")

    require_field(fields, ".ltpb.GeometricCalibration", 2, "per_focus_calibration", "message")
    require_field(fields, ".ltpb.GeometricCalibration", 3, "distortion", "message")
    require_field(fields, ".ltpb.GeometricCalibration.CalibrationFocusBundle", 1, "focus_distance", "float")
    require_field(fields, ".ltpb.GeometricCalibration.CalibrationFocusBundle", 2, "intrinsics", "message")
    require_field(fields, ".ltpb.GeometricCalibration.CalibrationFocusBundle", 3, "extrinsics", "message")
    require_field(fields, ".ltpb.GeometricCalibration.CalibrationFocusBundle", 6, "focus_hall_code", "float")
    require_field(fields, ".ltpb.GeometricCalibration.Intrinsics", 1, "k_mat", "message")
    require_field(fields, ".ltpb.GeometricCalibration.Extrinsics.CanonicalFormat", 1, "rotation", "message")
    require_field(fields, ".ltpb.GeometricCalibration.Extrinsics.CanonicalFormat", 2, "translation", "message")

    require_field(fields, ".ltpb.FactoryModuleCalibration", 1, "camera_id", "enum")
    require_field(fields, ".ltpb.FactoryModuleCalibration", 3, "geometry", "message")
    require_field(fields, ".ltpb.LightHeader", 5, "image_reference_camera", "enum")
    require_field(fields, ".ltpb.LightHeader", 12, "modules", "message")
    require_field(fields, ".ltpb.LightHeader", 13, "module_calibration", "message")


def fields_by_number(data: bytes) -> dict[int, list[tuple[int, Any]]]:
    fields, consumed = parse_fields(data)
    if consumed != len(data):
        raise ValueError(f"protobuf payload did not decode completely: {consumed}/{len(data)}")
    result: dict[int, list[tuple[int, Any]]] = {}
    for number, wire_type, value in fields:
        result.setdefault(number, []).append((wire_type, value))
    return result


def one_field(fields: dict[int, list[tuple[int, Any]]], number: int, wire_type: int) -> Any:
    values = fields.get(number, [])
    if len(values) != 1 or values[0][0] != wire_type:
        raise AssertionError(f"expected one field {number} with wire type {wire_type}; got {values}")
    return values[0][1]


def zigzag32(value: int) -> int:
    return (value >> 1) ^ -(value & 1)


def walk_lri_payloads(path: Path):
    file_size = path.stat().st_size
    with path.open("rb") as handle:
        offset = 0
        index = 0
        while offset + 32 <= file_size:
            handle.seek(offset)
            header = handle.read(32)
            if len(header) != 32 or header[:4] != b"LELR":
                break
            total_size = struct.unpack_from("<Q", header, 4)[0]
            message_offset = struct.unpack_from("<Q", header, 12)[0]
            message_size = struct.unpack_from("<I", header, 20)[0]
            if not total_size:
                break
            if message_offset + message_size > total_size:
                raise AssertionError(f"{path}: block {index} message exceeds block")
            handle.seek(offset + message_offset)
            payload = handle.read(message_size)
            if len(payload) != message_size:
                raise AssertionError(f"{path}: block {index} message truncated")
            yield index, payload
            offset += total_size
            index += 1


def verify_lri(path: Path) -> dict[str, Any]:
    module_rows: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    calibration_payloads: list[dict[str, Any]] = []

    for block_index, payload in walk_lri_payloads(path):
        top = fields_by_number(payload)
        for wire_type, raw_module in top.get(12, []):
            if wire_type != 2:
                continue
            module = fields_by_number(raw_module)
            camera_id = one_field(module, 2, 0)
            is_enabled_explicit = 3 in module
            is_enabled = bool(one_field(module, 3, 0)) if is_enabled_explicit else True
            mirror_position = one_field(module, 4, 0) if 4 in module else 0
            lens_position = one_field(module, 5, 0)
            sensor_exposure = one_field(module, 8, 0)
            surface = fields_by_number(one_field(module, 9, 2))
            size = fields_by_number(one_field(surface, 2, 2))
            width = one_field(size, 1, 0)
            height = one_field(size, 2, 0)
            raw_temperature = one_field(module, 10, 0) if 10 in module else None
            module_rows.append(
                {
                    "block": block_index,
                    "id": camera_id,
                    "is_enabled": is_enabled,
                    "is_enabled_explicit": is_enabled_explicit,
                    "mirror_position": mirror_position,
                    "lens_position": lens_position,
                    "sensor_exposure": sensor_exposure,
                    "sensor_temparature": zigzag32(raw_temperature) if raw_temperature is not None else None,
                    "sensor_data_surface_size": [width, height],
                }
            )

        block_calibration_count = 0
        block_focus_bundle_count = 0
        block_focus_hall_count = 0
        for wire_type, raw_calibration in top.get(13, []):
            if wire_type != 2:
                continue
            calibration = fields_by_number(raw_calibration)
            camera_id = one_field(calibration, 1, 0)
            if 3 not in calibration:
                continue
            geometry = fields_by_number(one_field(calibration, 3, 2))
            bundles = geometry.get(2, [])
            focus_rows = []
            for bundle_wire_type, raw_bundle in bundles:
                if bundle_wire_type != 2:
                    raise AssertionError(f"{path}: per_focus_calibration has wire type {bundle_wire_type}")
                bundle = fields_by_number(raw_bundle)
                focus_distance_raw = one_field(bundle, 1, 5)
                focus_distance = struct.unpack("<f", focus_distance_raw)[0]
                focus_hall_raw = one_field(bundle, 6, 5) if 6 in bundle else None
                focus_hall_code = struct.unpack("<f", focus_hall_raw)[0] if focus_hall_raw is not None else None
                if 2 in bundle:
                    intrinsics = fields_by_number(one_field(bundle, 2, 2))
                    one_field(intrinsics, 1, 2)
                if 3 in bundle:
                    extrinsics = fields_by_number(one_field(bundle, 3, 2))
                    if 1 in extrinsics:
                        canonical = fields_by_number(one_field(extrinsics, 1, 2))
                        one_field(canonical, 1, 2)
                        one_field(canonical, 2, 2)
                focus_rows.append(
                    {"focus_distance": focus_distance, "focus_hall_code": focus_hall_code}
                )
                block_focus_bundle_count += 1
                block_focus_hall_count += focus_hall_code is not None
            calibration_rows.append(
                {"block": block_index, "camera_id": camera_id, "per_focus_calibration": focus_rows}
            )
            block_calibration_count += 1
        if block_calibration_count:
            calibration_payloads.append(
                {
                    "block": block_index,
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "module_count": block_calibration_count,
                    "focus_bundle_count": block_focus_bundle_count,
                    "focus_hall_code_count": block_focus_hall_count,
                }
            )

    if not module_rows:
        raise AssertionError(f"{path}: no LightHeader.modules records")
    if sorted(row["id"] for row in module_rows) != sorted(set(row["id"] for row in module_rows)):
        raise AssertionError(f"{path}: duplicate module IDs across image chunks")
    if any(row["sensor_data_surface_size"] != [4160, 3120] for row in module_rows):
        raise AssertionError(f"{path}: unexpected sensor_data_surface.size")
    if not all(row["is_enabled"] for row in module_rows):
        raise AssertionError(f"{path}: disabled module in fired LightHeader.modules")
    if not all(row["is_enabled_explicit"] for row in module_rows):
        raise AssertionError(f"{path}: sampled module omits explicit is_enabled")
    if len(calibration_rows) != 16 or sorted(row["camera_id"] for row in calibration_rows) != list(range(16)):
        raise AssertionError(f"{path}: expected module_calibration camera IDs 0..15")
    if not calibration_payloads or not any(row["focus_hall_code_count"] for row in calibration_payloads):
        raise AssertionError(f"{path}: no named focus_hall_code calibration values")

    return {
        "path": str(path),
        "module_ids": [row["id"] for row in module_rows],
        "modules": module_rows,
        "calibration_payloads": calibration_payloads,
        "module_calibration_count": len(calibration_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    parser.add_argument("--lri", action="append", type=Path, default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = args.libcp.read_bytes()
    descriptors = [decode_file_descriptor(data, locate_descriptor(data, name)) for name in TARGET_FILES]
    verify(descriptors)
    all_descriptors = locate_all_descriptors(data)
    depth_public_boundary = verify_depth_public_boundary(data, all_descriptors)
    lri_reports = [verify_lri(path) for path in args.lri]

    if args.json:
        print(
            json.dumps(
                {
                    "libcp": str(args.libcp),
                    "descriptors": descriptors,
                    "depth_public_boundary": depth_public_boundary,
                    "lris": lri_reports,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"libcp_sha256={hashlib.sha256(data).hexdigest()}")
        for descriptor in descriptors:
            print(
                f"{descriptor['name']}: offset=0x{descriptor['file_offset']:x} "
                f"size={descriptor['serialized_size']} sha256={descriptor['serialized_sha256']}"
            )
            for message in descriptor["messages"]:
                print(message["full_name"])
                for field in message["fields"]:
                    suffix = f" {field['type_name']}" if field["type_name"] else ""
                    print(
                        f"  {field['number']}: {field['label']} {field['type']} "
                        f"{field['name']}{suffix}"
                    )
        for report in lri_reports:
            payloads = ",".join(
                f"block{row['block']}:{row['size']}:{row['sha256'][:16]}"
                for row in report["calibration_payloads"]
            )
            print(
                f"LRI {report['path']}: modules={report['module_ids']} "
                f"module_calibration={report['module_calibration_count']} payloads={payloads}"
            )
        print(
            "depth_public_boundary="
            f"descriptors:{depth_public_boundary['embedded_descriptor_count']},"
            "Stereo.depth_format:Float32,"
            f"proto_near_far_names:{depth_public_boundary['protobuf_near_far_field_names']},"
            "GDepth:RangeInverse/mm"
        )
        print("embedded_calibration_proto_schema=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
