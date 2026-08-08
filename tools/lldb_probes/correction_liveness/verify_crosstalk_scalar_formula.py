#!/usr/bin/env python3
"""Replay the scalar Bayer cross-talk helper from a captured runtime packet."""

import argparse
import json
import struct
from pathlib import Path

import numpy as np


def f32(value):
    return np.float32(value)


def add(a, b):
    return f32(f32(a) + f32(b))


def sub(a, b):
    return f32(f32(a) - f32(b))


def mul(a, b):
    return f32(f32(a) * f32(b))


def lerp(a, b, t):
    return add(a, mul(sub(b, a), t))


def sample(source, y, x):
    # The helper clamps in parity-separated half-resolution lanes. At the
    # low edge this is whole-sample reflection (-1 -> +1), not edge repeat.
    y = abs(y)
    x = abs(x)
    y = min(y, source.shape[0] - 1)
    x = min(x, source.shape[1] - 1)
    return source[y, x]


def four_sum(a, b, c, d):
    return add(add(add(a, b), c), d)


def pair_sum(a, b):
    return add(a, b)


def matrix_at(corners, x, y, offset, scale):
    tx = mul(add(x, offset[0]), scale[0])
    ty = mul(add(y, offset[1]), scale[1])
    left = np.empty((4, 4), dtype=np.float32)
    result = np.empty((4, 4), dtype=np.float32)
    for row in range(4):
        for column in range(4):
            left[row, column] = lerp(corners[0, row, column], corners[1, row, column], ty)
            # Match the generated helper's operation order. It forms the
            # horizontal slope before adding the top-right coefficient.
            slope = mul(sub(corners[3, row, column], corners[2, row, column]), ty)
            slope = sub(slope, left[row, column])
            slope = add(slope, corners[2, row, column])
            result[row, column] = add(left[row, column], mul(tx, slope))
    return result


def corrected_group(source, x, y, matrix):
    lane0 = sample(source, y, x + 1)
    lane1 = sample(source, y, x)
    lane2 = sample(source, y + 1, x + 1)
    lane3 = sample(source, y + 1, x)

    candidate0 = add(
        mul(lane0, matrix[0, 0]),
        mul(
            four_sum(
                sample(source, y, x),
                sample(source, y, x + 2),
                sample(source, y - 1, x + 1),
                sample(source, y + 1, x + 1),
            ),
            mul(matrix[0, 1], f32(0.5)),
        ),
    )
    candidate1 = add(
        mul(lane1, matrix[1, 1]),
        mul(
            add(
                mul(
                    pair_sum(sample(source, y, x - 1), sample(source, y, x + 1)),
                    matrix[1, 0],
                ),
                mul(
                    pair_sum(sample(source, y - 1, x), sample(source, y + 1, x)),
                    matrix[1, 3],
                ),
            ),
            f32(0.5),
        ),
    )
    candidate2 = add(
        mul(lane2, matrix[2, 2]),
        mul(
            add(
                mul(
                    pair_sum(
                        sample(source, y, x + 1), sample(source, y + 2, x + 1)
                    ),
                    matrix[2, 0],
                ),
                mul(
                    pair_sum(
                        sample(source, y + 1, x), sample(source, y + 1, x + 2)
                    ),
                    matrix[2, 3],
                ),
            ),
            f32(0.5),
        ),
    )
    candidate3 = add(
        mul(lane3, matrix[3, 3]),
        mul(
            four_sum(
                sample(source, y + 1, x + 1),
                sample(source, y + 1, x - 1),
                sample(source, y, x),
                sample(source, y + 2, x),
            ),
            mul(matrix[3, 1], f32(0.5)),
        ),
    )
    return (candidate0, candidate1, candidate2, candidate3), (
        lane0,
        lane1,
        lane2,
        lane3,
    )


def limiter(original, limits):
    first = mul(sub(original[0], f32(1.0)), limits[0])
    middle = mul(sub(max(original[1], original[2]), f32(1.0)), limits[1])
    last = mul(sub(original[3], f32(1.0)), limits[2])
    return min(f32(1.0), max(f32(0.0), first, middle, last))


def blend(candidate, original, amount):
    return add(candidate, mul(sub(original, candidate), amount))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_dir", type=Path)
    args = parser.parse_args()

    report = json.loads((args.capture_dir / "report.json").read_text(encoding="ascii"))
    helper = report["helper"]
    source_desc = helper["source_before"]["descriptor"]
    source = np.fromfile(args.capture_dir / "source_before_f32.bin", dtype="<f4").reshape(
        source_desc["size"][1], source_desc["stride"]
    )[:, : source_desc["size"][0]]
    destination_desc = helper["destination_before"]["descriptor"]
    observed = np.fromfile(args.capture_dir / "destination_after_f32.bin", dtype="<f4").reshape(
        destination_desc["size"][1], destination_desc["stride"]
    )
    corners = np.fromfile(args.capture_dir / "prepared_matrices.bin", dtype="<f4").reshape(
        4, 4, 4
    )
    offset = struct.unpack("<2f", bytes.fromhex(helper["coordinate_offset_f32"]))
    scale = struct.unpack("<2f", bytes.fromhex(helper["coordinate_scale_f32"]))
    limits = np.fromfile(args.capture_dir / "blend_limit.bin", dtype="<f4")[:3]
    start = helper["start_i32"]
    end = helper["end_i32"]

    replay = np.array(observed, copy=True)
    alpha_counts = {}
    for y in range(start[1], end[1], 2):
        for x in range(start[0], end[0], 2):
            matrix = matrix_at(corners, x, y, offset, scale)
            candidates, originals = corrected_group(source, x, y, matrix)
            amount = limiter(originals, limits)
            alpha_counts[float(amount)] = alpha_counts.get(float(amount), 0) + 1
            replay[y, x + 1] = blend(candidates[0], originals[0], amount)
            replay[y, x] = blend(candidates[1], originals[1], amount)
            replay[y + 1, x + 1] = blend(candidates[2], originals[2], amount)
            replay[y + 1, x] = blend(candidates[3], originals[3], amount)

    tested = np.s_[start[1] : end[1], start[0] : end[0]]
    expected = observed[tested]
    actual = replay[tested]
    bit_equal = actual.view("<u4") == expected.view("<u4")
    difference = actual.astype(np.float64) - expected.astype(np.float64)
    result = {
        "samples": int(expected.size),
        "bit_equal_samples": int(np.count_nonzero(bit_equal)),
        "bit_mismatch_samples": int(np.count_nonzero(~bit_equal)),
        "rmse": float(np.sqrt(np.mean(difference * difference))),
        "max_abs": float(np.max(np.abs(difference))),
        "alpha_counts": alpha_counts,
        "mismatch_parity_counts": {
            f"y{y_parity}_x{x_parity}": int(
                np.count_nonzero(mis := (~bit_equal)[y_parity::2, x_parity::2])
            )
            for y_parity in range(2)
            for x_parity in range(2)
        },
        "first_mismatches": [],
    }
    for y, x in np.argwhere(~bit_equal)[:16]:
        result["first_mismatches"].append(
            {
                "x": int(x + start[0]),
                "y": int(y + start[1]),
                "expected": float(expected[y, x]),
                "actual": float(actual[y, x]),
                "difference": float(difference[y, x]),
            }
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["bit_mismatch_samples"] == 0 else 1)


if __name__ == "__main__":
    main()
