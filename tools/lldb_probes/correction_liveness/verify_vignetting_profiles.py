#!/usr/bin/env python3
"""Replay captured shaped vignetting grids from public LRI protobuf values."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def fields(blob: bytes, number: int):
    return [value for field, _wire, value in parse_proto_fields(blob) if field == number]


def scalar(blob: bytes, number: int):
    values = fields(blob, number)
    if len(values) != 1:
        raise AssertionError(f"field {number}: expected one value, got {len(values)}")
    return values[0]


def decode_modules(lri: Path) -> dict[int, list[tuple[int, int, int, list[float]]]]:
    blocks = scan_lri_blocks(str(lri))
    block = next(
        item
        for item in blocks
        if len(fields(item["payload"], 13)) == 16
        and all(fields(raw, 4) for raw in fields(item["payload"], 13))
    )
    result = {}
    for module in fields(block["payload"], 13):
        camera = int(scalar(module, 1))
        vign = scalar(module, 4)
        models = []
        for mirror in fields(vign, 2):
            hall = int(scalar(mirror, 1))
            model = scalar(mirror, 2)
            width = int(scalar(model, 1))
            height = int(scalar(model, 2))
            packed = scalar(model, 3)
            values = list(struct.unpack("<" + "f" * (len(packed) // 4), packed))
            if len(values) != width * height:
                raise AssertionError("vignetting grid length mismatch")
            models.append((hall, width, height, values))
        result[camera] = sorted(models)
    return result


def interpolate(models, lens_position: int) -> tuple[int, int, list[float]]:
    if len(models) == 1 or lens_position <= models[0][0]:
        _hall, width, height, values = models[0]
        return width, height, values
    if lens_position >= models[-1][0]:
        _hall, width, height, values = models[-1]
        return width, height, values
    upper_index = next(
        index for index, item in enumerate(models) if item[0] >= lens_position
    )
    upper = models[upper_index]
    if upper[0] == lens_position:
        return upper[1], upper[2], upper[3]
    lower = models[upper_index - 1]
    if (lower[1], lower[2]) != (upper[1], upper[2]):
        raise AssertionError("bracketing vignetting dimensions differ")
    # Match 0x107064..0x1070a3 exactly: both differences are formed
    # upper-relative and therefore negative for an interior sample.
    t = f32(
        f32(float(lens_position - upper[0]))
        / f32(float(lower[0] - upper[0]))
    )
    one_minus_t = f32(f32(1.0) - t)
    values = [
        f32(f32(f32(low) * t) + f32(f32(high) * one_minus_t))
        for low, high in zip(lower[3], upper[3])
    ]
    return lower[1], lower[2], values


def shape(values: list[float], multiplier: float, inverse: int) -> list[float]:
    multiplier = f32(multiplier)
    result = []
    for value in values:
        shaped = f32(f32(f32(value) - f32(1.0)) * multiplier)
        shaped = f32(shaped + f32(1.0))
        if inverse:
            shaped = f32(shaped / f32(value))
        result.append(shaped)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lri", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    models = decode_modules(args.lri)
    calibration_order = list(models)
    report = json.loads(args.report.read_text())
    checked = []
    for packet in report["vignetting_packets"]:
        if "camera_id" not in packet:
            continue
        matches = []
        for calibration_camera_id, candidate_models in models.items():
            width, height, values = interpolate(
                candidate_models, packet["mirror_position"]
            )
            output = shape(
                values, packet["multiplier_xmm0"], packet["mode_bool"]
            )
            raw = struct.pack("<" + "f" * len(output), *output)
            digest = hashlib.sha256(raw).hexdigest()
            if digest == packet["data_sha256"]:
                matches.append((calibration_camera_id, width, height, raw, digest))
        if not matches:
            raise AssertionError(
                f"no public-model match for runtime camera {packet['camera_id']}"
            )
        calibration_camera_id, width, height, raw, digest = matches[0]
        calibration_candidates = [item[0] for item in matches]
        calibration_index = None
        if len(matches) != 1:
            calibration_camera_id = None
        else:
            calibration_index = calibration_order.index(calibration_camera_id)
            if calibration_index != packet["camera_id"]:
                raise AssertionError(
                    f"runtime key {packet['camera_id']} selected public "
                    f"calibration index {calibration_index}"
                )
        observed_width = (
            packet["width"]
            if "selected_hall_code" in packet
            else packet["height"]
        )
        observed_height = packet["height"] if "selected_hall_code" in packet else 13
        if (width, height, len(raw), digest) != (
            observed_width,
            observed_height,
            packet["byte_count"],
            packet["data_sha256"],
        ):
            raise AssertionError(
                f"packet mismatch camera={packet['camera_id']} "
                f"lens={packet['lens_position']} mode={packet['mode_bool']} "
                f"multiplier={packet['multiplier_xmm0']} expected={digest} "
                f"observed={packet['data_sha256']}"
            )
        checked.append(
            {
                "camera_id": packet["camera_id"],
                "calibration_camera_id": calibration_camera_id,
                "calibration_index": calibration_index,
                "calibration_candidates": calibration_candidates,
                "mirror_position": packet["mirror_position"],
                "lens_position": packet["lens_position"],
                "mode_bool": packet["mode_bool"],
                "multiplier": packet["multiplier_xmm0"],
                "sha256": digest,
            }
        )
    if not checked:
        raise AssertionError("no complete vignetting packets")
    print(
        json.dumps(
            {
                "status": "PASS",
                "packet_count": len(checked),
                "camera_ids": sorted({item["camera_id"] for item in checked}),
                "runtime_to_calibration_camera_ids": sorted(
                    {
                        (item["camera_id"], item["calibration_camera_id"])
                        for item in checked
                        if item["calibration_camera_id"] is not None
                    }
                ),
                "mode_multiplier_pairs": sorted(
                    {
                        (item["mode_bool"], item["multiplier"])
                        for item in checked
                    }
                ),
                "packets": checked,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
