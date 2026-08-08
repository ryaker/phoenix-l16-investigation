#!/usr/bin/env python3
"""Stream-compare two Radiance RGBE images without loading full rasters."""

from __future__ import annotations

import hashlib
import re
import sys
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
        require(len(row) == width * 4, "truncated flat RGBE scanline")
        return row
    marker = handle.read(4)
    require(
        len(marker) == 4
        and marker[0] == 2
        and marker[1] == 2
        and ((marker[2] << 8) | marker[3]) == width,
        f"unsupported scanline marker {marker!r}",
    )
    channels = []
    for _ in range(4):
        decoded = bytearray()
        while len(decoded) < width:
            code_raw = handle.read(1)
            require(code_raw, "truncated RLE code")
            code = code_raw[0]
            require(code != 0, "zero RLE code")
            if code > 128:
                count = code - 128
                value = handle.read(1)
                require(value, "truncated RLE run")
                decoded.extend(value * count)
            else:
                literal = handle.read(code)
                require(len(literal) == code, "truncated RLE literal")
                decoded.extend(literal)
        require(len(decoded) == width, "RLE run exceeded scanline")
        channels.append(decoded)
    output = bytearray(width * 4)
    for x in range(width):
        for channel in range(4):
            output[x * 4 + channel] = channels[channel][x]
    return bytes(output)


def compare(left_path: Path, right_path: Path) -> dict:
    left_hash = hashlib.sha256()
    right_hash = hashlib.sha256()
    differing_pixels = 0
    differing_channels = 0
    absolute_sum = 0
    maximum = 0
    with left_path.open("rb") as left, right_path.open("rb") as right:
        width_l, height_l, header_l = read_header(left)
        width_r, height_r, header_r = read_header(right)
        require((width_l, height_l) == (width_r, height_r), "dimension mismatch")
        flat_l = left_path.stat().st_size - left.tell() == width_l * height_l * 4
        flat_r = right_path.stat().st_size - right.tell() == width_r * height_r * 4
        require(flat_l == flat_r, "payload encoding mismatch")
        left_hash.update(header_l)
        right_hash.update(header_r)
        for _ in range(height_l):
            row_l = read_scanline(left, width_l, flat_l)
            row_r = read_scanline(right, width_l, flat_r)
            left_hash.update(row_l)
            right_hash.update(row_r)
            pixels_l = np.frombuffer(row_l, dtype=np.uint8).reshape((-1, 4))
            pixels_r = np.frombuffer(row_r, dtype=np.uint8).reshape((-1, 4))
            difference = np.abs(
                pixels_l.astype(np.int16) - pixels_r.astype(np.int16)
            )
            differing_pixels += int(np.count_nonzero(np.any(difference, axis=1)))
            differing_channels += int(np.count_nonzero(difference))
            absolute_sum += int(np.sum(difference, dtype=np.int64))
            maximum = max(maximum, int(np.max(difference)))
        require(left.read(1) == right.read(1) == b"", "trailing Radiance data")
    pixels = width_l * height_l
    return {
        "width": width_l,
        "height": height_l,
        "pixels": pixels,
        "differing_pixels": differing_pixels,
        "differing_pixel_fraction": differing_pixels / pixels,
        "differing_channels": differing_channels,
        "mean_abs_code_all_channels": absolute_sum / (pixels * 4),
        "max_abs_code": maximum,
        "decoded_sha256_left": left_hash.hexdigest(),
        "decoded_sha256_right": right_hash.hexdigest(),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} LEFT.hdr RIGHT.hdr")
    result = compare(Path(sys.argv[1]), Path(sys.argv[2]))
    for key, value in result.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
