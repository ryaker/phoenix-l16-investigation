#!/usr/bin/env python3
"""Pairwise streaming statistics for repeated full-resolution RGBE renders."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

import numpy as np


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_header(handle):
    header = []
    while True:
        line = handle.readline()
        require(line, "truncated Radiance header")
        header.append(line)
        if line in (b"\n", b"\r\n"):
            break
    resolution = handle.readline()
    match = re.fullmatch(rb"-Y (\d+) \+X (\d+)\r?\n", resolution)
    require(match is not None, f"unsupported resolution line {resolution!r}")
    return int(match.group(2)), int(match.group(1)), b"".join(header) + resolution


def read_scanline(handle, width: int, flat: bool) -> bytes:
    if flat:
        row = handle.read(width * 4)
        require(len(row) == width * 4, "truncated flat scanline")
        return row
    marker = handle.read(4)
    require(
        len(marker) == 4
        and marker[0] == marker[1] == 2
        and ((marker[2] << 8) | marker[3]) == width,
        f"unsupported scanline marker {marker!r}",
    )
    channels = []
    for _ in range(4):
        decoded = bytearray()
        while len(decoded) < width:
            code = handle.read(1)
            require(code and code[0], "truncated/zero RLE code")
            if code[0] > 128:
                count = code[0] - 128
                value = handle.read(1)
                require(value, "truncated RLE run")
                decoded.extend(value * count)
            else:
                literal = handle.read(code[0])
                require(len(literal) == code[0], "truncated RLE literal")
                decoded.extend(literal)
        require(len(decoded) == width, "RLE run exceeded row")
        channels.append(decoded)
    output = np.empty((width, 4), dtype=np.uint8)
    for channel in range(4):
        output[:, channel] = np.frombuffer(channels[channel], dtype=np.uint8)
    return output.tobytes()


def decode_rgbe(row: np.ndarray) -> np.ndarray:
    exponent = row[:, 3].astype(np.int16)
    scale = np.ldexp(
        np.ones(exponent.shape, dtype=np.float64),
        exponent - (128 + 8),
    )
    scale[exponent == 0] = 0.0
    return (row[:, :3].astype(np.float64) + 0.5) * scale[:, None]


def distribution(values: list[float]) -> dict:
    return {
        "min": min(values),
        "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
        "max": max(values),
    }


def analyze_group(paths: list[Path]) -> dict:
    require(len(paths) >= 2, "need at least two repeats")
    handles = [path.open("rb") for path in paths]
    try:
        headers = [read_header(handle) for handle in handles]
        dimensions = {(width, height) for width, height, _header in headers}
        require(len(dimensions) == 1, "repeat dimension mismatch")
        width, height = dimensions.pop()
        flat = [
            path.stat().st_size - handle.tell() == width * height * 4
            for path, handle in zip(paths, handles)
        ]
        require(len(set(flat)) == 1, "repeat encoding mismatch")
        pairs = list(itertools.combinations(range(len(paths)), 2))
        accumulators = {
            pair: {
                "differing_pixels": 0,
                "differing_channels": 0,
                "absolute_sum": 0,
                "maximum": 0,
                "linear_absolute_sum": 0.0,
                "linear_squared_sum": 0.0,
                "linear_symmetric_magnitude_sum": 0.0,
                "linear_symmetric_energy_sum": 0.0,
                "log2_luminance_absolute_sum": 0.0,
                "log2_luminance_count": 0,
            }
            for pair in pairs
        }
        hashes = [hashlib.sha256(header).copy() for _width, _height, header in headers]
        for _row in range(height):
            rows = []
            for index, handle in enumerate(handles):
                row = read_scanline(handle, width, flat[index])
                hashes[index].update(row)
                rows.append(np.frombuffer(row, dtype=np.uint8).reshape((-1, 4)))
            linear_rows = [decode_rgbe(row) for row in rows]
            luminance_rows = [
                np.mean(linear_row, axis=1) for linear_row in linear_rows
            ]
            for pair in pairs:
                left, right = pair
                difference = np.abs(
                    rows[left].astype(np.int16) - rows[right].astype(np.int16)
                )
                accumulator = accumulators[pair]
                accumulator["differing_pixels"] += int(
                    np.count_nonzero(np.any(difference, axis=1))
                )
                accumulator["differing_channels"] += int(np.count_nonzero(difference))
                accumulator["absolute_sum"] += int(np.sum(difference, dtype=np.int64))
                accumulator["maximum"] = max(
                    accumulator["maximum"], int(np.max(difference))
                )
                linear_left = linear_rows[left]
                linear_right = linear_rows[right]
                linear_difference = np.abs(linear_left - linear_right)
                accumulator["linear_absolute_sum"] += float(
                    np.sum(linear_difference, dtype=np.float64)
                )
                accumulator["linear_squared_sum"] += float(
                    np.sum(linear_difference * linear_difference, dtype=np.float64)
                )
                accumulator["linear_symmetric_magnitude_sum"] += float(
                    np.sum(
                        np.abs(linear_left) + np.abs(linear_right),
                        dtype=np.float64,
                    )
                )
                accumulator["linear_symmetric_energy_sum"] += float(
                    np.sum(
                        0.5
                        * (
                            linear_left * linear_left
                            + linear_right * linear_right
                        ),
                        dtype=np.float64,
                    )
                )
                luminance_left = luminance_rows[left]
                luminance_right = luminance_rows[right]
                valid = np.maximum(luminance_left, luminance_right) > 2.0**-20
                if np.any(valid):
                    log_difference = np.abs(
                        np.log2(np.maximum(luminance_left[valid], 2.0**-24))
                        - np.log2(np.maximum(luminance_right[valid], 2.0**-24))
                    )
                    accumulator["log2_luminance_absolute_sum"] += float(
                        np.sum(log_difference, dtype=np.float64)
                    )
                    accumulator["log2_luminance_count"] += int(
                        np.count_nonzero(valid)
                    )
        require(all(handle.read(1) == b"" for handle in handles), "trailing data")
    finally:
        for handle in handles:
            handle.close()

    pixels = width * height
    pair_results = []
    for left, right in pairs:
        accumulator = accumulators[(left, right)]
        pair_results.append(
            {
                "left": paths[left].name,
                "right": paths[right].name,
                "differing_pixel_fraction": accumulator["differing_pixels"] / pixels,
                "mean_abs_code_all_channels": accumulator["absolute_sum"]
                / (pixels * 4),
                "max_abs_code": accumulator["maximum"],
                "linear_mean_abs_rgb": accumulator["linear_absolute_sum"]
                / (pixels * 3),
                "linear_rmse_rgb": math.sqrt(
                    accumulator["linear_squared_sum"] / (pixels * 3)
                ),
                "linear_symmetric_l1": accumulator["linear_absolute_sum"]
                / accumulator["linear_symmetric_magnitude_sum"]
                if accumulator["linear_symmetric_magnitude_sum"]
                else 0.0,
                "linear_normalized_rmse": math.sqrt(
                    accumulator["linear_squared_sum"]
                    / accumulator["linear_symmetric_energy_sum"]
                )
                if accumulator["linear_symmetric_energy_sum"]
                else 0.0,
                "mean_abs_log2_luminance": accumulator[
                    "log2_luminance_absolute_sum"
                ]
                / accumulator["log2_luminance_count"]
                if accumulator["log2_luminance_count"]
                else 0.0,
            }
        )
    means = [item["mean_abs_code_all_channels"] for item in pair_results]
    fractions = [item["differing_pixel_fraction"] for item in pair_results]
    maxima = [item["max_abs_code"] for item in pair_results]
    return {
        "width": width,
        "height": height,
        "repeat_count": len(paths),
        "pair_count": len(pair_results),
        "decoded_sha256": {
            path.name: digest.hexdigest() for path, digest in zip(paths, hashes)
        },
        "mean_abs_code_distribution": {
            "min": min(means),
            "median": float(np.median(means)),
            "p95": float(np.percentile(means, 95)),
            "max": max(means),
        },
        "differing_pixel_fraction_distribution": {
            "min": min(fractions),
            "median": float(np.median(fractions)),
            "p95": float(np.percentile(fractions, 95)),
            "max": max(fractions),
        },
        "max_abs_code_distribution": {
            "min": min(maxima),
            "median": float(np.median(maxima)),
            "max": max(maxima),
        },
        "linear_symmetric_l1_distribution": distribution(
            [item["linear_symmetric_l1"] for item in pair_results]
        ),
        "linear_normalized_rmse_distribution": distribution(
            [item["linear_normalized_rmse"] for item in pair_results]
        ),
        "mean_abs_log2_luminance_distribution": distribution(
            [item["mean_abs_log2_luminance"] for item in pair_results]
        ),
        "pairs": pair_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = {}
    for directory in sorted(path for path in args.root.iterdir() if path.is_dir()):
        paths = sorted(directory.glob("repeat_*.hdr"))
        if len(paths) >= 2:
            print(f"ANALYZE {directory.name} repeats={len(paths)}")
            result[directory.name] = analyze_group(paths)
    require(result, "no repeat groups found")
    packet = {"status": "OK", "groups": result}
    if args.json_out:
        args.json_out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    for label, group in result.items():
        distribution = group["mean_abs_code_distribution"]
        print(
            f"{label} pairs={group['pair_count']} "
            f"mean_abs_code_p95={distribution['p95']:.12g} "
            f"max={distribution['max']:.12g}"
        )


if __name__ == "__main__":
    main()
