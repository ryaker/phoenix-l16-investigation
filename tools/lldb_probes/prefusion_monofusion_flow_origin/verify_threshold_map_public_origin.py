#!/usr/bin/env python3
"""Replay MonoFusion's flow-rejection map from public LRI vignetting data."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/lldb_probes/correction_liveness"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402
from verify_vignetting_profiles import decode_modules, f32, interpolate  # noqa: E402


def fields(blob: bytes, number: int):
    return [value for field, _wire, value in parse_proto_fields(blob) if field == number]


def one(blob: bytes, number: int, default=None):
    values = fields(blob, number)
    return values[0] if values else default


def public_camera_modules(lri: Path) -> dict[int, dict[str, float | int]]:
    result = {}
    for block in scan_lri_blocks(str(lri)):
        for module in fields(block["payload"], 12):
            gain_raw = one(module, 7)
            result[int(one(module, 2))] = {
                "mirror_position": int(one(module, 4, 0)),
                "sensor_analog_gain": (
                    struct.unpack("<f", struct.pack("<I", gain_raw))[0]
                    if gain_raw is not None else 0.0
                ),
            }
    return result


def sample_profile(values: list[float], grid_width: int, x: int, y: int) -> float:
    step = f32(260.0)
    inverse = f32(f32(1.0) / step)
    grid_x = min(x // 260, 15)
    grid_y = min(y // 260, 11)
    local_x = f32(float(x - grid_x * 260))
    local_y = f32(float(y - grid_y * 260))

    top_left = values[grid_y * grid_width + grid_x]
    top_right = values[grid_y * grid_width + grid_x + 1]
    bottom_left = values[(grid_y + 1) * grid_width + grid_x]
    bottom_right = values[(grid_y + 1) * grid_width + grid_x + 1]

    ty = f32(local_y * inverse)
    left = f32(f32(ty * f32(bottom_left - top_left)) + top_left)
    right = f32(f32(ty * f32(bottom_right - top_right)) + top_right)
    row_slope = f32(f32(right - left) * inverse)
    return f32(float(local_x) * float(row_slope) + float(left))


def expected_threshold(analog_gain: float) -> float:
    normalized = f32(
        f32(f32(analog_gain) - f32(1.0)) * f32(0.3333333432674408)
    )
    normalized = min(max(normalized, f32(0.0)), f32(1.0))
    return f32(f32(f32(30.0) * normalized) + f32(30.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lri", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    report = json.loads(args.report.read_text())
    build = report["threshold_map_builds"][0]
    entry = report["threshold_map_entries"][0]
    modules = public_camera_modules(args.lri)
    calibration_models = decode_modules(args.lri)
    calibration_order = list(calibration_models)

    camera_index = build["reference_camera_index_0xb8"]
    calibration_index = build["calibration_index_0x60"]
    calibration_camera_id = calibration_order[calibration_index]
    mirror_position = build["mirror_position_0x50"]
    width, height, profile = interpolate(
        calibration_models[calibration_camera_id], mirror_position
    )
    assert (width, height) == (17, 13)
    assert build["rectangle"] == [0.0, 0.0, 4160.0, 3120.0]
    assert build["multiplier_xmm0"] == 1.0
    assert build["inverse_r8"] == 0

    expected_samples = []
    for sample in entry["samples"]["samples"]:
        expected = sample_profile(profile, width, *sample["pixel"])
        if struct.pack("<f", expected) != struct.pack("<f", sample["value"]):
            raise AssertionError(
                f"map mismatch at {sample['pixel']}: {expected} != {sample['value']}"
            )
        expected_samples.append(expected)

    public_gain = modules[camera_index]["sensor_analog_gain"]
    assert build["sensor_analog_gain_0x40"] == public_gain
    threshold = expected_threshold(public_gain)
    assert threshold == entry["flow_threshold_0x200"]

    print(json.dumps({
        "status": "PASS",
        "reference_camera_index": camera_index,
        "calibration_index": calibration_index,
        "calibration_camera_id": calibration_camera_id,
        "mirror_position": mirror_position,
        "sensor_analog_gain": public_gain,
        "flow_threshold": threshold,
        "callback_threshold_x256": f32(threshold * f32(256.0)),
        "sample_count": len(expected_samples),
        "samples": expected_samples,
    }, indent=2))


if __name__ == "__main__":
    main()
