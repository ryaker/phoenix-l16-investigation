#!/usr/bin/env python3
"""Bit-replay a captured ColorFusion 16x16xvec4 forward transform."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


SIDE = 16
LANES = 4
INV_SQRT2 = struct.unpack("<f", bytes.fromhex("f304353f"))[0]
INV_2_SQRT2 = struct.unpack("<f", bytes.fromhex("f304b53e"))[0]
SQRT2 = struct.unpack("<f", bytes.fromhex("f304b53f"))[0]
HALF = struct.unpack("<f", bytes.fromhex("ffffff3e"))[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def forward_line(values: list[float]) -> list[float]:
    even = values[::2]
    odd = values[1::2]
    detail = []
    for index, odd_value in enumerate(odd):
        right = even[index + 1] if index + 1 < len(even) else even[index]
        prediction = f32(f32(even[index] + right) * INV_2_SQRT2)
        detail.append(f32(f32(odd_value * INV_SQRT2) - prediction))
    smooth = []
    for index, even_value in enumerate(even):
        left = detail[index - 1] if index else detail[0]
        update = f32(f32(left + detail[index]) * HALF)
        smooth.append(f32(f32(even_value * SQRT2) + update))
    output = [0.0] * len(values)
    output[::2] = smooth
    output[1::2] = detail
    return output


def forward_block(raw: bytes) -> bytes:
    require(len(raw) == SIDE * SIDE * LANES * 4, "unexpected input size")
    flat = list(struct.unpack("<1024f", raw))
    block = [
        [
            [flat[(row * SIDE + column) * LANES + lane] for lane in range(LANES)]
            for column in range(SIDE)
        ]
        for row in range(SIDE)
    ]
    for stride in (1, 2, 4, 8):
        indices = list(range(0, SIDE, stride))
        for row in indices:
            for lane in range(LANES):
                transformed = forward_line([block[row][column][lane] for column in indices])
                for column, value in zip(indices, transformed):
                    block[row][column][lane] = value
        for column in indices:
            for lane in range(LANES):
                transformed = forward_line([block[row][column][lane] for row in indices])
                for row, value in zip(indices, transformed):
                    block[row][column][lane] = value
    values = [
        block[row][column][lane]
        for row in range(SIDE)
        for column in range(SIDE)
        for lane in range(LANES)
    ]
    return struct.pack("<1024f", *values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    record = json.loads(args.capture.read_text())
    before = (args.capture.parent / record["before"]["file"]).read_bytes()
    after = (args.capture.parent / record["after"]["file"]).read_bytes()
    require(hashlib.sha256(before).hexdigest() == record["before"]["sha256"], "before SHA mismatch")
    require(hashlib.sha256(after).hexdigest() == record["after"]["sha256"], "after SHA mismatch")
    replay = forward_block(before)
    actual_words = struct.unpack("<1024I", after)
    replay_words = struct.unpack("<1024I", replay)
    mismatches = sum(actual != expected for actual, expected in zip(actual_words, replay_words))
    require(mismatches == 0, f"transform differs at {mismatches}/1024 float32 words")
    print(
        "colorfusion_transform_runtime=PASS "
        f"words=1024 mismatches={mismatches} after_sha256={record['after']['sha256']}"
    )


if __name__ == "__main__":
    main()
