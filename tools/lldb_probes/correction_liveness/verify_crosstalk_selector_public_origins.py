#!/usr/bin/env python3
"""Verify public origins of the selected cross-talk table selectors."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

SCHEMA_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
CCM_PATH = (
    ROOT
    / "tools/lldb_probes/ccm_illuminant_selection"
    / "verify_ccm_illuminant_selection.py"
)
AWB_PATH = ROOT / "tools/lldb_probes/awb_public_origin/verify_awb_public_origin.py"

CASES = (
    {
        "label": "unit1_28mm",
        "lri": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        "amount": ROOT / "runs/correction_liveness/amount_fit_unit1_28mm_a1/report.json",
        "ir": ROOT / "runs/correction_liveness/ir_origin_unit1_28mm_a1/report.json",
    },
    {
        "label": "unit2_28mm",
        "lri": Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
        "amount": ROOT / "runs/correction_liveness/amount_fit_unit2_28mm_a1/report.json",
        "ir": ROOT / "runs/correction_liveness/ir_origin_unit2_28mm_a1/report.json",
    },
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCHEMA = load_module("crosstalk_selector_schema", SCHEMA_PATH)
CCM = load_module("crosstalk_selector_ccm", CCM_PATH)
AWB = load_module("crosstalk_selector_awb", AWB_PATH)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def instructions(data: bytes, start: int, end: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return {
        item.address: (item.mnemonic, item.op_str)
        for item in decoder.disasm(data[start:end], start)
    }


def verify_static() -> dict:
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp SHA-256 drift: {digest}")

    expected = {
        0xE3393: ("mov", "edi, dword ptr [rsi + 0x58]"),
        0xE3A1C: ("cmp", "dword ptr [rbx + 0x20], 0"),
        0xE3A30: ("mov", "rax, qword ptr [rbx + 0x28]"),
        0xE3A34: ("mov", "rsi, qword ptr [rax + r13*8 + 8]"),
        0xE3A39: ("test", "byte ptr [rsi + 0x10], 4"),
        0xE3A3F: ("mov", "byte ptr [r12 + 0x280], 1"),
        0xF2734: ("mov", "eax, dword ptr [rdi + 0x100]"),
        0xF36C4: ("mov", "rax, qword ptr [rdi + 0xa0]"),
        0xF36CB: ("mov", "al, byte ptr [rax + 0x280]"),
        0xFE607: ("call", "0xf2730"),
        0xFE612: ("call", "0xf36c0"),
        0xFE617: ("movzx", "ecx, al"),
        0xFE637: ("call", "0xfd940"),
        0x33E91E: ("lea", "rsi, [rbx + 0xc]"),
        0x33E929: ("call", "0xab2e0"),
        0x33E9E1: ("call", "0xfe570"),
    }
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    for address, value in expected.items():
        item = next(decoder.disasm(data[address : address + 16], address))
        observed = (item.mnemonic, item.op_str)
        require(observed == value, f"0x{address:x}: {observed} != {value}")

    descriptors = SCHEMA.locate_all_descriptors(data)
    fields = SCHEMA.field_map(descriptors)
    SCHEMA.require_field(fields, ".ltpb.LightHeader", 13, "module_calibration", "message")
    SCHEMA.require_field(fields, ".ltpb.LightHeader", 16, "sensor_data", "message")
    SCHEMA.require_field(fields, ".ltpb.FactoryModuleCalibration", 2, "color", "message")
    SCHEMA.require_field(fields, ".ltpb.ColorCalibration", 3, "color_matrix", "message")
    SCHEMA.require_field(fields, ".ltpb.SensorData", 1, "type", "enum")
    sensor_signature = b"\x0a\x11sensor_type.proto"
    sensor_offset = data.find(sensor_signature)
    require(sensor_offset >= 0, "missing sensor_type.proto descriptor")
    sensor_descriptor = SCHEMA.decode_file_descriptor(data, sensor_offset)
    require(
        sensor_descriptor["serialized_sha256"]
        == "c7800a32690c4dbb09faa66d84cda8aecdb7b67a22183e3a47190e241af8b952",
        "sensor_type.proto descriptor drift",
    )
    sensor_enum = next(
        enum for enum in sensor_descriptor["enums"]
        if enum["full_name"] == ".ltpb.SensorType"
    )
    require(
        {item["number"]: item["name"] for item in sensor_enum["values"]}.get(2)
        == "SENSOR_AR1335",
        f"SensorType 2 changed: {sensor_enum}",
    )
    return {
        "libcp_sha256": digest,
        "instruction_count": len(expected),
        "variant_public_predicate": "any FactoryModuleCalibration.color[].color_matrix present",
        "sensor_public_path": "LightHeader.sensor_data[].type",
    }


def top_level_payloads(path: Path):
    data = path.read_bytes()
    offset = 0
    while offset + 32 <= len(data) and data[offset : offset + 4] == b"LELR":
        total = struct.unpack_from("<Q", data, offset + 4)[0]
        message_offset = struct.unpack_from("<Q", data, offset + 12)[0]
        message_size = struct.unpack_from("<I", data, offset + 20)[0]
        require(total > 0, f"{path}: zero LELR block size")
        yield data[offset + message_offset : offset + message_offset + message_size]
        offset += total


def values(fields, number: int, wire_type: int):
    return [value for field, wire, value in fields if field == number and wire == wire_type]


def public_sensor_types(path: Path) -> set[int]:
    result = set()
    for payload in top_level_payloads(path):
        fields, _ = SCHEMA.parse_fields(payload)
        for raw in values(fields, 16, 2):
            inner, consumed = SCHEMA.parse_fields(raw)
            require(consumed == len(raw), f"{path}: SensorData parse")
            result.update(int(value) for value in values(inner, 1, 0))
    return result


def public_color_matrix_count(path: Path) -> int:
    count = 0
    for payload in top_level_payloads(path):
        fields, _ = SCHEMA.parse_fields(payload)
        for raw_calibration in values(fields, 13, 2):
            calibration, consumed = SCHEMA.parse_fields(raw_calibration)
            require(consumed == len(raw_calibration), f"{path}: calibration parse")
            for raw_color in values(calibration, 2, 2):
                color, color_consumed = SCHEMA.parse_fields(raw_color)
                require(color_consumed == len(raw_color), f"{path}: ColorCalibration parse")
                if values(color, 3, 2):
                    count += 1
    return count


def public_scene_inputs(path: Path, camera: int = 0) -> dict:
    records = CCM.public_color_records(path)
    awb = AWB.parse_awb(path)["gains"]
    require((camera, 0) in records, f"{path}: missing camera {camera} A matrix")
    require((camera, 2) in records, f"{path}: missing camera {camera} D65 matrix")
    matrix_a = records[(camera, 0)]["color_matrix"]
    matrix_d65 = records[(camera, 2)]["color_matrix"]
    require(len(matrix_a) == 36 and len(matrix_d65) == 36, f"{path}: matrix size")
    return {
        "awb": [awb["r"], awb["g_r"], awb["b"]],
        "matrix_a_sha256": hashlib.sha256(matrix_a).hexdigest(),
        "matrix_d65_sha256": hashlib.sha256(matrix_d65).hexdigest(),
    }


def verify_case(case: dict) -> dict:
    amount = json.loads(case["amount"].read_text(encoding="ascii"))
    ir = json.loads(case["ir"].read_text(encoding="ascii"))
    require(amount["complete"] and not amount["errors"], f"{case['label']}: amount capture")
    require(ir["complete"] and not ir["errors"], f"{case['label']}: IR capture")

    sensor_types = public_sensor_types(case["lri"])
    require(sensor_types == {2}, f"{case['label']}: public sensor types {sensor_types}")
    require(amount["fit"]["sensor_type"] == 2, f"{case['label']}: fit sensor selector")
    require(ir["builder"]["sensor_type"] == 2, f"{case['label']}: builder sensor selector")

    matrix_count = public_color_matrix_count(case["lri"])
    require(matrix_count == 42, f"{case['label']}: color_matrix count {matrix_count}")
    require(amount["fit"]["variant_flag"] == 1, f"{case['label']}: fit variant")
    require(ir["builder"]["variant_flag"] == 1, f"{case['label']}: builder variant")
    require(ir["stage"]["captured_flag_a0_280"] == 1, f"{case['label']}: owner variant")

    public_inputs = public_scene_inputs(case["lri"])
    captured_xy = amount["producer"]["chromaticity_xy_primary_0xc"]
    converted_cct = amount["producer"]["xy_to_cct_tint"][0]
    captured_cct = amount["fit"]["cct_xmm0"][0]
    require(len(captured_xy) == 2, f"{case['label']}: scene xy")
    require(
        f32_bits(captured_cct) == f32_bits(converted_cct),
        f"{case['label']}: 0xab2e0 CCT does not reach the fit",
    )

    return {
        "label": case["label"],
        "sensor_type": 2,
        "sensor_name": "SENSOR_AR1335",
        "public_color_matrix_records": matrix_count,
        "variant_flag": 1,
        "public_scene_inputs": public_inputs,
        "scene_xy": captured_xy,
        "scene_cct": captured_cct,
    }


def main() -> None:
    static = verify_static()
    cases = [verify_case(case) for case in CASES]

    # The movable B2 packet uses the same scene-owner xy/CCT but independently
    # exercises camera group 1 and the C-table gate.
    b2 = json.loads(
        (ROOT / "runs/correction_liveness/amount_fit_unit1_28mm_b2_direct/report.json")
        .read_text(encoding="ascii")
    )
    require(b2["fit"]["sensor_type"] == 2 and b2["fit"]["variant_flag"] == 1, "B2 selectors")
    require(
        [f32_bits(value) for value in b2["producer"]["chromaticity_xy_primary_0xc"]]
        == [f32_bits(value) for value in cases[0]["scene_xy"]],
        "B2 scene xy differs from the Unit-1 scene owner",
    )
    require(f32_bits(b2["fit"]["cct_xmm0"][0]) == f32_bits(cases[0]["scene_cct"]), "B2 CCT")

    print(
        "crosstalk_selector_origins=OK "
        f"libcp={static['libcp_sha256']} cases={len(cases)} "
        "sensor=LightHeader.sensor_data.type:SENSOR_AR1335(2) "
        "variant=FactoryModuleCalibration.color[].color_matrix_present "
        "cct=admitted_public_scene_xy_then_installed_0xab2e0"
    )
    for case in cases:
        print(
            f"{case['label']}: OK color_matrices={case['public_color_matrix_records']} "
            f"xy={tuple(case['scene_xy'])} cct={case['scene_cct']}"
        )


if __name__ == "__main__":
    main()
