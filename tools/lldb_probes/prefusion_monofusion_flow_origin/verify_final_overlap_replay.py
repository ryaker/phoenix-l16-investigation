#!/usr/bin/env python3
"""Replay the full 16x16/overlap-8/radius-2 MonoFusion flow stage."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from numba import njit, prange

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/lldb_probes/prefusion_monofusion_flow_origin"))

from verify_threshold_map_public_origin import (  # noqa: E402
    decode_modules,
    expected_threshold,
    interpolate,
    public_camera_modules,
    sample_profile,
)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


@njit(inline="always")
def patch_sad(reference, source, bx, by, sx, sy):
    total = np.int64(0)
    for py in range(16):
        for px in range(16):
            left = np.int32(reference[by + py, bx + px])
            right = np.int32(source[sy + py, sx + px])
            difference = left - right
            total += -difference if difference < 0 else difference
    return total


@njit(parallel=True)
def replay_candidates(reference, source, previous):
    output_height = 389
    output_width = 519
    flow = np.empty((output_height, output_width, 2), dtype=np.int32)
    minimum_sad = np.empty((output_height, output_width), dtype=np.int32)
    predictor_origin = np.empty((output_height, output_width, 2), dtype=np.int32)
    source_height, source_width = source.shape
    previous_height, previous_width, _ = previous.shape

    for linear in prange(output_height * output_width):
        gy = linear // output_width
        gx = linear - gy * output_width
        bx = gx * 8
        by = gy * 8

        prior_x = gx // 4
        prior_y = gy // 4
        best_predictor_sad = 0x7FFFFFFF
        predicted_x = bx
        predicted_y = by
        for offset_y in range(-1, 2):
            iy = prior_y + offset_y
            if iy < 0:
                iy = 0
            elif iy >= previous_height:
                iy = previous_height - 1
            for offset_x in range(-1, 2):
                ix = prior_x + offset_x
                if ix < 0:
                    ix = 0
                elif ix >= previous_width:
                    ix = previous_width - 1
                sx = bx + int(previous[iy, ix, 0] * np.float32(2.0))
                sy = by + int(previous[iy, ix, 1] * np.float32(2.0))
                if sx < 0:
                    sx = 0
                elif sx > source_width - 17:
                    sx = source_width - 17
                if sy < 0:
                    sy = 0
                elif sy > source_height - 17:
                    sy = source_height - 17
                sad = patch_sad(reference, source, bx, by, sx, sy)
                if sad < best_predictor_sad:
                    best_predictor_sad = sad
                    predicted_x = sx
                    predicted_y = sy

        best_sad = 0x7FFFFFFF
        best_x = predicted_x
        best_y = predicted_y
        for local_y in range(-2, 3):
            sy = predicted_y + local_y
            if sy < 0 or sy > source_height - 16:
                continue
            for local_x in range(-2, 3):
                sx = predicted_x + local_x
                if sx < 0 or sx > source_width - 16:
                    continue
                sad = patch_sad(reference, source, bx, by, sx, sy)
                if sad < best_sad:
                    best_sad = sad
                    best_x = sx
                    best_y = sy

        predictor_origin[gy, gx, 0] = predicted_x
        predictor_origin[gy, gx, 1] = predicted_y
        minimum_sad[gy, gx] = best_sad
        flow[gy, gx, 0] = best_x - bx
        flow[gy, gx, 1] = best_y - by

    return flow, minimum_sad, predictor_origin


def public_threshold_inputs(lri, report_path):
    report = json.loads(report_path.read_text(encoding="ascii"))
    build = report["threshold_map_builds"][0]
    modules = public_camera_modules(lri)
    models = decode_modules(lri)
    calibration_order = list(models)
    camera_index = build["reference_camera_index_0xb8"]
    calibration_index = build["calibration_index_0x60"]
    camera_id = calibration_order[calibration_index]
    width, height, profile = interpolate(models[camera_id], build["mirror_position_0x50"])
    assert (width, height) == (17, 13)
    analog_gain = modules[camera_index]["sensor_analog_gain"]
    multiplier = f32(expected_threshold(analog_gain) * f32(256.0))
    return profile, multiplier


def classify(profile, multiplier, minimum_sad, predictor_origin, width, height):
    output_height, output_width = minimum_sad.shape
    rejected = np.zeros((output_height, output_width), dtype=np.bool_)
    sampled = np.empty((output_height, output_width, 2), dtype=np.int32)
    for gy in range(output_height):
        for gx in range(output_width):
            predicted_x = int(predictor_origin[gy, gx, 0])
            predicted_y = int(predictor_origin[gy, gx, 1])
            normalized_x = f32(f32(float(predicted_x)) / f32(float(width)))
            normalized_y = f32(f32(float(predicted_y)) / f32(float(height)))
            sample_x = int(f32(f32(float(width)) * normalized_x))
            sample_y = int(f32(f32(float(height)) * normalized_y))
            sample_x = min(max(sample_x, 0), width - 1)
            sample_y = min(max(sample_y, 0), height - 1)
            sampled[gy, gx] = [sample_x, sample_y]
            gain = sample_profile(profile, 17, sample_x, sample_y)
            threshold = f32(f32(np.sqrt(np.float32(gain))) * multiplier)
            rejected[gy, gx] = threshold < f32(float(minimum_sad[gy, gx]))
    return rejected, sampled


def float_bits(values):
    return values.astype("<f4", copy=False).view("<u4")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", required=True, type=Path)
    parser.add_argument("--lri", required=True, type=Path)
    parser.add_argument("--threshold-report", required=True, type=Path)
    args = parser.parse_args()

    reference = np.fromfile(args.stage_dir / "reference_level0.u16le", dtype="<u2").reshape(3120, 4160)
    source = np.fromfile(args.stage_dir / "source_level0.u16le", dtype="<u2").reshape(3120, 4160)
    previous = np.fromfile(
        args.stage_dir / "refine_16x16_search_r4.f32x2le", dtype="<f4"
    ).reshape(97, 130, 2)
    oracle = np.fromfile(
        args.stage_dir / "overlap_16x16_search_r2.f32x2le", dtype="<f4"
    ).reshape(389, 519, 2)

    candidate_flow, minimum_sad, predictor_origin = replay_candidates(reference, source, previous)
    profile, multiplier = public_threshold_inputs(args.lri, args.threshold_report)
    rejected, sampled = classify(
        profile, multiplier, minimum_sad, predictor_origin, source.shape[1], source.shape[0]
    )

    replay = candidate_flow.astype("<f4")
    sentinel = np.float32(-1000000.0)
    predictor_displacement = predictor_origin.copy()
    yy, xx = np.indices(rejected.shape)
    predictor_displacement[:, :, 0] -= xx * 8
    predictor_displacement[:, :, 1] -= yy * 8
    for channel in range(2):
        replay[:, :, channel][rejected] = (
            sentinel + predictor_displacement[:, :, channel][rejected].astype(np.float32)
        ).astype(np.float32)

    equal = np.all(float_bits(replay) == float_bits(oracle), axis=2)
    if not np.all(equal):
        bad = np.argwhere(~equal)
        examples = []
        for gy, gx in bad[:12]:
            examples.append({
                "grid": [int(gx), int(gy)],
                "replay": replay[gy, gx].tolist(),
                "oracle": oracle[gy, gx].tolist(),
                "sad": int(minimum_sad[gy, gx]),
                "predictor": predictor_origin[gy, gx].tolist(),
                "map_pixel": sampled[gy, gx].tolist(),
                "rejected": bool(rejected[gy, gx]),
            })
        raise AssertionError(
            f"final overlap mismatch: {int(equal.sum())}/{equal.size}; examples={examples}"
        )

    print(json.dumps({
        "status": "PASS",
        "vectors_bit_exact": int(equal.sum()),
        "total_vectors": int(equal.size),
        "rejected": int(rejected.sum()),
        "threshold_multiplier": multiplier,
        "minimum_sad_range": [int(minimum_sad.min()), int(minimum_sad.max())],
    }, indent=2))


if __name__ == "__main__":
    main()
