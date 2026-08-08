#!/usr/bin/env python3
"""Verify public AWB-to-CCM chromaticity custody and installed conversion math."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/ccm_chromaticity_origin"
HARNESS = RUN_ROOT / "dump_ccm_chromaticity"
TABLE_DUMP = RUN_ROOT / "dump.txt"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
CCM_PATH = (
    ROOT
    / "tools/lldb_probes/ccm_illuminant_selection"
    / "verify_ccm_illuminant_selection.py"
)
AWB_PATH = (
    ROOT
    / "tools/lldb_probes/awb_public_origin"
    / "verify_awb_public_origin.py"
)
FRAMEWORKS = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
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


STATIC = load_module("ccm_origin_static", STATIC_PATH)
CCM = load_module("ccm_origin_ccm", CCM_PATH)
AWB = load_module("ccm_origin_awb", AWB_PATH)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def range_hash(data: bytes, mapping, start: int, end: int) -> str:
    return hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()


def require_call(data: bytes, mapping, address: int, target: int) -> None:
    item = STATIC.instruction(data, mapping, address)
    require(
        STATIC.direct_call_target(item) == target,
        f"call 0x{address:x} changed: {item.mnemonic} {item.op_str}",
    )


def verify_static() -> None:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    expected_hashes = {
        (0x1BD270, 0x1BDB60): "116186090d780e5f4b7c6f8d318b46025c9ec03d0a81694352f41a576b5ebde5",
        (0x1BDFB0, 0x1BE270): "ec0a45d7d62d09395c52f48e93588f077f4a88f0ad56952eddbbdd676ac96ee7",
        (0x342620, 0x342B10): "f048e9ca2044ac99ff7568b21379d5343206c980b83a8cadca6c300b7b14e4d4",
        (0x350380, 0x350570): "49792342315e49dab4137813a0605c1876857729f23c4ebabd6502bdc5eca088",
        (0x350570, 0x350BC0): "fd6718314938817323b33467eda893186f9c248f0ebdaa09d746c29b08c87a74",
        (0xAB130, 0xAB2E0): "1fc4a7b8f643fe4857b4137664ade6bd9929699af3aafb18fe8ab0f68bdc5f10",
        (0xAB2E0, 0xAB4C0): "a154871a8c7886f74f5d0ef6948f59237aa34e3ec0488b68d1944f48d6e38381",
    }
    for (start, end), expected in expected_hashes.items():
        require(
            range_hash(data, mapping, start, end) == expected,
            f"static body 0x{start:x}..0x{end:x} changed",
        )

    for address, target in (
        (0x1BD592, 0x13F170),  # ViewPreferences.awb_gains accessor
        (0x1BD75D, 0x350570),  # normalized neutral RGB -> xy
        (0x1BD83D, 0xAB2E0),   # xy -> neutral temperature/tint
        (0x1BE11E, 0x31BB10),  # neutral_temp property write
        (0x1BE18E, 0x31BB10),  # neutral_tint property write
        (0x3187F1, 0xC6F0),    # neutral_temp property read
        (0x318810, 0xC6F0),    # neutral_tint property read
        (0x318847, 0x33EAD0),  # pair -> ISP object +0x15d0
        (0x342A9E, 0xAB130),   # temp/tint -> xy
        (0x342AB1, 0x350BC0),  # xy -> live CCM interpolation
        (0x3505E8, 0xAB2E0),   # current xy -> CCT in fixed-point solve
        (0x35060A, 0xAB720),   # interpolate A/D65 color matrix
        (0x350612, 0x9E250),   # matrix determinant
        (0x35062E, 0x9D7E0),   # matrix inverse
    ):
        require_call(data, mapping, address, target)

    require(
        STATIC.memory_displacement(STATIC.instruction(data, mapping, 0x1BD703), 0)
        == 0x74,
        "neutral RGB destination changed",
    )
    require(
        STATIC.memory_displacement(STATIC.instruction(data, mapping, 0x1BD848), 0)
        == 0x88,
        "neutral_temp destination changed",
    )
    require(
        STATIC.memory_displacement(STATIC.instruction(data, mapping, 0x1BD855), 0)
        == 0x8C,
        "neutral_tint destination changed",
    )
    print(f"static_ccm_chromaticity_origin=OK libcp={digest}")


def key_values(line: str) -> dict[str, str]:
    return dict(re.findall(r"([A-Za-z0-9_]+)=([^ ]+)", line))


def verify_runtime_dump() -> None:
    require(TABLE_DUMP.is_file(), f"missing runtime table dump: {TABLE_DUMP}")
    lines = TABLE_DUMP.read_text().splitlines()
    properties = {
        item["label"]: item["value"]
        for item in map(key_values, lines)
        if item.get("property") is None and "label" in item and "value" in item
    }
    require(properties.get("awb_parent") == "auto_white_balance", "AWB parent name")
    require(properties.get("awb_type") == "type", "AWB type name")
    require(properties.get("mode2_vector") == "neutral_color", "neutral_color name")
    require(properties.get("mode3_scalar_1") == "neutral_temp", "neutral_temp name")
    require(properties.get("mode3_scalar_2") == "neutral_tint", "neutral_tint name")

    table = bytearray()
    rows = [line for line in lines if line.startswith("locus row=")]
    require(len(rows) == 31, f"Robertson row count {len(rows)}")
    for expected_row, line in enumerate(rows):
        item = key_values(line)
        require(int(item["row"]) == expected_row, f"Robertson row {expected_row}")
        for name in ("reciprocal", "u", "v", "slope"):
            table.extend(struct.pack("<I", int(item[f"{name}_bits"], 16)))
    require(
        hashlib.sha256(table).hexdigest()
        == "a82b3a43e3e19947839db421b880770a0590ee4eefa088ff7a3914a5ef081ada",
        "Robertson table changed",
    )

    initial = key_values(next(line for line in lines if line.startswith("neutral_solver_initial")))
    require(int(initial["x_bits"], 16) == 0x3EB0FB8D, "solver initial x")
    require(int(initial["y_bits"], 16) == 0x3EB78CD0, "solver initial y")

    expected_cct = {
        (0x3EB160B0, 0x3EB4BBFF): (0x459ACD4F, 0x3F0C2638),
        (0x3EB1EB48, 0x3EB5DA82): (0x4599D0AB, 0x4027C37B),
        (0x3EAF2373, 0x3EB25F76): (0x459F9EE9, 0xBF813E50),
        (0x3EB25BB7, 0x3EB37436): (0x459837A0, 0xC0AD1955),
    }
    observed = {}
    for line in lines:
        if not line.startswith("xy_to_cct_tint "):
            continue
        item = key_values(line)
        observed[(f32_bits(float(item["x"])), f32_bits(float(item["y"])))] = (
            int(item["cct_bits"], 16),
            int(item["tint_bits"], 16),
        )
    for xy_bits, output_bits in expected_cct.items():
        require(observed.get(xy_bits) == output_bits, f"xy/CCT table case changed: {xy_bits}")
    expected_standard_illuminants = {
        (0x3EE5283F, 0x3ED09BF5): (0x45327A1E, 0xBB87327D),
        (0x3EA01DB4, 0x3EA875B8): (0x45CB30A7, 0x411C4431),
    }
    for xy_bits, output_bits in expected_standard_illuminants.items():
        require(
            observed.get(xy_bits) == output_bits,
            f"standard illuminant xy/CCT case changed: {xy_bits}",
        )
    print("runtime_table=OK properties=neutral_temp,neutral_tint rows=31")


def run_public_case(arguments: list[float]) -> dict[str, str]:
    require(HARNESS.is_file(), f"missing harness: {HARNESS}")
    environment = os.environ.copy()
    environment["DYLD_FRAMEWORK_PATH"] = str(FRAMEWORKS)
    environment["DYLD_LIBRARY_PATH"] = str(FRAMEWORKS)
    result = subprocess.run(
        ["arch", "-x86_64", str(HARNESS), *(repr(value) for value in arguments)],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    line = result.stdout.strip()
    require(line.startswith("public_case "), f"unexpected harness output: {line}")
    return key_values(line)


def verify_four_focal_public_join() -> None:
    for tier, lri_path in CCM.LRIS.items():
        report = json.loads((CCM.RUN_ROOT / f"{tier}.json").read_text())
        sample = report["samples"][0]
        records = CCM.public_color_records(lri_path)
        matrix_a = bytes.fromhex(sample["matrix_1"]["hex"])
        matrix_d65 = bytes.fromhex(sample["matrix_2"]["hex"])
        cameras = [
            camera
            for camera in range(16)
            if records.get((camera, 0), {}).get("color_matrix") == matrix_a
            and records.get((camera, 2), {}).get("color_matrix") == matrix_d65
        ]
        require(len(cameras) == 1, f"{tier}: anchor matrix camera")
        camera = cameras[0]
        require(camera == (0 if tier in ("28mm", "35mm") else 8), f"{tier}: anchor")

        awb = AWB.parse_awb(AWB.LRIS[f"unit1_{tier}"])["gains"]
        arguments = [
            2855.63232421875,
            6502.08203125,
            *struct.unpack("<9f", records[(camera, 0)]["color_matrix"]),
            *struct.unpack("<9f", records[(camera, 2)]["color_matrix"]),
            awb["r"],
            awb["g_r"],
            awb["b"],
        ]
        result = run_public_case(arguments)

        expected_neutral = [
            f32(f32(1.0) / awb["r"]),
            f32(f32(1.0) / awb["g_r"]),
            f32(f32(1.0) / awb["b"]),
        ]
        scale = f32(f32(1.0) / max(expected_neutral))
        expected_neutral = [f32(value * scale) for value in expected_neutral]
        for name, expected in zip(("r", "g", "b"), expected_neutral):
            require(
                int(result[f"neutral_{name}_bits"], 16) == f32_bits(expected),
                f"{tier}: normalized neutral {name}",
            )

        expected_xy = bytes.fromhex(sample["xy"]["hex"])
        actual_xy = struct.pack(
            "<II",
            int(result["reconstructed_x_bits"], 16),
            int(result["reconstructed_y_bits"], 16),
        )
        require(actual_xy == expected_xy, f"{tier}: public AWB/calibration -> live xy")
        if sample.get("target_cct") is not None:
            require(
                int(result["final_cct_bits"], 16) == f32_bits(sample["target_cct"]),
                f"{tier}: live CCT",
            )
        print(
            f"{tier}: OK camera={camera} xy={struct.unpack('<2f', actual_xy)} "
            f"cct_bits={result['final_cct_bits']}"
        )


def main() -> None:
    verify_static()
    verify_runtime_dump()
    verify_four_focal_public_join()
    print("ccm_chromaticity_origin=OK")


if __name__ == "__main__":
    main()
