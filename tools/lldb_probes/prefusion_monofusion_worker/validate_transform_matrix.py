#!/usr/bin/env python3
"""Validate clean-room normalized 5/3 edge and lattice-packing pseudocode."""

from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs/prefusion_monofusion_worker"
SIDE = 16
CELLS = SIDE * SIDE
EXPECTED_FORWARD_SHA256 = (
    "d8eb695ea69277a83979a348aad7dccd5dfd070253d67fb2b519f2e921554693"
)
EXPECTED_INVERSE_SHA256 = (
    "d83beb53f1f2d367782558b7d91ec1f992b3d19140bbd2037ababcc5bf0bde55"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


INV_SQRT2 = f32(1.0 / math.sqrt(2.0))
INV_2_SQRT2 = f32(1.0 / (2.0 * math.sqrt(2.0)))
SQRT2 = f32(math.sqrt(2.0))
HALF = f32(0.5)


def read_matrix(path: Path) -> list[list[float]]:
    raw = path.read_bytes()
    require(len(raw) == CELLS * CELLS * 4, f"{path}: unexpected size")
    values = struct.unpack(f"<{CELLS * CELLS}f", raw)
    return [list(values[offset : offset + CELLS]) for offset in range(0, len(values), CELLS)]


def forward_line(values: list[float]) -> list[float]:
    even = values[::2]
    odd = values[1::2]
    details = []
    for index, odd_value in enumerate(odd):
        right = even[index + 1] if index + 1 < len(even) else even[index]
        prediction = f32(f32(even[index] + right) * INV_2_SQRT2)
        details.append(f32(f32(odd_value * INV_SQRT2) - prediction))
    smooth = []
    for index, even_value in enumerate(even):
        left = details[index - 1] if index else details[0]
        update = f32(f32(left + details[index]) * HALF)
        smooth.append(f32(f32(even_value * SQRT2) + update))
    output = [0.0] * len(values)
    output[::2] = smooth
    output[1::2] = details
    return output


def inverse_line(values: list[float]) -> list[float]:
    smooth = values[::2]
    details = values[1::2]
    even = []
    for index, smooth_value in enumerate(smooth):
        left = details[index - 1] if index else details[0]
        update = f32(f32(left + details[index]) * INV_2_SQRT2)
        even.append(f32(f32(smooth_value * INV_SQRT2) - update))
    odd = []
    for index, detail in enumerate(details):
        right = even[index + 1] if index + 1 < len(even) else even[index]
        interpolation = f32(f32(even[index] + right) * HALF)
        odd.append(f32(f32(detail * SQRT2) + interpolation))
    output = [0.0] * len(values)
    output[::2] = even
    output[1::2] = odd
    return output


def forward_block(basis: int) -> list[float]:
    block = [[0.0] * SIDE for _ in range(SIDE)]
    block[basis // SIDE][basis % SIDE] = 1.0
    stride = 1
    while stride < SIDE:
        indices = list(range(0, SIDE, stride))
        for row in indices:
            transformed = forward_line([block[row][column] for column in indices])
            for column, value in zip(indices, transformed):
                block[row][column] = value
        for column in indices:
            transformed = forward_line([block[row][column] for row in indices])
            for row, value in zip(indices, transformed):
                block[row][column] = value
        stride *= 2
    return [value for row in block for value in row]


def inverse_block(basis: int) -> list[float]:
    block = [[0.0] * SIDE for _ in range(SIDE)]
    block[basis // SIDE][basis % SIDE] = 1.0
    stride = SIDE // 2
    while stride:
        indices = list(range(0, SIDE, stride))
        for column in indices:
            transformed = inverse_line([block[row][column] for row in indices])
            for row, value in zip(indices, transformed):
                block[row][column] = value
        for row in indices:
            transformed = inverse_line([block[row][column] for column in indices])
            for column, value in zip(indices, transformed):
                block[row][column] = value
        stride //= 2
    return [value for row in block for value in row]


def maximum_error(actual: list[list[float]], producer) -> float:
    maximum = 0.0
    for basis, row in enumerate(actual):
        expected = producer(basis)
        maximum = max(maximum, max(abs(a - b) for a, b in zip(row, expected)))
    return maximum


def main() -> None:
    forward_path = RUNS / "transform_forward_matrix.bin"
    inverse_path = RUNS / "transform_inverse_matrix.bin"
    forward_raw = forward_path.read_bytes()
    require(
        hashlib.sha256(forward_raw).hexdigest() == EXPECTED_FORWARD_SHA256,
        "installed forward basis matrix changed",
    )
    require(
        hashlib.sha256(inverse_path.read_bytes()).hexdigest() == EXPECTED_INVERSE_SHA256,
        "installed inverse basis matrix changed",
    )
    forward_error = maximum_error(read_matrix(forward_path), forward_block)
    inverse_error = maximum_error(read_matrix(inverse_path), inverse_block)
    require(forward_error < 4e-7, f"forward clean-room mismatch {forward_error}")
    require(inverse_error < 4e-7, f"inverse clean-room mismatch {inverse_error}")
    print(
        "prefusion_monofusion_transform_matrix=OK "
        f"forward_max_error={forward_error:.9g} "
        f"inverse_max_error={inverse_error:.9g}"
    )
    print("edge=replicate_outer_even_for_predict_replicate_first_detail_for_update")
    print("packing=interleaved_smooth_even_detail_odd_strides_1_2_4_8")


if __name__ == "__main__":
    main()
