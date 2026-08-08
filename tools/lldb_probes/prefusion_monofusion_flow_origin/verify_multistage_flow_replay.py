#!/usr/bin/env python3
"""Bit-verify MonoFusion's four non-overlap coarse-to-fine flow stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from verify_quadratic_formula import add, quadratic_fit


STAGES = (
    {
        "name": "initial_8x8_search_r8",
        "level": 4,
        "patch": 8,
        "radius": 8,
        "size": (4, 3),
        "previous": None,
    },
    {
        "name": "refine_8x8_search_r4",
        "level": 3,
        "patch": 8,
        "radius": 4,
        "size": (16, 12),
        "previous": "initial_8x8_search_r8",
    },
    {
        "name": "refine_16x16_search_r8",
        "level": 2,
        "patch": 16,
        "radius": 8,
        "size": (32, 24),
        "previous": "refine_8x8_search_r4",
    },
    {
        "name": "refine_16x16_search_r4",
        "level": 1,
        "patch": 16,
        "radius": 4,
        "size": (130, 97),
        "previous": "refine_16x16_search_r8",
    },
)


def load_u16(path, width, height):
    values = np.fromfile(path, dtype="<u2")
    assert values.size == width * height, (path, values.size, width * height)
    return values.reshape(height, width)


def sad(reference_patch, source, sx, sy, patch):
    source_patch = source[sy:sy + patch, sx:sx + patch].astype(np.int32)
    return int(np.abs(reference_patch - source_patch).sum())


def local_search(reference_patch, source, center_x, center_y, patch, radius):
    height, width = source.shape
    costs = {}
    best = None
    for local_y in range(-radius, radius + 1):
        sy = center_y + local_y
        if sy < 0 or sy > height - patch:
            continue
        for local_x in range(-radius, radius + 1):
            sx = center_x + local_x
            if sx < 0 or sx > width - patch:
                continue
            value = sad(reference_patch, source, sx, sy, patch)
            costs[(sx, sy)] = value
            if best is None or value < best[0]:
                best = (value, sx, sy)
    return best, costs


def predictor(reference_patch, source, previous, gx, gy, bx, by, patch):
    height, width = source.shape
    previous_height, previous_width, _ = previous.shape
    prior_x = gx // 4
    prior_y = gy // 4
    best = None
    for offset_y in (-1, 0, 1):
        iy = min(max(prior_y + offset_y, 0), previous_height - 1)
        for offset_x in (-1, 0, 1):
            ix = min(max(prior_x + offset_x, 0), previous_width - 1)
            flow_x, flow_y = previous[iy, ix]
            sx = bx + int(float(flow_x) * 4.0)
            sy = by + int(float(flow_y) * 4.0)
            sx = min(max(sx, 0), width - patch - 1)
            sy = min(max(sy, 0), height - patch - 1)
            value = sad(reference_patch, source, sx, sy, patch)
            if best is None or value < best[0]:
                best = (value, sx, sy)
    return best[1], best[2]


def replay_stage(reference, source, previous, patch, radius, output_width, output_height):
    result = np.empty((output_height, output_width, 2), dtype="<f4")
    for gy in range(output_height):
        for gx in range(output_width):
            bx = gx * patch
            by = gy * patch
            reference_patch = reference[by:by + patch, bx:bx + patch].astype(np.int32)
            if previous is None:
                center_x = bx
                center_y = by
            else:
                center_x, center_y = predictor(
                    reference_patch, source, previous, gx, gy, bx, by, patch
                )

            best, costs = local_search(
                reference_patch, source, center_x, center_y, patch, radius
            )
            _minimum, sx, sy = best
            fit_available = all(
                (sx + offset_x, sy + offset_y) in costs
                for offset_y in (-1, 0, 1)
                for offset_x in (-1, 0, 1)
            )
            if fit_available:
                samples = [
                    costs[(sx + offset_x, sy + offset_y)]
                    for offset_y in (-1, 0, 1)
                    for offset_x in (-1, 0, 1)
                ]
                subpixel_x, subpixel_y = quadratic_fit(samples)
            else:
                subpixel_x = 0.0
                subpixel_y = 0.0

            predictor_x = center_x - bx
            predictor_y = center_y - by
            local_x = sx - center_x
            local_y = sy - center_y
            result[gy, gx, 0] = add(predictor_x, add(local_x, subpixel_x))
            result[gy, gx, 1] = add(predictor_y, add(local_y, subpixel_y))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage_dir", type=Path)
    args = parser.parse_args()

    observed = {}
    total = 0
    report = json.loads((args.stage_dir / "stages.json").read_text(encoding="ascii"))
    for stage in STAGES:
        name = stage["name"]
        level = stage["level"]
        oracle_width, oracle_height = stage["size"]
        oracle = np.fromfile(args.stage_dir / f"{name}.f32x2le", dtype="<f4").reshape(
            oracle_height, oracle_width, 2
        )
        descriptor = next(
            item["descriptor"] for item in report["intermediate_stages"] if item["stage"] == name
        )
        assert descriptor["size"] == [oracle_width, oracle_height]
        pyramid = report["pyramid_inputs"][0]
        reference_descriptor = pyramid["reference"]["records"][level]
        source_descriptor = pyramid["source"]["records"][level]
        width, height = reference_descriptor["size"]
        assert source_descriptor["size"] == [width, height]
        reference = load_u16(
            args.stage_dir / f"reference_level{level}.u16le", width, height
        )
        source = load_u16(args.stage_dir / f"source_level{level}.u16le", width, height)
        previous = observed.get(stage["previous"])
        replay = replay_stage(
            reference,
            source,
            previous,
            stage["patch"],
            stage["radius"],
            oracle_width,
            oracle_height,
        )
        equal = np.all(replay.view("<u4") == oracle.view("<u4"), axis=2)
        if not np.all(equal):
            bad = np.argwhere(~equal)
            examples = [
                {
                    "grid": [int(gx), int(gy)],
                    "replay": replay[gy, gx].tolist(),
                    "oracle": oracle[gy, gx].tolist(),
                }
                for gy, gx in bad[:12]
            ]
            raise AssertionError(
                f"{name}: {int(equal.sum())}/{equal.size} bit-exact; {examples}"
            )
        observed[name] = replay
        total += equal.size
        print(name, f"{equal.size}/{equal.size} vectors bit-exact")
    print("verified", total, "coarse-to-fine vectors bit-exact")


if __name__ == "__main__":
    main()
