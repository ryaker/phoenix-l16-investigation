#!/usr/bin/env python3
"""Independently verify Pile-2 calibration, VST, and schema extractions."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
VST_VA = 0x5AD7C0
VST_SIZE = 28 * 0x20
VST_SHA256 = "e0e40ce025012b1df9c96d0ad59d00f45722d521c48a3bc04de806ae3467d878"

CANONICAL = {
    "28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "35mm": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
    "70mm": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
    "150mm": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
}

PAYLOAD_DIGESTS = {
    32832: "722a6e721636c9c4bc8249f2f0fea14cf34ff00e66a3e50ee17f1e9d8649513e",
    262968: "f0c34433f9cf9b07bcf0880f7363db346c79a71a06aef2093a36954eac7660eb",
    35266: "6a0d52b6a4d1b4de62eda1975acec1ada4b0577fdaa2e93ff362247f426c8875",
}

DESCRIPTOR_DIGESTS = {
    "distortion.proto": "3651b91818e2f71d387d4bbb83be9c8aca43d1fb7fead5d62a69742d8c50ec08",
    "color_calibration.proto": "986015aea1758f57c5fa36e2d29d68eafe81fc5b563a6c28fedae1a18f5f937d",
    "vignetting_characterization.proto": "890ef948e0497ff6ac1ea793c1387f947b6cdad4636d049f9951aca4df7861fb",
    "sensor_characterization.proto": "0c249e4e9acbf7d4c1dcb0e3faa0ebbb8ca498f632ba263544924816f9385609",
}

PACKED_FIELDS = {
    (".ltpb.Distortion.Polynomial", 3): "coeffs",
    (".ltpb.VignettingCharacterization.CrosstalkModel", 4): "data_packed",
    (".ltpb.VignettingCharacterization.VignettingModel", 3): "data",
    (".ltpb.ColorCalibration.SpectralSensitivity", 3): "data",
}

SELECTED_FIELDS = {
    (".ltpb.Distortion.Polynomial", 1): ("distortion_center", "message"),
    (".ltpb.Distortion.Polynomial", 2): ("normalization", "message"),
    (".ltpb.Distortion.Polynomial", 3): ("coeffs", "float"),
    (".ltpb.Distortion.Polynomial", 4): ("fit_cost", "float"),
    (".ltpb.Distortion.Polynomial", 5): ("valid_roi", "message"),
    (".ltpb.Distortion.CRA", 4): ("pixel_size", "float"),
    (".ltpb.ColorCalibration", 1): ("type", "enum"),
    (".ltpb.ColorCalibration", 2): ("forward_matrix", "message"),
    (".ltpb.ColorCalibration", 3): ("color_matrix", "message"),
    (".ltpb.ColorCalibration", 4): ("rg_ratio", "float"),
    (".ltpb.ColorCalibration", 5): ("bg_ratio", "float"),
    (".ltpb.VignettingCharacterization", 1): ("crosstalk", "message"),
    (".ltpb.VignettingCharacterization", 2): ("vignetting", "message"),
    (".ltpb.VignettingCharacterization", 3): ("relative_brightness", "float"),
    (".ltpb.VignettingCharacterization", 4): ("lens_hall_code", "int32"),
    (".ltpb.SensorCharacterization", 1): ("black_level", "float"),
    (".ltpb.SensorCharacterization", 2): ("white_level", "float"),
    (".ltpb.SensorCharacterization", 3): ("cliff_slope", "float"),
    (".ltpb.SensorCharacterization", 4): ("vst_model", "message"),
    (".ltpb.SensorCharacterization.VstNoiseModel", 1): ("gain", "uint32"),
    (".ltpb.SensorCharacterization.VstNoiseModel", 7): ("panchromatic", "message"),
    (".ltpb.SensorCharacterization.VstNoiseModel.VstModel", 1): ("a", "float"),
    (".ltpb.SensorCharacterization.VstNoiseModel.VstModel", 2): ("b", "float"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_payloads() -> dict:
    by_size: dict[int, set[str]] = {size: set() for size in PAYLOAD_DIGESTS}
    rows = {}
    for label, path in CANONICAL.items():
        require(path.is_file(), f"missing canonical LRI {path}")
        found = {}
        for block in scan_lri_blocks(str(path)):
            payload = block["payload"]
            size = len(payload)
            if size not in PAYLOAD_DIGESTS:
                continue
            digest = hashlib.sha256(payload).hexdigest()
            found[size] = digest
            by_size[size].add(digest)
            if size in (32832, 262968):
                field13 = sum(
                    1 for number, wire, _value in parse_proto_fields(payload)
                    if number == 13 and wire == 2
                )
                require(field13 == 16, f"{label}: size {size} has {field13} field-13 records")
        require(set(found) == set(PAYLOAD_DIGESTS), f"{label}: missing calibration payload")
        rows[label] = {str(size): found[size] for size in sorted(found)}
    for size, expected in PAYLOAD_DIGESTS.items():
        require(by_size[size] == {expected}, f"payload {size}: digest mismatch {by_size[size]}")
    return rows


def verify_vst(data: bytes, static) -> list[dict]:
    mapping = static.segments(data)
    blob = static.bytes_at(data, mapping, VST_VA, VST_SIZE)
    require(hashlib.sha256(blob).hexdigest() == VST_SHA256, "VST table digest changed")
    rows = []
    for index in range(28):
        record = blob[index * 0x20 : (index + 1) * 0x20]
        values = struct.unpack("<I7f", record)
        words = struct.unpack("<8I", record)
        gain = values[0]
        require(gain == 100 + 25 * index, f"VST row {index}: gain {gain}")
        require(values[3:6] == (2.0, 42.0, 1023.0), f"VST row {index}: invariants")
        rows.append(
            {
                "index": index,
                "gain": gain,
                "scale": values[1],
                "threshold": values[2],
                "cliff_slope": values[3],
                "black_level": values[4],
                "white_level": values[5],
                "panchromatic_a": values[6],
                "panchromatic_b": values[7],
                "float_words_hex": [f"0x{word:08x}" for word in words[1:]],
            }
        )
    return rows


def verify_schema(data: bytes, schema) -> dict:
    descriptors = schema.locate_all_descriptors(data)
    by_file = {item["name"]: item for item in descriptors}
    for filename, expected in DESCRIPTOR_DIGESTS.items():
        require(filename in by_file, f"missing descriptor {filename}")
        require(by_file[filename]["serialized_sha256"] == expected,
                f"descriptor digest changed: {filename}")
    fields = schema.field_map(descriptors)
    for (message, number), (name, field_type) in SELECTED_FIELDS.items():
        field = fields.get(message, {}).get(number)
        require(field is not None, f"missing {message} field {number}")
        require((field["name"], field["type"]) == (name, field_type),
                f"unexpected {message} field {number}: {field}")
    packed = {}
    for (message, number), name in PACKED_FIELDS.items():
        field = fields.get(message, {}).get(number)
        require(field is not None and field["name"] == name, f"missing packed field {message}.{name}")
        require(field["label"] == "repeated" and field["type"] == "float",
                f"wrong packed field type {message}.{name}")
        require(field["packed"] is True, f"{message}.{name} is not explicitly packed")
        packed[f"{message}.{name}"] = True
    return {
        "descriptor_sha256": DESCRIPTOR_DIGESTS,
        "explicit_packed": packed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    static = load_module(
        "pile2_static_helper",
        ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py",
    )
    schema = load_module(
        "pile2_schema_helper",
        ROOT / "tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_embedded_calibration_proto_schema.py",
    )

    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")
    report = {
        "libcp_sha256": digest,
        "calibration_payloads": verify_payloads(),
        "vst_table_va": f"0x{VST_VA:x}",
        "vst_table_sha256": VST_SHA256,
        "vst_rows": verify_vst(data, static),
        "schema": verify_schema(data, schema),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("pile2_calibration_payloads=OK sizes=32832,35266,262968 seeds=4")
    print(f"pile2_vst_table=OK rows={len(report['vst_rows'])} sha256={VST_SHA256}")
    print("pile2_schema=OK selected_fields=23 explicit_packed=4")


if __name__ == "__main__":
    main()
