#!/usr/bin/env python3
"""Join MonoFusion's full-resolution source flow operand to public A2 RAW."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_REPLAY = (
    ROOT
    / "tools/lldb_probes/index5_guidance_channel_origin"
    / "verify_create_stereo_mono_public_reconstruction.py"
)
EXPECTED_LIBCP_SHA256 = (
    "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
)
LUT_OFFSET = 0x5CC080
WIDTH = 4160
HEIGHT = 3120


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("flow_source_public_replay", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PUBLIC = load_module(PUBLIC_REPLAY)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", required=True, type=Path)
    parser.add_argument("--lri", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--hotpixel-report", required=True, type=Path)
    args = parser.parse_args()

    digest = hashlib.sha256(args.libcp.read_bytes()).hexdigest()
    assert digest == EXPECTED_LIBCP_SHA256, digest
    with args.libcp.open("rb") as handle:
        handle.seek(LUT_OFFSET)
        lut = np.array(struct.unpack("<4096H", handle.read(8192)), dtype=np.uint16)

    surface, packed, context = PUBLIC.find_a2_surface(args.lri)
    raw = PUBLIC.unpack_raw10(packed, surface["row_stride"])
    hotpixel_report = json.loads(args.hotpixel_report.read_text(encoding="ascii"))
    assert hotpixel_report["complete"] and not hotpixel_report["errors"]
    hotpixel_source_path = Path(hotpixel_report["helper"]["source_dump"]["path"])
    hotpixel_output_path = Path(hotpixel_report["helper"]["destination_dump"]["path"])
    hotpixel_source_bytes = hotpixel_source_path.read_bytes()
    hotpixel_output_bytes = hotpixel_output_path.read_bytes()
    assert (
        hashlib.sha256(hotpixel_source_bytes).hexdigest()
        == hotpixel_report["helper"]["source_dump"]["sha256"]
    )
    assert (
        hashlib.sha256(hotpixel_output_bytes).hexdigest()
        == hotpixel_report["helper"]["destination_dump"]["sha256"]
    )
    hotpixel_source = np.frombuffer(hotpixel_source_bytes, dtype="<u2").reshape(
        HEIGHT, WIDTH
    )
    corrected = np.frombuffer(hotpixel_output_bytes, dtype="<u2").reshape(
        HEIGHT, WIDTH
    )
    assert np.array_equal(raw, hotpixel_source), "public A2 RAW != hot-pixel input"
    black, _white = PUBLIC.sensor_levels(context["blocks"])
    profile = PUBLIC.selected_profile(args.lri, 1, surface["lens_position"])
    shading = PUBLIC.vignetting_plane(profile)

    black_subtracted = np.subtract(
        corrected.astype(np.float32), black, dtype=np.float32
    )
    prepared = np.multiply(black_subtracted, shading, dtype=np.float32)
    indices = np.trunc(prepared + np.float32(0.5)).astype(np.int32)
    np.clip(indices, 1, 4095, out=indices)
    rebuilt = lut[indices]

    observed = np.fromfile(args.observed, dtype="<u2").reshape(HEIGHT, WIDTH)
    equal = rebuilt == observed
    exact = int(equal.sum())
    if exact != equal.size:
        bad = np.argwhere(~equal)
        examples = [
            {
                "xy": [int(x), int(y)],
                "raw": int(raw[y, x]),
                "vignetting": float(shading[y, x]),
                "prepared": float(prepared[y, x]),
                "index": int(indices[y, x]),
                "rebuilt": int(rebuilt[y, x]),
                "observed": int(observed[y, x]),
            }
            for y, x in bad[:12]
        ]
        raise AssertionError(f"{exact}/{equal.size} source pixels exact; {examples}")
    print(
        "flow_source_public_origin=OK",
        f"pixels={exact}/{equal.size}",
        f"camera_key=1",
        f"lens_position={surface['lens_position']}",
        f"black_level={float(black)}",
        f"raw_sha256={hashlib.sha256(packed).hexdigest()}",
        f"hotpixel_input_sha256={hashlib.sha256(hotpixel_source_bytes).hexdigest()}",
        f"hotpixel_output_sha256={hashlib.sha256(hotpixel_output_bytes).hexdigest()}",
        f"hotpixel_changed={int(np.count_nonzero(corrected != raw))}",
        f"output_sha256={hashlib.sha256(rebuilt.tobytes()).hexdigest()}",
    )


if __name__ == "__main__":
    main()
