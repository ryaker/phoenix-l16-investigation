#!/usr/bin/env python3
"""Replay the captured top-row vec4 vignetting store."""

import argparse
import json
import struct
from pathlib import Path


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def first_f32s(packet, pointee, count=2):
    raw = bytes.fromhex(packet["context_pointees"][str(pointee)]["first_96_hex"])
    return struct.unpack("<" + "f" * count, raw[: count * 4])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    packet = json.loads(args.report.read_text())["packet"]

    step_x, step_y = first_f32s(packet, 1)
    origin_x, origin_y = first_f32s(packet, 6)
    if origin_y != 0.0 or packet["registers"]["r15"] != 0:
        raise AssertionError("captured packet is not the expected top-row discriminator")
    profile = packet["profile_f32"]
    grid_x = int(origin_x // step_x)
    local_x = f32(origin_x - f32(grid_x * step_x))
    slope = f32(f32(profile[grid_x + 1] - profile[grid_x]) / step_x)
    factor = f32(float(local_x) * float(slope) + float(profile[grid_x]))
    expected = [
        f32(packet["source_vec4"][lane] * factor) for lane in range(3)
    ] + [packet["source_vec4"][3]]
    if expected != packet["xmm0_output"]:
        raise AssertionError(
            f"store mismatch expected={expected} observed={packet['xmm0_output']}"
        )
    print(
        json.dumps(
            {
                "status": "PASS",
                "step": [step_x, step_y],
                "origin": [origin_x, origin_y],
                "grid_x": grid_x,
                "factor": factor,
                "source": packet["source_vec4"],
                "output": expected,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
