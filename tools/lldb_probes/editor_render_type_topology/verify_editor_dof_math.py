#!/usr/bin/env python3
"""Verify installed DOF optical constants and bit-exact observed math."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROBE = Path(__file__).resolve().parent
LIBCP = Path("/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib")
REPORT = ROOT / "runs/editor_render_type_topology/editor_dof_math_mode1_blur9_f2.json"
REPLAY = ROOT / "runs/editor_render_type_topology/replay_editor_dof_math"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
SCHEMA_PATH = ROOT / "tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_embedded_calibration_proto_schema.py"
AUDIT_PATH = ROOT / "tools/lane_b_index5_public_meaning_audit.py"
LRI_CORPUS = (
    "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
    "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri",
    "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
    "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
    "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri",
    "/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri",
    "/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri",
    "/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def unpack_f32(blob: bytes, offset: int) -> float:
    return struct.unpack_from("<f", blob, offset)[0]


def unpack_f64(blob: bytes, offset: int) -> float:
    return struct.unpack_from("<d", blob, offset)[0]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_public_data_scale(blob: bytes) -> tuple[int, set[float]]:
    schema = load_module("dof_schema", SCHEMA_PATH)
    descriptors = schema.locate_all_descriptors(blob)
    fields = schema.field_map(descriptors)
    schema.require_field(fields, ".ltpb.CameraModule", 9,
                         "sensor_data_surface", "message")
    schema.require_field(fields, ".ltpb.CameraModule.Surface", 6,
                         "data_scale", "message")
    schema.require_field(fields, ".ltpb.Point2F", 1, "x", "float")
    schema.require_field(fields, ".ltpb.Point2F", 2, "y", "float")

    audit = load_module("dof_audit", AUDIT_PATH)
    module_count = 0
    values: set[float] = set()
    for path in LRI_CORPUS:
        for block in audit.scan_lri_blocks(path):
            for module in audit.field_values(block["payload"], 12, wire_type=2):
                surface = audit.first_field(module, 9, wire_type=2)
                require(isinstance(surface, bytes), f"{path}: missing sensor surface")
                data_scale = audit.first_field(surface, 6, wire_type=2)
                require(isinstance(data_scale, bytes), f"{path}: missing data scale")
                x_bits = audit.first_field(data_scale, 1, wire_type=5)
                y_bits = audit.first_field(data_scale, 2, wire_type=5)
                require(isinstance(x_bits, int) and isinstance(y_bits, int),
                        f"{path}: malformed data scale")
                x = struct.unpack("<f", struct.pack("<I", x_bits))[0]
                y = struct.unpack("<f", struct.pack("<I", y_bits))[0]
                require(x == y, f"{path}: anisotropic data scale {x},{y}")
                values.add(x)
                module_count += 1
    require(values == {1.0}, f"unexpected exact-focal data scales {values}")
    return module_count, values


def compile_replay() -> None:
    REPLAY.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "clang", "-arch", "x86_64", "-std=c11", "-O2",
            "-ffp-contract=off", "-Wall", "-Wextra",
            str(PROBE / "replay_editor_dof_math.c"), "-o", str(REPLAY),
        ],
        check=True,
    )


def main() -> None:
    blob = LIBCP.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == LIBCP_SHA256, "libcp SHA drift")

    physical_focal = [unpack_f32(blob, 0x5ADFB8 + 4 * i) for i in range(5)]
    equivalent_focal = [unpack_f32(blob, 0x5ADFCC + 4 * i) for i in range(4)]
    pixel_pitch = [unpack_f64(blob, 0x5ADFE0 + 8 * i) for i in range(3)]
    hardware_f_number = [unpack_f32(blob, 0x5AE5D8 + 4 * i) for i in range(3)]
    require(physical_focal == [9.1899995803833, 19.770000457763672,
                               4.559999942779541, 3.950000047683716,
                               3.680000066757202], "physical-focal table drift")
    require(equivalent_focal == [70.0, 150.0, 35.0, 28.0],
            "equivalent-focal table drift")
    require(pixel_pitch == [0.0012, 0.0011, 0.0014], "pixel-pitch table drift")
    require(hardware_f_number == [2.0, 2.0, 2.4000000953674316],
            "hardware f-number table drift")
    require(blob[0x5A81F0:0x5A8200] == bytes.fromhex("ffffff7f" * 4),
            "absolute-value mask drift")
    require(unpack_f64(blob, 0x5DE950) == 1.600000023841858,
            "radius bucket multiplier drift")

    # CapturedImage copies CameraModule.Surface.data_scale into +0x124/+0x128,
    # using [1,1] only when both public components are zero.
    require(blob[0xF3044:0xF3053] == bytes.fromhex("488b73284885f6480f4435d5bf5500"),
            "data_scale pointer/default selection drift")
    require(blob[0xF3053:0xF305F] == bytes.fromhex("488dbd48feffffe8d14c0400"),
            "Point2F extraction call drift")
    require(blob[0xF3082:0xF3093] == bytes.fromhex("48b80000803f0000803f48898548feffff"),
            "zero data_scale fallback drift")
    require(blob[0xF30A7:0xF30B5] == bytes.fromhex("41898d2401000041898528010000"),
            "CapturedImage data_scale stores drift")
    public_module_count, public_scales = verify_public_data_scale(blob)

    imports = subprocess.run(
        ["otool", "-Iv", str(LIBCP)], check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout
    for address, name in (("0x0000000000555fde", "_ldexp"),
                          ("0x0000000000555ffc", "_log2"),
                          ("0x0000000000556002", "_log2f")):
        require(address in imports and name in imports, f"missing import {name}")

    report = json.loads(REPORT.read_text())
    range_samples = report["range_samples"]
    radius_samples = report["radius_result_samples"]
    require(len(range_samples) == 64, "expected 64 focus-range samples")
    require(len(radius_samples) >= 2, "radius result coverage too small")
    require(sorted(sample["result"] for sample in radius_samples) ==
            [1, 3, 6, 12, 25, 51, 102], "radius bucket incidence drift")

    compile_replay()
    lines: list[str] = []
    for sample in range_samples:
        lines.append("F " + " ".join(sample["input_bits"]))
    for sample in radius_samples:
        lines.append("R " + " ".join(sample["depth_range_bits"]) +
                     f" {sample['depth_type']} " + " ".join(sample["input_bits"]))
    replay = subprocess.run(
        ["arch", "-x86_64", str(REPLAY)], input="\n".join(lines) + "\n",
        check=True, text=True, stdout=subprocess.PIPE,
    ).stdout.splitlines()
    require(len(replay) == len(lines), "replay output count mismatch")

    for index, sample in enumerate(range_samples):
        expected = "F " + " ".join(sample["output_bits"])
        require(replay[index] == expected,
                f"focus-range replay mismatch at sample {index}: {replay[index]} != {expected}")
    offset = len(range_samples)
    for index, sample in enumerate(radius_samples):
        expected = f"R {sample['result']}"
        require(replay[offset + index] == expected,
                f"tile-radius replay mismatch at result {sample['result']}")

    results = sorted(sample["result"] for sample in radius_samples)
    print("installed_constants=OK physical_focal=" + ",".join(map(str, physical_focal)))
    print("installed_constants=OK equivalent_focal=" + ",".join(map(str, equivalent_focal)))
    print("installed_constants=OK pixel_pitch=" + ",".join(map(str, pixel_pitch)) +
          " hardware_f_number=" + ",".join(map(str, hardware_f_number)))
    print(f"public_data_scale=OK modules={public_module_count} values={sorted(public_scales)}")
    print(f"focus_range_replay=OK samples={len(range_samples)}")
    print(f"tile_radius_replay=OK representatives={len(radius_samples)} results={results}")


if __name__ == "__main__":
    main()
