#!/usr/bin/env python3
"""Verify public LELR block roles and live preference-derived formulas."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, CS_OP_IMM, CS_OP_MEM, Cs


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
SCHEMA_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
RUNS = ROOT / "runs/lri_consumed_block_roles"
TIERS = {
    "28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "35mm": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
    "70mm": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
    "150mm": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value):
    return struct.pack("<f", value)


def fields(blob, number=None):
    result = list(parse_proto_fields(blob))
    if number is None:
        return result
    return [(wire, value) for field, wire, value in result if field == number]


def one(blob, number, wire=None):
    values = fields(blob, number)
    require(len(values) == 1, f"field {number}: expected one, got {len(values)}")
    actual_wire, value = values[0]
    if wire is not None:
        require(actual_wire == wire, f"field {number}: wire {actual_wire}, expected {wire}")
    return value


def fixed32(blob, number):
    return f32(struct.unpack("<f", struct.pack("<I", one(blob, number, 5)))[0])


def point2f(blob):
    return [fixed32(blob, 1), fixed32(blob, 2)]


def decode_preferences(blob):
    result = {}
    scalar_f32 = {
        1: "f_number",
        2: "ev_offset",
        10: "image_gain",
        17: "qc_lux_index",
        18: "display_gain",
    }
    scalar_varint = {
        3: "disable_cropping",
        4: "hdr_mode",
        5: "view_preset",
        6: "scene_mode",
        7: "awb_mode",
        9: "orientation",
        11: "image_integration_time_ns",
        12: "user_rating",
        13: "aspect_ratio",
        16: "is_on_tripod",
        19: "display_integration_time_ns",
    }
    for number, wire, value in fields(blob):
        if number in scalar_f32:
            require(wire == 5, f"ViewPreferences field {number}: expected fixed32")
            result[scalar_f32[number]] = f32(
                struct.unpack("<f", struct.pack("<I", value))[0]
            )
        elif number in scalar_varint:
            require(wire == 0, f"ViewPreferences field {number}: expected varint")
            result[scalar_varint[number]] = value
        elif number == 14:
            require(wire == 2, "ViewPreferences.crop: expected message")
            start = point2f(one(value, 1, 2))
            size = point2f(one(value, 2, 2))
            result["crop"] = [
                start[0],
                start[1],
                f32(start[0] + size[0]),
                f32(start[1] + size[1]),
            ]
        elif number == 15:
            require(wire == 2, "ViewPreferences.awb_gains: expected message")
            red = fixed32(value, 1)
            green_r = fixed32(value, 2)
            green_b = fixed32(value, 3)
            blue = fixed32(value, 4)
            result["awb_gains_rgb"] = [
                red,
                f32(f32(green_r + green_b) * f32(0.5)),
                blue,
            ]
    return result


def load_schema_module():
    spec = importlib.util.spec_from_file_location("embedded_schema", SCHEMA_PATH)
    require(spec is not None and spec.loader is not None, "cannot load schema verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def descriptor_map():
    schema = load_schema_module()
    data = LIBCP.read_bytes()
    descriptors = schema.locate_all_descriptors(data)
    enum_filename = "sensor_type.proto"
    start = schema.locate_descriptor(data, "lightheader.proto")
    require(start == 0x5C8B10, f"lightheader descriptor moved: {start:#x}")
    signature = bytes((0x0A, len(enum_filename))) + enum_filename.encode()
    enum_start = data.find(signature)
    require(enum_start >= 0, "sensor_type.proto missing")
    descriptors.append(schema.decode_file_descriptor(data, enum_start))
    by_name = {item["name"]: item for item in descriptors}
    required_hashes = {
        "lightheader.proto": "8c3795d6c609bcfe01e7302ccf385278e63dd17e63d42ef5481a47b31c81ab75",
        "sensor_characterization.proto": "0c249e4e9acbf7d4c1dcb0e3faa0ebbb8ca498f632ba263544924816f9385609",
        "sensor_type.proto": "c7800a32690c4dbb09faa66d84cda8aecdb7b67a22183e3a47190e241af8b952",
        "view_preferences.proto": "fdc7259f0c4ef618574bfcc1af27a9cc5baeb0dad08636e939228dc52be8a14a",
        "gps_data.proto": "02599ddd82395b7083312d056844c2e0bc541c28347528f2c68b4b6ff897d534",
        "flash_calibration.proto": "da4585c86b8d8c70001e960de406a69e5744c3a9e256fda22e2495aef5d2739e",
        "tof_calibration.proto": "511ba692dad1f25276351a5e0edd07a8c5849a25fdf7df860c63cfbc2246f78c",
    }
    for filename, digest in required_hashes.items():
        require(by_name[filename]["serialized_sha256"] == digest, f"{filename}: hash drift")
    message_fields = schema.field_map(descriptors)
    required_fields = [
        (".ltpb.LightHeader", 14, "device_calibration"),
        (".ltpb.LightHeader", 16, "sensor_data"),
        (".ltpb.LightHeader", 19, "view_preferences"),
        (".ltpb.SensorData", 1, "type"),
        (".ltpb.SensorData", 2, "data"),
        (".ltpb.SensorCharacterization", 1, "black_level"),
        (".ltpb.SensorCharacterization", 2, "white_level"),
        (".ltpb.SensorCharacterization", 3, "cliff_slope"),
        (".ltpb.SensorCharacterization", 4, "vst_model"),
        (".ltpb.ViewPreferences", 2, "ev_offset"),
        (".ltpb.ViewPreferences", 10, "image_gain"),
        (".ltpb.ViewPreferences", 11, "image_integration_time_ns"),
        (".ltpb.ViewPreferences", 14, "crop"),
        (".ltpb.ViewPreferences", 15, "awb_gains"),
        (".ltpb.ViewPreferences", 18, "display_gain"),
        (".ltpb.ViewPreferences", 19, "display_integration_time_ns"),
        (".ltpb.GPSData", 3, "timestamp"),
    ]
    for message, number, name in required_fields:
        require(message_fields[message][number]["name"] == name, f"{message}.{number} drift")
    sensor_enum = next(
        enum
        for enum in by_name["sensor_type.proto"]["enums"]
        if enum["full_name"] == ".ltpb.SensorType"
    )
    require(
        {"name": "SENSOR_AR1335", "number": 2} in sensor_enum["values"],
        "SensorType 2 drift",
    )
    return required_hashes


def verify_installed_parser():
    data = LIBCP.read_bytes()
    require(
        hashlib.sha256(data).hexdigest()
        == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        "libcp hash drift",
    )
    require(
        data[0x5CB190 : 0x5CB190 + 25] == b"N4ltpb15ViewPreferencesE\0",
        "ViewPreferences RTTI drift",
    )
    require(data.startswith(b"N4ltpb7GPSDataE\0", 0x5CB98A), "GPSData RTTI drift")
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    md.skipdata = True
    direct_calls = {}
    for instruction in md.disasm(data[0x2250:0x555D20], 0x2250):
        if (
            instruction.mnemonic == "call"
            and instruction.operands
            and instruction.operands[0].type == CS_OP_IMM
        ):
            direct_calls.setdefault(instruction.operands[0].imm, []).append(
                instruction.address
            )
    require(direct_calls.get(0x13CC80) == [0xE532C], "LELR parser caller drift")
    require(0x13CDEF in direct_calls.get(0x180A50, []), "type-1 constructor drift")
    require(0x13CDC7 in direct_calls.get(0x187170, []), "type-2 constructor drift")
    require(
        direct_calls.get(0xE7690) == [0x419D6D, 0x419D7E],
        "GPS accessor caller set drift",
    )

    flash_field_reads = []
    for instruction in md.disasm(data[0xE52C0:0xE5F8C], 0xE52C0):
        for operand in instruction.operands:
            if operand.type != CS_OP_MEM:
                continue
            memory = operand.mem
            if instruction.reg_name(memory.base) == "rbx" and memory.disp == 0xD0:
                flash_field_reads.append(instruction.address)
    require(
        not flash_field_reads,
        f"CaptureStack merge unexpectedly reads LightHeader+0xd0: {flash_field_reads}",
    )
    return {
        "parser_call": "0xe532c->0x13cc80",
        "type1_view_preferences_constructor": "0x13cdef->0x180a50",
        "type2_gps_constructor": "0x13cdc7->0x187170",
        "gps_accessor_callers": ["0x419d6d", "0x419d7e"],
        "flash_field_reads_in_capture_stack_merge": flash_field_reads,
    }


def classify_lri(path):
    blocks = scan_lri_blocks(str(path))
    merged_preferences = {}
    inventory = []
    sensor = None
    device = None
    gps = []
    for block in blocks:
        payload = block["payload"]
        record_type = block["msg_type"]
        top = [(number, wire) for number, wire, _value in fields(payload)]
        role = None
        if record_type == 1:
            role = "standalone_view_preferences"
            merged_preferences.update(decode_preferences(payload))
        elif record_type == 2:
            role = "standalone_gps_data"
            gps.append(
                {
                    "fields": top,
                    "timestamp": one(payload, 3, 0),
                }
            )
        else:
            require(record_type == 0, f"{path}: unexpected record type {record_type}")
            preference_values = fields(payload, 19)
            for wire, value in preference_values:
                require(wire == 2, "LightHeader.view_preferences wire drift")
                merged_preferences.update(decode_preferences(value))
            module_calibrations = [value for wire, value in fields(payload, 13) if wire == 2]
            modules = [value for wire, value in fields(payload, 12) if wire == 2]
            if block["msg_offset"] > 32 and modules:
                role = "raw_sensor_chunk_lightheader"
            elif module_calibrations:
                nested_fields = {
                    number
                    for calibration in module_calibrations
                    for number, _wire, _value in fields(calibration)
                }
                if 3 in nested_fields:
                    role = "geometry_calibration"
                elif 4 in nested_fields:
                    role = "vignetting_calibration"
                elif 2 in nested_fields:
                    role = "color_calibration"
                else:
                    role = "module_calibration_other"
            elif fields(payload, 16):
                role = "sensor_characterization"
                sensor_data = one(payload, 16, 2)
                characterization = one(sensor_data, 2, 2)
                models = [value for wire, value in fields(characterization, 4) if wire == 2]
                sensor = {
                    "type": one(sensor_data, 1, 0),
                    "black_level": fixed32(characterization, 1),
                    "white_level": fixed32(characterization, 2),
                    "cliff_slope": fixed32(characterization, 3),
                    "model_count": len(models),
                    "gain_keys": [one(model, 1, 0) for model in models],
                }
            elif fields(payload, 14):
                role = "device_calibration"
                calibration = one(payload, 14, 2)
                flash = one(calibration, 1, 2)
                device = {
                    "fields": [(number, wire) for number, wire, _value in fields(calibration)],
                    "flash": [fixed32(flash, number) for number in range(1, 7)],
                }
            elif preference_values:
                role = "wrapped_view_preferences"
            else:
                role = "lightheader_fragment"
        inventory.append(
            {
                "index": block["idx"],
                "type": record_type,
                "payload_size": block["payload_size"],
                "total_size": block["total_size"],
                "role": role,
                "top_fields": top,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    require(sensor is not None, f"{path}: sensor characterization missing")
    require(device is not None, f"{path}: device calibration missing")
    require(gps, f"{path}: GPS record missing")
    return {
        "inventory": inventory,
        "preferences": merged_preferences,
        "sensor": sensor,
        "device": device,
        "gps": gps,
    }


def compare_optional(runtime, key, public, public_key=None):
    public_key = public_key or key
    item = runtime[key]
    expected_present = public_key in public
    require(item["present"] == expected_present, f"{key}: presence mismatch")
    if not expected_present:
        return
    expected = public[public_key]
    actual = item["value"]
    if isinstance(expected, list):
        require(len(actual) == len(expected), f"{key}: vector length")
        for lhs, rhs in zip(actual, expected):
            require(f32_bits(lhs) == f32_bits(rhs), f"{key}: {lhs} != {rhs}")
    elif isinstance(expected, float):
        require(f32_bits(actual) == f32_bits(expected), f"{key}: {actual} != {expected}")
    else:
        require(actual == expected, f"{key}: {actual} != {expected}")


def verify_runtime(tier, decoded):
    report_path = RUNS / f"unit1_{tier}.json"
    report = json.loads(report_path.read_text())
    require(not report["errors"], f"{tier}: probe errors {report['errors']}")
    expected_dispatch = [
        (item["type"], item["payload_size"]) for item in decoded["inventory"]
    ]
    actual_dispatch = [
        (item["type"], item["message_size"]) for item in report["record_dispatches"]
    ]
    require(actual_dispatch == expected_dispatch, f"{tier}: runtime record dispatch mismatch")
    require(len(report["preference_merges"]) == 3, f"{tier}: preference merge count")
    require(len(report["merged_preferences"]) == 1, f"{tier}: merged preference packet")
    runtime = report["merged_preferences"][0]
    public = decoded["preferences"]
    for key in (
        "f_number",
        "ev_offset",
        "disable_cropping",
        "awb_gains_rgb",
        "awb_mode",
        "orientation",
        "image_gain",
        "image_integration_time_ns",
        "display_gain",
        "display_integration_time_ns",
        "user_rating",
        "aspect_ratio",
        "crop",
    ):
        runtime_key = key
        if key == "user_rating" and key not in runtime:
            runtime_key = "is_on_tripod"  # reports captured before the label correction
        compare_optional(runtime, runtime_key, public, key)
    counts = report["counts"]
    for key in (
        "crop_accessor",
        "disable_cropping_accessor",
        "awb_gains_accessor",
        "orientation_accessor",
        "image_gain_accessor",
        "image_integration_accessor",
        "crop_policy_entry",
    ):
        require(counts[key] > 0, f"{tier}: {key} not live")
    for key in (
        "ev_offset_accessor",
        "display_gain_accessor",
        "display_integration_accessor",
        "aspect_ratio_accessor",
    ):
        require(counts[key] == 0, f"{tier}: unexpected {key} liveness")
    require(counts.get("gps_accessor", 0) == 0, f"{tier}: GPS accessor live")
    require(report["crop_policy"][0]["result"] == runtime["crop"]["value"], f"{tier}: crop")
    require(report["exposure_normalization"], f"{tier}: no exposure-normalization packets")
    for packet in report["exposure_normalization"]:
        if "captured_image" not in packet or "sensor_exposure" not in packet:
            continue
        denominator = f32(
            f32(float(packet["sensor_exposure"])) * f32(packet["sensor_analog_gain"])
        )
        numerator = f32(
            f32(float(public["image_integration_time_ns"])) * f32(public["image_gain"])
        )
        expected = f32(numerator / denominator)
        require(
            f32_bits(packet["result"]) == f32_bits(expected),
            f"{tier}: exposure normalization mismatch",
        )
    return {
        "record_count": len(decoded["inventory"]),
        "roles": [item["role"] for item in decoded["inventory"]],
        "preferences": public,
        "live_counts": {key: value for key, value in counts.items() if value},
        "sensor": decoded["sensor"],
        "device": decoded["device"],
        "gps_fields": decoded["gps"][0]["fields"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    descriptor_hashes = descriptor_map()
    installed_parser = verify_installed_parser()
    results = {}
    for tier, path in TIERS.items():
        decoded = classify_lri(path)
        results[tier] = verify_runtime(tier, decoded)
    sensor_hashes = {
        hashlib.sha256(
            json.dumps(result["sensor"], sort_keys=True).encode()
        ).hexdigest()
        for result in results.values()
    }
    require(len(sensor_hashes) == 1, "canonical sensor characterization drift")
    header_records = json.loads((RUNS / "unit1_28mm.json").read_text()).get(
        "header_records", []
    )
    flash_matches = [
        match
        for record in header_records
        for match in record.get("flash_pointer_matches", [])
    ]
    require(len(flash_matches) == 1, "expected one parsed flash-calibration object")
    require(
        flash_matches[0]["record_offset"] == 0xD0
        and flash_matches[0]["first_flash_offset"] == 0x48,
        "flash-calibration generated-object custody drift",
    )
    output = {
        "status": "PASS",
        "libcp_sha256": hashlib.sha256(LIBCP.read_bytes()).hexdigest(),
        "descriptor_hashes": descriptor_hashes,
        "installed_parser": installed_parser,
        "flash_generated_object": {
            "lightheader_offset": flash_matches[0]["record_offset"],
            "first_float_offset": flash_matches[0]["first_flash_offset"],
        },
        "tiers": results,
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print("lri_consumed_block_roles=OK")
        for tier, result in results.items():
            print(
                f"{tier}: records={result['record_count']} "
                f"roles={','.join(result['roles'])} "
                f"crop={result['preferences']['crop']} "
                f"image_target=({result['preferences']['image_integration_time_ns']},"
                f"{result['preferences']['image_gain']})"
            )


if __name__ == "__main__":
    main()
