#!/usr/bin/env python3
"""Verify CreateStereoImage input against its public packed-RAW10 surface."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RAW_VERIFIER = ROOT / "tools/lldb_probes/raw_sensor_layout/verify_raw_sensor_layout.py"
DEFAULT_RUNS = (
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_input_unit1_28mm",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_input_new_06689",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_input_unit2_28mm",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RAW = load_module("create_stereo_input_raw", RAW_VERIFIER)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def locate_public_surface(path: Path, camera_key: int) -> tuple[int, dict]:
    matches = []
    for block in RAW.lri.scan_lri_blocks(str(path)):
        for wire_type, module in RAW.fields(block["payload"]).get(12, []):
            if wire_type != 2:
                continue
            surface = RAW.decode_surface(module)
            if surface["camera_id"] == camera_key:
                matches.append((block["block_offset"], surface))
    require(len(matches) == 1, f"{path}: camera {camera_key} surface count {len(matches)}")
    return matches[0]


def unpack_row(raw: bytes) -> np.ndarray:
    require(len(raw) == RAW.ROW_STRIDE, f"packed row size {len(raw)}")
    groups = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 10).astype(np.uint16)
    result = np.empty(groups.shape[0] * 8, dtype="<u2")
    result[0::8] = groups[:, 0] | ((groups[:, 1] & 0x03) << 8)
    result[1::8] = (groups[:, 1] >> 2) | ((groups[:, 2] & 0x0F) << 6)
    result[2::8] = (groups[:, 2] >> 4) | ((groups[:, 3] & 0x3F) << 4)
    result[3::8] = (groups[:, 3] >> 6) | (groups[:, 4] << 2)
    result[4::8] = groups[:, 5] | ((groups[:, 6] & 0x03) << 8)
    result[5::8] = (groups[:, 6] >> 2) | ((groups[:, 7] & 0x0F) << 6)
    result[6::8] = (groups[:, 7] >> 4) | ((groups[:, 8] & 0x3F) << 4)
    result[7::8] = (groups[:, 8] >> 6) | (groups[:, 9] << 2)
    return result


def verify_run(run_dir: Path) -> dict:
    report = json.loads((run_dir / "report.json").read_text(encoding="ascii"))
    require(not report["errors"], f"{run_dir}: capture errors {report['errors']}")
    require(report["terminated_after_capture"], f"{run_dir}: incomplete capture")
    capture = report["capture"]
    require(capture is not None, f"{run_dir}: missing capture")
    descriptor = capture["descriptor"]
    require(descriptor["origin"] == [0, 0], f"{run_dir}: origin")
    require(descriptor["size"] == [RAW.WIDTH, RAW.HEIGHT], f"{run_dir}: size")
    require(descriptor["stride"] == RAW.WIDTH, f"{run_dir}: stride")
    observed_path = run_dir / "create_stereo_input.u16le"
    require(sha256(observed_path) == capture["artifact"]["sha256"], f"{run_dir}: SHA")
    require(observed_path.stat().st_size == RAW.WIDTH * RAW.HEIGHT * 2, f"{run_dir}: bytes")

    source_lri = Path(report["source_lri"])
    require(source_lri.is_file(), f"{run_dir}: source LRI unavailable")
    block_offset, surface = locate_public_surface(source_lri, int(capture["source_key"]))
    require((surface["width"], surface["height"]) == (RAW.WIDTH, RAW.HEIGHT), f"{run_dir}: public size")
    require(surface["format"] == 7, f"{run_dir}: public format")
    require(surface["row_stride"] == RAW.ROW_STRIDE, f"{run_dir}: public stride")

    digest = hashlib.sha256()
    mismatches = 0
    with source_lri.open("rb") as packed, observed_path.open("rb") as observed:
        packed.seek(block_offset + surface["data_offset"])
        for row in range(RAW.HEIGHT):
            expected = unpack_row(packed.read(RAW.ROW_STRIDE)).tobytes()
            actual = observed.read(RAW.WIDTH * 2)
            require(len(actual) == len(expected), f"{run_dir}: observed row {row}")
            digest.update(expected)
            if actual != expected:
                left = np.frombuffer(actual, dtype="<u2")
                right = np.frombuffer(expected, dtype="<u2")
                mismatches += int(np.count_nonzero(left != right))
    require(mismatches == 0, f"{run_dir}: {mismatches} RAW sample mismatches")
    require(digest.hexdigest() == capture["artifact"]["sha256"], f"{run_dir}: rebuilt SHA")
    return {
        "run": run_dir.name,
        "source_lri": str(source_lri),
        "camera_key": capture["source_key"],
        "pixels": RAW.WIDTH * RAW.HEIGHT,
        "sha256": digest.hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", nargs="*", type=Path)
    args = parser.parse_args()
    RAW.verify_installed()
    rows = [verify_run(path) for path in (args.run_dir or DEFAULT_RUNS)]
    for row in rows:
        print(
            f"{row['run']}: camera={row['camera_key']} pixels={row['pixels']} "
            f"sha256={row['sha256']} public_RAW10=exact"
        )
    print(f"create_stereo_input_public_raw=OK runs={len(rows)}")


if __name__ == "__main__":
    main()
