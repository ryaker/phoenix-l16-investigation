#!/usr/bin/env python3
"""Verify selected-color normalization and lens shading from public LRI data."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
MONO_PATH = (
    ROOT
    / "tools/lldb_probes/index5_guidance_channel_origin"
    / "verify_create_stereo_mono_public_reconstruction.py"
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


MONO = load_module("selected_color_mono_helpers", MONO_PATH)
RAW = MONO.RAW
VIGNETTING = MONO.VIGNETTING
STATIC = MONO.STATIC
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
STATIC_BODIES = {
    (0x350FF0, 0x3510C4): "8ec80ba2b03d411336dbed25c61066a829ca0b553eef7d40f2b4cea027c2c042",
    (0x352CE0, 0x352EC5): "fe6b338cfee353b0b83507588461fdd265ee8d5ed559f790ee3eb6492e4135ad",
    (0x353330, 0x353810): "07703c08210c43abf944a384c3dc9410c389a5e4bfd11fd01424428a7b6263a7",
    (0x108080, 0x10827F): "25059587828cec09a146ffb0221b032c120b15053da8e6b5ba3edb778cedad20",
}


def f32(value) -> np.float32:
    return np.float32(value)


def fields(message: bytes, number: int, wire_type: int) -> list:
    return [
        value
        for observed_wire_type, value in RAW.fields(message).get(number, [])
        if observed_wire_type == wire_type
    ]


def verify_static() -> str:
    data = STATIC.LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")
    mapping = STATIC.segments(data)
    for (start, end), expected in STATIC_BODIES.items():
        body = STATIC.bytes_at(data, mapping, start, end - start)
        require(
            hashlib.sha256(body).hexdigest() == expected,
            f"body 0x{start:x}..0x{end:x} changed",
        )
    require(
        STATIC.bytes_at(data, mapping, 0x340A30, 13).hex()
        == "554889e54889f75de9b3050100",
        "default Bayer normalization thunk changed",
    )
    for vtable, target in ((0x65AE40, 0x340A30), (0x65CA18, 0x345D50)):
        observed = STATIC.u64(STATIC.bytes_at(data, mapping, vtable + 0x30, 8))
        require(observed == target, f"vtable 0x{vtable:x} target changed")
    return digest


def selected_surface(path: Path, camera_key: int) -> tuple[dict, list[dict]]:
    blocks = RAW.lri.scan_lri_blocks(str(path))
    matches = []
    for block in blocks:
        for module in fields(block["payload"], 12, 2):
            if RAW.one(module, 2, 0) != camera_key:
                continue
            surface = RAW.one(module, 9, 2)
            size = RAW.one(surface, 2, 2)
            matches.append(
                {
                    "lens_position": RAW.one(module, 5, 0),
                    "mirror_position": RAW.one(module, 4, 0, 0),
                    "width": RAW.one(size, 1, 0),
                    "height": RAW.one(size, 2, 0),
                }
            )
    require(len(matches) == 1, f"expected one camera {camera_key}, got {len(matches)}")
    return matches[0], blocks


def artifact_plane(slot: dict) -> np.ndarray:
    descriptor = slot["descriptor"]
    element_size = slot["artifact"]["bytes_per_pixel"]
    dtype = "<u2" if element_size == 2 else "<f4"
    path = Path(slot["artifact"]["path"])
    data = path.read_bytes()
    require(len(data) == slot["artifact"]["bytes"], f"artifact size changed: {path}")
    require(
        hashlib.sha256(data).hexdigest() == slot["artifact"]["sha256"],
        f"artifact digest changed: {path}",
    )
    raw = np.frombuffer(data, dtype=dtype)
    channels = element_size // 4 if element_size >= 4 else 1
    if channels == 1:
        return raw.reshape(descriptor["size"][1], descriptor["stride"])
    return raw.reshape(descriptor["size"][1], descriptor["stride"], channels)


def profile_factor(
    profile: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    image_width: int,
    image_height: int,
) -> np.ndarray:
    step_x = f32(float(image_width) / f32(profile.shape[1] - 1))
    step_y = f32(float(image_height) / f32(profile.shape[0] - 1))
    inverse_x = f32(f32(1.0) / f32(np.floor(step_x)))
    inverse_y = f32(f32(1.0) / f32(np.floor(step_y)))
    grid_x = np.floor(x / float(step_x)).astype(np.int32)
    grid_y = np.floor(y / float(step_y)).astype(np.int32)
    grid_x = np.clip(grid_x, 0, profile.shape[1] - 2)
    grid_y = np.clip(grid_y, 0, profile.shape[0] - 2)
    local_x = np.asarray(
        x.astype(np.float32) - (grid_x.astype(np.float32) * step_x),
        dtype=np.float32,
    )
    local_y = np.asarray(
        y.astype(np.float32) - (grid_y.astype(np.float32) * step_y),
        dtype=np.float32,
    )
    ty = np.asarray(local_y * inverse_y, dtype=np.float32)
    top_left = profile[grid_y, grid_x]
    top_right = profile[grid_y, grid_x + 1]
    left_delta = np.asarray(profile[grid_y + 1, grid_x] - top_left, dtype=np.float32)
    right_delta = np.asarray(
        profile[grid_y + 1, grid_x + 1] - top_right, dtype=np.float32
    )
    left = np.asarray((ty * left_delta) + top_left, dtype=np.float32)
    right = np.asarray((ty * right_delta) + top_right, dtype=np.float32)
    slope = np.asarray((right - left) * inverse_x, dtype=np.float32)
    return np.asarray(
        local_x.astype(np.float64) * slope.astype(np.float64) + left.astype(np.float64),
        dtype=np.float32,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lri", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--camera-key", type=int, default=0)
    args = parser.parse_args()

    libcp_digest = verify_static()
    report = json.loads(args.report.read_text(encoding="ascii"))
    require(report["complete"] and not report["errors"], "incomplete stage capture")
    calls = {item["stage_index"]: item for item in report["calls"]}
    require(list(calls) == [1, 3, 5, 6, 11, 12, 15], "unexpected stage order")

    surface, blocks = selected_surface(args.lri, args.camera_key)
    black, white = MONO.sensor_levels(blocks)
    source_u16 = artifact_plane(calls[3]["before"]["payload_slots"]["0x100"])
    normalized = artifact_plane(calls[5]["before"]["payload_slots"]["0xd0"])
    expected_normalized = np.asarray(
        (source_u16.astype(np.float32) - black) * f32(f32(1.0) / f32(white - black)),
        dtype=np.float32,
    )
    require(
        np.array_equal(expected_normalized.view(np.uint32), normalized.view(np.uint32)),
        "normalization tile is not bit exact",
    )

    models = VIGNETTING.decode_modules(args.lri)
    calibration_order = list(models)
    require(args.camera_key < len(calibration_order), "calibration index out of range")
    calibration_camera_id = calibration_order[args.camera_key]
    profile_models = models[calibration_camera_id]
    profile_position = (
        surface["mirror_position"] if len(profile_models) > 1 else surface["lens_position"]
    )
    width, height, values = VIGNETTING.interpolate(
        profile_models, profile_position
    )
    require((width, height) == (17, 13), "unexpected profile dimensions")
    profile = np.asarray(values, dtype=np.float32).reshape(height, width)

    sharpen_input_slot = calls[11]["before"]["payload_slots"]["0x70"]
    lens_input_slot = calls[12]["before"]["payload_slots"]["0x70"]
    lens_output_slot = calls[15]["before"]["payload_slots"]["0x70"]
    sharpen_input = artifact_plane(sharpen_input_slot)
    lens_input = artifact_plane(lens_input_slot)
    lens_output = artifact_plane(lens_output_slot)
    require(
        np.array_equal(sharpen_input.view(np.uint32), lens_input.view(np.uint32)),
        "stage 11 changed the captured vec4 tile",
    )
    descriptor = lens_input_slot["descriptor"]
    valid_width = descriptor["size"][0]
    lens_input = lens_input[:, :valid_width]
    lens_output = lens_output[:, :valid_width]
    require(
        np.array_equal(
            lens_input[:, :, 3].view(np.uint32), lens_output[:, :, 3].view(np.uint32)
        ),
        "lens stage changed alpha",
    )

    mapped = struct.unpack(
        "<4f", bytes.fromhex(report["executors"][0]["mapped_rectangle_raw"])
    )
    rows, columns = np.indices(lens_input.shape[:2], dtype=np.float32)
    local_x = columns + f32(descriptor["origin"][0])
    local_y = rows + f32(descriptor["origin"][1])
    x = f32(mapped[0] / 2.0) + local_x - f32(descriptor["origin"][0])
    y = f32(mapped[1] / 2.0) + local_y - f32(descriptor["origin"][1])
    factor = profile_factor(profile, x, y, 2080, 1560)
    expected_rgb = np.asarray(
        lens_input[:, :, :3] * factor[:, :, None], dtype=np.float32
    )
    lens_exact = int(
        np.count_nonzero(
            expected_rgb.view(np.uint32) == lens_output[:, :, :3].view(np.uint32)
        )
    )
    require(lens_exact == expected_rgb.size, f"lens replay exact={lens_exact}")
    print(
        json.dumps(
            {
                "libcp_sha256": libcp_digest,
                "static_body_sha256": {
                    f"0x{start:x}..0x{end:x}": digest
                    for (start, end), digest in STATIC_BODIES.items()
                },
                "normalization_samples_exact": int(source_u16.size),
                "black": float(black),
                "white": float(white),
                "surface": surface,
                "camera_key": args.camera_key,
                "calibration_camera_id": calibration_camera_id,
                "profile_model_count": len(profile_models),
                "profile_position": profile_position,
                "profile_sha256": hashlib.sha256(profile.tobytes()).hexdigest(),
                "profile_range": [float(profile.min()), float(profile.max())],
                "mapped_rectangle": mapped,
                "stage_workers": {
                    str(index): f"0x{call['before']['rtti']['worker_va']:x}"
                    for index, call in calls.items()
                },
                "normalization_artifacts": {
                    "source_u16": calls[3]["before"]["payload_slots"]["0x100"]["artifact"]["sha256"],
                    "output_f32": calls[5]["before"]["payload_slots"]["0xd0"]["artifact"]["sha256"],
                },
                "lens_rgb_samples": int(lens_input[:, :, :3].size),
                "lens_rgb_samples_exact": lens_exact,
                "stage11_storage_words_unchanged": int(sharpen_input.size),
                "lens_artifacts": {
                    "input_vec4f": lens_input_slot["artifact"]["sha256"],
                    "output_vec4f": lens_output_slot["artifact"]["sha256"],
                },
                "lens_coordinate_domain": [2080, 1560],
                "lens_storage_origin_compensation": [
                    -descriptor["origin"][0],
                    -descriptor["origin"][1],
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
