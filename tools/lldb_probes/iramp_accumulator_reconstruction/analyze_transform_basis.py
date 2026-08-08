#!/usr/bin/env python3
"""Derive and verify the separable 16-point inverse transform basis."""

from __future__ import annotations

import struct
import sys
from pathlib import Path


SIDE = 16
RESPONSE_FLOATS = SIDE**4


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


INV_K = f32(0.869864404)
K = f32(1.14960444)
DELTA_K = f32(0.509857476)
TWO_DELTA_K = f32(1.01971495)
NEG_GAMMA = f32(-0.882911086)
TWO_NEG_GAMMA = f32(-1.76582217)
BETA = f32(-0.0529801175)
TWO_BETA = f32(-0.105960235)
NEG_ALPHA = f32(1.58613431)
TWO_NEG_ALPHA = f32(3.17226863)


def add(a: float, b: float) -> float:
    return f32(f32(a) + f32(b))


def sub(a: float, b: float) -> float:
    return f32(f32(a) - f32(b))


def mul(a: float, b: float) -> float:
    return f32(f32(a) * f32(b))


def inverse97(values: list[float]) -> list[float]:
    out = [f32(value) for value in values]
    count = len(out)
    require(count >= 2 and count % 2 == 0, "inverse97 even length")

    for index in range(0, count, 2):
        scaled = mul(out[index], INV_K)
        if index == 0:
            correction = mul(out[1], TWO_DELTA_K)
        else:
            correction = mul(add(out[index - 1], out[index + 1]), DELTA_K)
        out[index] = sub(scaled, correction)

    for index in range(1, count, 2):
        scaled = mul(out[index], K)
        if index == count - 1:
            correction = mul(out[index - 1], TWO_NEG_GAMMA)
        else:
            correction = mul(add(out[index - 1], out[index + 1]), NEG_GAMMA)
        out[index] = add(scaled, correction)

    for index in range(0, count, 2):
        if index == 0:
            correction = mul(out[1], TWO_BETA)
        else:
            correction = mul(add(out[index - 1], out[index + 1]), BETA)
        out[index] = sub(out[index], correction)

    for index in range(1, count, 2):
        if index == count - 1:
            correction = mul(out[index - 1], TWO_NEG_ALPHA)
        else:
            correction = mul(add(out[index - 1], out[index + 1]), NEG_ALPHA)
        out[index] = add(out[index], correction)
    return out


def reconstruct_basis(input_y: int, input_x: int, vertical_first: bool) -> list[float]:
    tile = [[0.0 for _ in range(SIDE)] for _ in range(SIDE)]
    tile[input_y][input_x] = 1.0
    for stride in (8, 4, 2, 1):
        coordinates = list(range(0, SIDE, stride))

        def horizontal() -> None:
            for y in coordinates:
                transformed = inverse97([tile[y][x] for x in coordinates])
                for x, value in zip(coordinates, transformed):
                    tile[y][x] = value

        def vertical() -> None:
            for x in coordinates:
                transformed = inverse97([tile[y][x] for y in coordinates])
                for y, value in zip(coordinates, transformed):
                    tile[y][x] = value

        if vertical_first:
            vertical()
            horizontal()
        else:
            horizontal()
            vertical()
    return [value for row in tile for value in row]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} BASIS.bin")
    path = Path(sys.argv[1])
    raw = path.read_bytes()
    require(len(raw) == RESPONSE_FLOATS * 4, "basis file size")
    values = struct.unpack(f"<{RESPONSE_FLOATS}f", raw)

    def response(iy: int, ix: int, oy: int, ox: int) -> float:
        input_index = iy * SIDE + ix
        output_index = oy * SIDE + ox
        return values[input_index * SIDE * SIDE + output_index]

    results = []
    for vertical_first in (False, True):
        max_error = 0.0
        max_location = None
        exact_bits = 0
        for iy in range(SIDE):
            for ix in range(SIDE):
                expected = reconstruct_basis(iy, ix, vertical_first)
                for output_index, predicted in enumerate(expected):
                    oy, ox = divmod(output_index, SIDE)
                    actual = response(iy, ix, oy, ox)
                    error = abs(actual - predicted)
                    if struct.pack("<f", actual) == struct.pack("<f", predicted):
                        exact_bits += 1
                    if error > max_error:
                        max_error = error
                        max_location = (iy, ix, oy, ox, actual, predicted)
        results.append((max_error, exact_bits, vertical_first, max_location))

    best = min(results)
    max_error, exact_bits, vertical_first, max_location = best
    print(
        "schedule="
        + ("vertical_then_horizontal" if vertical_first else "horizontal_then_vertical")
    )
    print(f"basis_exact_float_bits={exact_bits}/{RESPONSE_FLOATS}")
    print(f"basis_max_abs_error={max_error:.12g} at={max_location}")
    require(max_error < 3e-5, f"inverse lifting mismatch: {max_location}")
    print("iramp_inverse_transform_basis=OK")


if __name__ == "__main__":
    main()
