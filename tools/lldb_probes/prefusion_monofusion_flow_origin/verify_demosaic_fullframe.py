#!/usr/bin/env python3
"""Bit-compare an installed DemosaickLightV1 RGBA capture and clean-room replay."""

import argparse
import hashlib
import json
import struct
from pathlib import Path


WIDTH = 4160
HEIGHT = 3120
CHANNELS = 4
EXPECTED_BYTES = WIDTH * HEIGHT * CHANNELS * 4


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("installed", type=Path)
    parser.add_argument("cleanroom", type=Path)
    parser.add_argument("--label", default="DemosaickLightV1 RGBA")
    args = parser.parse_args()

    installed = args.installed.read_bytes()
    cleanroom = args.cleanroom.read_bytes()
    if len(installed) != EXPECTED_BYTES or len(cleanroom) != EXPECTED_BYTES:
        raise SystemExit(
            f"expected {EXPECTED_BYTES} bytes per input, got "
            f"installed={len(installed)} cleanroom={len(cleanroom)}"
        )

    mismatches = 0
    max_abs = 0.0
    first = None
    for word in range(WIDTH * HEIGHT * CHANNELS):
        begin = word * 4
        if installed[begin:begin + 4] == cleanroom[begin:begin + 4]:
            continue
        mismatches += 1
        have = struct.unpack_from("<f", cleanroom, begin)[0]
        want = struct.unpack_from("<f", installed, begin)[0]
        max_abs = max(max_abs, abs(have - want))
        if first is None:
            pixel, channel = divmod(word, CHANNELS)
            y, x = divmod(pixel, WIDTH)
            first = {
                "x": x,
                "y": y,
                "channel": channel,
                "installed": want,
                "cleanroom": have,
            }

    result = {
        "label": args.label,
        "words": WIDTH * HEIGHT * CHANNELS,
        "mismatches": mismatches,
        "max_abs": max_abs,
        "first_mismatch": first,
        "installed_sha256": digest(installed),
        "cleanroom_sha256": digest(cleanroom),
    }
    print(json.dumps(result, indent=2))
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
