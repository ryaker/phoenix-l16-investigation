#!/usr/bin/env python3
"""Rebuild CreateStereoImage's A2 mono plane from public LRI fields."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
RAW_PATH = ROOT / "tools/lldb_probes/raw_sensor_layout/verify_raw_sensor_layout.py"
VIGNETTING_PATH = (
    ROOT / "tools/lldb_probes/correction_liveness/verify_vignetting_profiles.py"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
WIDTH = 4160
HEIGHT = 3120
A2_KEY = 1
DEFAULT_RUNS = (
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_mono_replication_unit1_28mm",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_mono_replication_new_06689",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_mono_replication_unit2_28mm",
)
EXPOSURE_RUNS = {
    "create_stereo_mono_replication_unit1_28mm": (
        ROOT / "runs/index5_guidance_channel_origin/create_stereo_exposure_unit1_28mm"
    ),
    "create_stereo_mono_replication_new_06689": (
        ROOT / "runs/index5_guidance_channel_origin/create_stereo_exposure_new_06689"
    ),
    "create_stereo_mono_replication_unit2_28mm": (
        ROOT / "runs/index5_guidance_channel_origin/create_stereo_exposure_unit2_28mm"
    ),
}


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


STATIC = load_module("mono_public_static", STATIC_PATH)
RAW = load_module("mono_public_raw", RAW_PATH)
VIGNETTING = load_module("mono_public_vignetting", VIGNETTING_PATH)


def f32(value) -> np.float32:
    return np.float32(value)


def field_f32(message: bytes, number: int) -> np.float32:
    bits = RAW.one(message, number, 5)
    return f32(struct.unpack("<f", struct.pack("<I", bits))[0])


def verify_static() -> str:
    data = STATIC.LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")
    mapping = STATIC.segments(data)
    bodies = {
        (0x108370, 0x1085C6): "57de18e3f50fd16f3f700643e618de41c3d6ee305fc9f757b48f1e8942524d50",
        (0x31B470, 0x31B526): "3efdd072adf272c260620ec498741a139fb642b5b67ee0e2b8eb769b9cea7ac0",
        (0x3403F0, 0x3408DD): "9c98cef13b78f5ababf576963f82e611d036cb4fdd5e0d4c6055591ceecee8c2",
    }
    for (start, end), expected in bodies.items():
        body = STATIC.bytes_at(data, mapping, start, end - start)
        require(
            hashlib.sha256(body).hexdigest() == expected,
            f"body 0x{start:x}..0x{end:x} changed",
        )
    expected_mnemonics = {
        0x1083EB: "roundss",
        0x108404: "divss",
        0x10844A: "cvtsi2ss",
        0x10844F: "mulss",
        0x10848A: "subss",
        0x1084FB: "subss",
        0x1084FF: "mulss",
        0x108527: "movapd",
        0x10852C: "mulsd",
        0x108530: "addsd",
        0x108534: "cvtsd2ss",
        0x108538: "mulss",
        0x31B4F6: "call",
    }
    for address, mnemonic in expected_mnemonics.items():
        require(
            STATIC.instruction(data, mapping, address).mnemonic == mnemonic,
            f"instruction 0x{address:x} changed",
        )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x31B4F6))
        == 0x3403F0,
        "A2 sentinel branch target changed",
    )
    return digest


def fields(message: bytes, number: int, wire_type: int) -> list:
    return [
        value
        for observed_wire_type, value in RAW.fields(message).get(number, [])
        if observed_wire_type == wire_type
    ]


def find_a2_surface(path: Path) -> tuple[dict, bytes, dict]:
    blocks = RAW.lri.scan_lri_blocks(str(path))
    matches = []
    for block in blocks:
        modules = fields(block["payload"], 12, 2)
        for slot, module in enumerate(modules):
            if RAW.one(module, 2, 0) != A2_KEY:
                continue
            surface = RAW.one(module, 9, 2)
            size = RAW.one(surface, 2, 2)
            row = {
                "block": block,
                "slot": slot,
                "module": module,
                "lens_position": RAW.one(module, 5, 0),
                "mirror_position": RAW.one(module, 4, 0, 0),
                "width": RAW.one(size, 1, 0),
                "height": RAW.one(size, 2, 0),
                "format": RAW.one(surface, 3, 0),
                "row_stride": RAW.one(surface, 4, 0),
                "data_offset": RAW.one(surface, 5, 0),
            }
            matches.append(row)
    require(len(matches) == 1, f"{path}: expected one A2 surface, got {len(matches)}")
    row = matches[0]
    require((row["width"], row["height"]) == (WIDTH, HEIGHT), f"{path}: dimensions")
    require(row["format"] == 7, f"{path}: RAW format")
    require(row["row_stride"] == WIDTH * 5 // 4, f"{path}: RAW10 stride")
    byte_count = row["row_stride"] * HEIGHT
    with path.open("rb") as handle:
        handle.seek(row["block"]["block_offset"] + row["data_offset"])
        packed = handle.read(byte_count)
    require(len(packed) == byte_count, f"{path}: truncated A2 RAW")
    return row, packed, {"blocks": blocks}


def unpack_raw10(packed: bytes, stride: int) -> np.ndarray:
    source = np.frombuffer(packed, dtype=np.uint8).reshape(HEIGHT, stride // 5, 5)
    words = source.astype(np.uint16)
    output = np.empty((HEIGHT, WIDTH), dtype=np.uint16)
    output[:, 0::4] = words[:, :, 0] | ((words[:, :, 1] & 0x03) << 8)
    output[:, 1::4] = (words[:, :, 1] >> 2) | ((words[:, :, 2] & 0x0F) << 6)
    output[:, 2::4] = (words[:, :, 2] >> 4) | ((words[:, :, 3] & 0x3F) << 4)
    output[:, 3::4] = (words[:, :, 3] >> 6) | (words[:, :, 4] << 2)
    return output


def sensor_levels(blocks: list[dict]) -> tuple[np.float32, np.float32]:
    rows = []
    for block in blocks:
        for sensor_data in fields(block["payload"], 16, 2):
            characterization = RAW.one(sensor_data, 2, 2)
            rows.append((field_f32(characterization, 1), field_f32(characterization, 2)))
    require(len(rows) == 1, f"expected one SensorCharacterization, got {len(rows)}")
    return rows[0]


def selected_profile(path: Path, runtime_key: int, lens_position: int) -> np.ndarray:
    models = VIGNETTING.decode_modules(path)
    calibration_order = list(models)
    require(runtime_key < len(calibration_order), f"{path}: calibration index")
    calibration_camera_id = calibration_order[runtime_key]
    width, height, values = VIGNETTING.interpolate(
        models[calibration_camera_id], lens_position
    )
    require((width, height) == (17, 13), f"{path}: vignetting dimensions")
    return np.asarray(values, dtype=np.float32).reshape(height, width)


def vignetting_plane(profile: np.ndarray) -> np.ndarray:
    step_x = f32(WIDTH / f32(profile.shape[1] - 1))
    step_y = f32(HEIGHT / f32(profile.shape[0] - 1))
    floor_x = f32(np.floor(step_x))
    floor_y = f32(np.floor(step_y))
    require((step_x, step_y, floor_x, floor_y) == (260.0, 260.0, 260.0, 260.0), "profile spacing")
    inverse_x = f32(f32(1.0) / floor_x)
    inverse_y = f32(f32(1.0) / floor_y)
    output = np.empty((HEIGHT, WIDTH), dtype=np.float32)
    for y in range(HEIGHT):
        grid_y = y // int(floor_y)
        local_y = f32(f32(y) - f32(f32(grid_y) * step_y))
        ty = f32(local_y * inverse_y)
        for grid_x in range(profile.shape[1] - 1):
            top_left = profile[grid_y, grid_x]
            top_right = profile[grid_y, grid_x + 1]
            left_delta = f32(profile[grid_y + 1, grid_x] - top_left)
            right_delta = f32(profile[grid_y + 1, grid_x + 1] - top_right)
            left = f32(f32(ty * left_delta) + top_left)
            right = f32(f32(ty * right_delta) + top_right)
            slope = f32(f32(right - left) * inverse_x)
            start = grid_x * int(floor_x)
            end = min(start + int(floor_x), WIDTH)
            local_x = f32(f32(start) - f32(f32(grid_x) * step_x))
            coordinates = np.arange(end - start, dtype=np.float64) + float(local_x)
            output[y, start:end] = np.asarray(
                coordinates * float(slope) + float(left), dtype=np.float32
            )
    return output


def exposure_scale(run_name: str, source_lri: Path) -> np.float32:
    report_path = EXPOSURE_RUNS[run_name] / "report.json"
    report = json.loads(report_path.read_text(encoding="ascii"))
    require(Path(report["source_lri"]) == source_lri, f"{run_name}: exposure LRI")
    packet = report["packets"][str(A2_KEY)]
    require(packet["path"] == "mono", f"{run_name}: A2 exposure path")
    require(not packet["relative_brightness_correction"]["applied"], f"{run_name}: A2 brightness policy")
    return f32(packet["scalar"])


def verify_run(run_dir: Path) -> dict:
    report = json.loads((run_dir / "report.json").read_text(encoding="ascii"))
    require(not report["errors"], f"{run_dir}: {report['errors']}")
    require(report["terminated_after_capture"], f"{run_dir}: incomplete capture")
    source_lri = Path(report["source_lri"])
    packet = report["packet"]
    require(packet["camera_key"] == A2_KEY, f"{run_dir}: camera key")
    source_path = Path(packet["source_path"])
    source_bytes = source_path.read_bytes()
    require(hashlib.sha256(source_bytes).hexdigest() == packet["source_sha256"], f"{run_dir}: source SHA")
    observed = np.frombuffer(source_bytes, dtype="<f4").reshape(HEIGHT, WIDTH)

    surface, packed, context = find_a2_surface(source_lri)
    raw = unpack_raw10(packed, surface["row_stride"])
    black, white = sensor_levels(context["blocks"])
    require(white > black, f"{run_dir}: sensor levels")
    profile = selected_profile(source_lri, A2_KEY, surface["lens_position"])
    shading = vignetting_plane(profile)
    scale = exposure_scale(run_dir.name, source_lri)

    reciprocal = f32(f32(1.0) / f32(white - black))
    normalized = np.asarray(
        np.asarray(raw, dtype=np.float32) - black, dtype=np.float32
    )
    normalized = np.asarray(normalized * reciprocal, dtype=np.float32)
    corrected = np.asarray(normalized * shading, dtype=np.float32)
    rebuilt = np.asarray(corrected * scale, dtype=np.float32)
    exact = rebuilt.view(np.uint32) == observed.view(np.uint32)
    exact_count = int(np.count_nonzero(exact))
    require(exact_count == WIDTH * HEIGHT, f"{run_dir}: {exact_count} exact pixels")

    calibration_order = list(VIGNETTING.decode_modules(source_lri))
    result = {
        "run": run_dir.name,
        "source_lri": str(source_lri),
        "pixels_exact": exact_count,
        "raw10_sha256": hashlib.sha256(packed).hexdigest(),
        "raw_range": [int(raw.min()), int(raw.max())],
        "black_level": float(black),
        "white_level": float(white),
        "normalization_reciprocal": float(reciprocal),
        "lens_position": surface["lens_position"],
        "mirror_position": surface["mirror_position"],
        "calibration_index": A2_KEY,
        "calibration_camera_id": calibration_order[A2_KEY],
        "vignetting_grid_sha256": hashlib.sha256(profile.tobytes()).hexdigest(),
        "vignetting_range": [float(shading.min()), float(shading.max())],
        "exposure_scale": float(scale),
        "normalized_range": [float(normalized.min()), float(normalized.max())],
        "normalized_negative_pixels": int(np.count_nonzero(normalized < f32(0.0))),
        "output_range": [float(rebuilt.min()), float(rebuilt.max())],
        "rebuilt_sha256": hashlib.sha256(rebuilt.tobytes()).hexdigest(),
        "observed_sha256": packet["source_sha256"],
    }
    del observed, raw, profile, shading, normalized, corrected, rebuilt, exact
    gc.collect()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dirs", nargs="*", type=Path)
    args = parser.parse_args()
    digest = verify_static()
    print(f"static_create_stereo_mono_public=OK libcp={digest}")
    for run_dir in args.run_dirs or DEFAULT_RUNS:
        print(
            "create_stereo_mono_public=OK "
            + json.dumps(verify_run(run_dir), sort_keys=True)
        )


if __name__ == "__main__":
    main()
