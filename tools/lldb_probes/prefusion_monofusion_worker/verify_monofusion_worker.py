#!/usr/bin/env python3
"""Verify MonoFusion mode-0 public inputs and installed formula custody."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
SCHEMA_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
DEFAULT_LRIS = {
    "unit1_28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "unit1_35mm": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
    "unit2_28mm": Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
}
EXPECTED_CAPTURE = {
    "unit1_28mm": (1.5, 1.015625, 14639008),
    "unit1_35mm": (1.0, 1.0, 2606820),
    "unit2_28mm": (7.75, 1.0, 42005140),
}
EXPECTED_TARGET = {
    "unit1_28mm": (1.0, 1.0, 11238709),
    "unit1_35mm": (1.0, 1.0, 1301331),
    "unit2_28mm": (3.875, 1.0, 42009320),
}
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
COEFFICIENT_WEIGHT_SHA256 = "3eebf27ff044f8a715e45ab3fe17972728f2bf0e596d1259d7d2aa3d25c85ca4"
PANCHROMATIC_TABLE_VA = 0x5AD7C0
PANCHROMATIC_TABLE_SIZE = 28 * 0x20
PANCHROMATIC_TABLE_SHA256 = "e0e40ce025012b1df9c96d0ad59d00f45722d521c48a3bc04de806ae3467d878"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("monofusion_static", STATIC_PATH)
SCHEMA = load_module("monofusion_schema", SCHEMA_PATH)


def f32(raw: bytes) -> float:
    return struct.unpack("<f", raw)[0]


def round_f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def field_f32(fields, number: int) -> float:
    return f32(SCHEMA.one_field(fields, number, 5))


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify_schema(data: bytes) -> dict:
    descriptors = SCHEMA.locate_all_descriptors(data)
    fields = SCHEMA.field_map(descriptors)
    expected = (
        (".ltpb.LightHeader", 16, "sensor_data", "message"),
        (".ltpb.CameraModule", 7, "sensor_analog_gain", "float"),
        (".ltpb.CameraModule", 8, "sensor_exposure", "uint64"),
        (".ltpb.CameraModule", 13, "sensor_bayer_red_override", "message"),
        (".ltpb.CameraModule", 14, "sensor_digital_gain", "float"),
        (".ltpb.SensorData", 1, "type", "enum"),
        (".ltpb.SensorData", 2, "data", "message"),
        (".ltpb.SensorCharacterization", 1, "black_level", "float"),
        (".ltpb.SensorCharacterization", 2, "white_level", "float"),
        (".ltpb.SensorCharacterization", 3, "cliff_slope", "float"),
        (".ltpb.SensorCharacterization", 4, "vst_model", "message"),
        (".ltpb.SensorCharacterization.VstNoiseModel", 1, "gain", "uint32"),
        (".ltpb.SensorCharacterization.VstNoiseModel", 2, "threshold", "float"),
        (".ltpb.SensorCharacterization.VstNoiseModel", 3, "scale", "float"),
        (".ltpb.SensorCharacterization.VstNoiseModel", 7, "panchromatic", "message"),
        (".ltpb.SensorCharacterization.VstNoiseModel.VstModel", 1, "a", "float"),
        (".ltpb.SensorCharacterization.VstNoiseModel.VstModel", 2, "b", "float"),
    )
    for message, number, name, field_type in expected:
        SCHEMA.require_field(fields, message, number, name, field_type)
    sensor_filename = b"sensor_type.proto"
    sensor_offset = data.index(bytes((0x0A, len(sensor_filename))) + sensor_filename)
    sensor_type = SCHEMA.decode_file_descriptor(data, sensor_offset)
    expected_sensor_types = [
        {"name": "SENSOR_UNKNOWN", "number": 0},
        {"name": "SENSOR_AR835", "number": 1},
        {"name": "SENSOR_AR1335", "number": 2},
        {"name": "SENSOR_AR1335_MONO", "number": 3},
        {"name": "SENSOR_IMX386", "number": 4},
        {"name": "SENSOR_IMX386_MONO", "number": 5},
    ]
    require(
        sensor_type["enums"]
        == [{"full_name": ".ltpb.SensorType", "values": expected_sensor_types}],
        "SensorType enum changed",
    )
    return {
        "sensor_data": fields[".ltpb.SensorData"],
        "sensor_characterization": fields[".ltpb.SensorCharacterization"],
        "vst_noise_model": fields[".ltpb.SensorCharacterization.VstNoiseModel"],
        "sensor_type": expected_sensor_types,
    }


def verify_static(data: bytes, mapping) -> None:
    windows = {
        (0x1B17C0, 0x1B2730): "110546b1cb4417ed765e49562531481db1719479af577980f9cc3ade02710f23",
        (0x1B37A0, 0x1B3CD0): "5c548a46b6b2d3d7468de9083aa89b082a48abdd62411bb004ad7ee1d3c74ccc",
        (0x1A3C00, 0x1A4DE0): "b340bbcc8191a708cfe7872f2c57cd2efbe9c675ee01a294b132674f6445f855",
        (0x18CE50, 0x18CEA0): "bec1729da0e34dcde9b69b76021ec4330acfaa3bd4fb30c484aa782d7254ac26",
        (0x18DA80, 0x18DC20): "4ba05579f24e311e23ad8fddcb56a3e749bcae331e3a7255b70493d9a611d6e9",
        (0x18E940, 0x18EA20): "40bd296eaa1c0d0c4405971c5c3508c8c5900e1744255c5962bd4ef6f43b12cc",
        (0x1A28F0, 0x1A2C10): "960205b48b16561cd498e8415fa456d61890faa4a1a068eb15a121a3f6046ce4",
        (0x1A2C10, 0x1A2FF0): "f58f4d6380855b24bb1bbb21fffa418b45ca9fc16f9fa7461767d012fbc98ab2",
        (0x1908B0, 0x190DA0): "fa0a42c2cffd6d7d42c6bc115800dc8ef08949bf04ec4d1344aaa15a4d541c55",
        (0x1A7F20, 0x1A8320): "ddbe94f0fbf63d00175abde84e96a6ee749577e7e37d4eaf4b9beefd4cc5908a",
        (0x1B3CD0, 0x1B3D60): "6b8cadf4d1ba141ec6d99a43b2d4b65580d6a7d0667742a6adafaf6f209d9077",
        (0x1B4390, 0x1B4430): "2a979db03d280a8005fb3fc6db09f6ed57c62e54a7dfdabdef6250ce13d3ad30",
        (0xEF050, 0xEF120): "bcdeed373cdd1debf67354bbf0cd04bd067cb4b1ea7462e5ccf0cbc682fe6b20",
        (0xE67C0, 0xE6AD4): "35340dd189966c98250bc435264e27cba69d74cba5feaec633e8451be6a96ae8",
        (0xEF820, 0xEF88A): "e4c6b1ede1629d72b895217cb2db8ad98ce91e0abce13702c7c1e366b8324870",
        (0x1B1C70, 0x1B1D10): "10dd2deb34960747494d774ca83982e582f928b4a99760fcb3edeeffdaf64a8f",
        (0x1B33A0, 0x1B33CA): "0ab16d967217c807212c8b57f2b7a30c73ce035aed6ea08c167209eec400a5b5",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static window 0x{start:x}..0x{end:x} changed")

    expected_calls = {
        0x1B1D97: 0xEF050,
        0x1B1DA6: 0xF0610,
        0x1B2279: 0x1B3CD0,
        0x1B22DE: 0x1B3CD0,
        0x1B26A0: 0x1B4390,
        0x1B2387: 0xE67C0,
        0x1B239B: 0xEF820,
        0x1B3B61: 0x1A3C00,
        0x1A3CD1: 0x18CE50,
        0x1A464D: 0x18E940,
        0x1A481D: 0x1A2520,
        0x1A4825: 0x1A28F0,
        0x1A4853: 0x18DA80,
        0x1A485B: 0x1A2C10,
        0x1A4A71: 0x18CE90,
        0x1A4AC7: 0x18D530,
        0x1A4BD8: 0x1A4DE0,
    }
    for call, target in expected_calls.items():
        require(call_target(data, mapping, call) == target, f"call target changed at 0x{call:x}")

    constants = {
        0x5C5800: 0.1,
        0x5A8128: 1.0,
        0x5A8884: 1e-5,
        0x5CBF80: 1.0 / math.sqrt(2.0),
        0x5CBF90: 1.0 / (2.0 * math.sqrt(2.0)),
        0x5CBFA0: math.sqrt(2.0),
        0x5CBFB0: 0.5,
        0x5CC060: 1.0 / 256.0,
    }
    for va, expected in constants.items():
        actual = f32(STATIC.bytes_at(data, mapping, va, 4))
        require(math.isclose(actual, expected, rel_tol=1e-7), f"constant changed at 0x{va:x}")

    half = struct.unpack("<d", STATIC.bytes_at(data, mapping, 0x5AE6F8, 8))[0]
    two_pi = struct.unpack("<d", STATIC.bytes_at(data, mapping, 0x5CBF60, 8))[0]
    require(half == 0.5, "half-Hann 0.5 constant changed")
    require(math.isclose(two_pi, 2.0 * math.pi, rel_tol=1e-7), "half-Hann 2*pi changed")

    require(
        STATIC.bytes_at(data, mapping, 0x18DA84, 6) == bytes.fromhex("c70600008043"),
        "Wiener confidence initializer is not float32 256",
    )
    require(
        STATIC.bytes_at(data, mapping, 0x1A3C85, 8) == bytes.fromhex("488b4518f30f1000"),
        "mode-0 alpha argument load changed",
    )
    require(
        STATIC.bytes_at(data, mapping, 0x1B3B46, 13)
        == bytes.fromhex("4883c35048895c24084c892424"),
        "MonoFusion+0x50 mode-0 parameter custody changed",
    )
    coefficient_weights = STATIC.bytes_at(data, mapping, 0x5D0070, 16 * 16 * 4)
    require(
        hashlib.sha256(coefficient_weights).hexdigest() == COEFFICIENT_WEIGHT_SHA256,
        "16x16 coefficient-weight table changed",
    )
    panchromatic_table = STATIC.bytes_at(
        data, mapping, PANCHROMATIC_TABLE_VA, PANCHROMATIC_TABLE_SIZE
    )
    require(
        hashlib.sha256(panchromatic_table).hexdigest() == PANCHROMATIC_TABLE_SHA256,
        "installed panchromatic characterization table changed",
    )
    require(
        data.count(panchromatic_table) == 86,
        "installed panchromatic table copy count changed",
    )
    require(
        STATIC.bytes_at(data, mapping, 0xE1B72, 7) == bytes.fromhex("0f100547bc4c00"),
        "installed panchromatic table initializer xref changed",
    )


def decode_installed_panchromatic_table(data: bytes, mapping) -> list[dict]:
    raw = STATIC.bytes_at(data, mapping, PANCHROMATIC_TABLE_VA, PANCHROMATIC_TABLE_SIZE)
    rows = []
    for index in range(28):
        record = raw[index * 0x20 : (index + 1) * 0x20]
        gain, scale, threshold, cliff, black, white, a, b = struct.unpack(
            "<I7f", record
        )
        rows.append(
            {
                "gain": gain,
                "scale": scale,
                "threshold": threshold,
                "cliff_slope": cliff,
                "black_level": black,
                "white_level": white,
                "panchromatic": (a, b),
            }
        )
    require(
        [row["gain"] for row in rows] == list(range(100, 776, 25)),
        "installed panchromatic table gain keys changed",
    )
    require(
        all(
            row["cliff_slope"] == 2.0
            and row["black_level"] == 42.0
            and row["white_level"] == 1023.0
            for row in rows
        ),
        "installed panchromatic table level constants changed",
    )
    return rows


def decode_vst_model(raw: bytes) -> tuple[float, float]:
    fields = SCHEMA.fields_by_number(raw)
    return field_f32(fields, 1), field_f32(fields, 2)


def decode_lri(path: Path) -> dict:
    source_rows = []
    target_rows = []
    sensor_rows = []
    for block, payload in SCHEMA.walk_lri_payloads(path):
        top = SCHEMA.fields_by_number(payload)
        for wire_type, raw in top.get(12, []):
            if wire_type != 2:
                continue
            module = SCHEMA.fields_by_number(raw)
            camera_id = SCHEMA.one_field(module, 2, 0)
            if camera_id not in (0, 1):
                continue
            row = (
                {
                    "block": block,
                    "sensor_analog_gain": field_f32(module, 7),
                    "sensor_digital_gain": field_f32(module, 14) if 14 in module else 1.0,
                    "sensor_exposure": SCHEMA.one_field(module, 8, 0),
                }
            )
            (target_rows if camera_id == 0 else source_rows).append(row)
        for wire_type, raw in top.get(16, []):
            if wire_type != 2:
                continue
            sensor_data = SCHEMA.fields_by_number(raw)
            characterization = SCHEMA.fields_by_number(
                SCHEMA.one_field(sensor_data, 2, 2)
            )
            models = []
            for model_wire_type, model_raw in characterization.get(4, []):
                require(model_wire_type == 2, f"{path}: invalid vst_model wire type")
                model = SCHEMA.fields_by_number(model_raw)
                models.append(
                    {
                        "gain": SCHEMA.one_field(model, 1, 0),
                        "threshold": field_f32(model, 2),
                        "scale": field_f32(model, 3),
                        "panchromatic": (
                            decode_vst_model(SCHEMA.one_field(model, 7, 2))
                            if 7 in model
                            else None
                        ),
                    }
                )
            sensor_rows.append(
                {
                    "block": block,
                    "type": SCHEMA.one_field(sensor_data, 1, 0),
                    "black_level": field_f32(characterization, 1),
                    "white_level": field_f32(characterization, 2),
                    "cliff_slope": field_f32(characterization, 3),
                    "models": models,
                }
            )

    require(len(source_rows) == 1, f"{path}: expected one A2 module record")
    require(len(target_rows) == 1, f"{path}: expected one A1 module record")
    require(len(sensor_rows) == 1, f"{path}: expected one sensor_data record")
    sensor = sensor_rows[0]
    require(sensor["type"] == 2, f"{path}: unexpected public SensorType")
    require(sensor["black_level"] == 42.0, f"{path}: black_level changed")
    require(sensor["white_level"] == 1023.0, f"{path}: white_level changed")
    require(sensor["cliff_slope"] == 2.0, f"{path}: cliff_slope changed")
    require(
        [row["gain"] for row in sensor["models"]] == list(range(100, 776, 25)),
        f"{path}: unexpected VST gain table",
    )
    require(all(row["panchromatic"] is not None for row in sensor["models"]), f"{path}: missing panchromatic")
    return {"target": target_rows[0], "source": source_rows[0], "sensor": sensor}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=STATIC.LIBCP)
    parser.add_argument(
        "--lri",
        action="append",
        metavar="LABEL=PATH",
        help="override/add a labeled LRI; defaults to Unit-1 28/35 and Unit-2 28",
    )
    parser.add_argument("--dump-coefficient-table", action="store_true")
    args = parser.parse_args()

    lris = dict(DEFAULT_LRIS)
    if args.lri:
        lris = {}
        for item in args.lri:
            label, separator, path = item.partition("=")
            require(bool(separator and label and path), f"invalid --lri {item!r}")
            lris[label] = Path(path)

    data = args.libcp.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"unexpected libcp digest {digest}")
    mapping = STATIC.segments(data)
    verify_schema(data)
    verify_static(data, mapping)
    installed_rows = decode_installed_panchromatic_table(data, mapping)
    installed_by_gain = {row["gain"]: row for row in installed_rows}

    reports = {label: decode_lri(path) for label, path in lris.items()}
    for label, expected in EXPECTED_CAPTURE.items():
        if label not in reports:
            continue
        source = reports[label]["source"]
        actual = (
            source["sensor_analog_gain"],
            source["sensor_digital_gain"],
            source["sensor_exposure"],
        )
        require(actual == expected, f"{label}: public A2 capture tuple changed: {actual}")
        target = reports[label]["target"]
        target_actual = (
            target["sensor_analog_gain"],
            target["sensor_digital_gain"],
            target["sensor_exposure"],
        )
        require(
            target_actual == EXPECTED_TARGET[label],
            f"{label}: public A1 capture tuple changed: {target_actual}",
        )
        iso_key = int(source["sensor_analog_gain"] * 100.0)
        model = next(row for row in reports[label]["sensor"]["models"] if row["gain"] == iso_key)
        installed = installed_by_gain[iso_key]
        require(
            model["panchromatic"] != installed["panchromatic"],
            f"{label}: LRI and installed panchromatic rows unexpectedly match",
        )
        print(
            f"{label}: A2 analog={actual[0]:g} digital={actual[1]:g} "
            f"exposure={actual[2]} VST_gain={iso_key} "
            f"LRI_type2_panchromatic=({model['panchromatic'][0]:.9g},"
            f"{model['panchromatic'][1]:.9g}) "
            f"installed_type3_panchromatic=({installed['panchromatic'][0]:.9g},"
            f"{installed['panchromatic'][1]:.9g})"
        )
        target_energy = round_f32(
            round_f32(float(target_actual[2])) * round_f32(target_actual[0])
        )
        source_energy = round_f32(
            round_f32(float(actual[2])) * round_f32(actual[0])
        )
        exposure_ratio = round_f32(target_energy / source_energy)
        frame_scale = round_f32(
            exposure_ratio / round_f32(2.3183400630950928)
        )
        print(
            f"{label}: frame_scale=(A1.exposure*A1.analog_gain)/"
            f"(A2.exposure*A2.analog_gain*R)={frame_scale:.9g}"
        )

    print(f"prefusion_monofusion_worker_static=OK libcp={digest}")
    print("schema=SensorData.data->SensorCharacterization.vst_model[].panchromatic.{a,b}")
    print("source_sensor_type=SENSOR_AR1335_MONO(3); sensor_data_type=SENSOR_AR1335(2)")
    print(
        "mono_vst_origin=installed_type3_table_not_LRI_type2 "
        f"va=0x{PANCHROMATIC_TABLE_VA:x} sha256={PANCHROMATIC_TABLE_SHA256} copies=86"
    )
    print("source_affine_origin=public_A1_A2_sensor_exposure_and_sensor_analog_gain")
    print("mode0=16x16 coefficient-domain Wiener blend plus half-Hann overlap-add; step=8")
    print(
        "confidence_callback=(alpha+(1-alpha)*sum(1-confidence)/N)^2"
        "+((1-alpha)^2*C/(N^2*R))*sum(confidence^2)"
    )
    print("transform=normalized_5/3_lifting_forward_inverse_pair")
    print("half_Hann(i)=0.5*(1-cos(2*pi*(i+0.5)/16))")
    print(f"coefficient_weight_table_sha256={COEFFICIENT_WEIGHT_SHA256}")
    print("public_to_internal_vst_preparation=REFUTED_FOR_MONO_SOURCE")
    if args.dump_coefficient_table:
        raw = STATIC.bytes_at(data, mapping, 0x5D0070, 16 * 16 * 4)
        values = struct.unpack("<256f", raw)
        print(json.dumps([values[row : row + 16] for row in range(0, 256, 16)]))


if __name__ == "__main__":
    main()
