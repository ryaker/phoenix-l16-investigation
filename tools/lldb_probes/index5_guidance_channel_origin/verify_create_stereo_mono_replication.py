#!/usr/bin/env python3
"""Verify A2 scalar-to-vec4 conversion in CreateStereoImage."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
DEFAULT_RUNS = (
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_mono_replication_unit1_28mm",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_mono_replication_new_06689",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_mono_replication_unit2_28mm",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("mono_replication_static", STATIC_PATH)


def verify_static() -> str:
    data = STATIC.LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")
    mapping = STATIC.segments(data)
    body = STATIC.bytes_at(data, mapping, 0x27DEA0, 0x27DF3F - 0x27DEA0)
    require(
        hashlib.sha256(body).hexdigest()
        == "e2fbfe5196a1f059c2a40cf2ce37034f24e49c44156232f3e39628f2dd80d77d",
        "0x27dea0 body changed",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x27BC40))
        == 0x27DEA0,
        "mono conversion call changed",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x27DECF))
        == 0x1CD40,
        "pixel-conversion selector changed",
    )
    return digest


def verify_run(run_dir: Path) -> dict:
    report = json.loads((run_dir / "report.json").read_text(encoding="ascii"))
    require(not report["errors"], f"{run_dir}: {report['errors']}")
    require(report["terminated_after_capture"], f"{run_dir}: incomplete capture")
    packet = report["packet"]
    require(packet["camera_key"] == 1, f"{run_dir}: camera key")
    source_path = Path(packet["source_path"])
    output_path = Path(packet["output_path"])
    require(
        hashlib.sha256(source_path.read_bytes()).hexdigest() == packet["source_sha256"],
        f"{run_dir}: source SHA",
    )
    require(
        hashlib.sha256(output_path.read_bytes()).hexdigest() == packet["output_sha256"],
        f"{run_dir}: output SHA",
    )
    source = np.fromfile(source_path, dtype="<f4")
    output = np.fromfile(output_path, dtype="<f4").reshape(-1, 4)
    require(source.size == output.shape[0], f"{run_dir}: pixel count")
    source_bits = source.view("<u4")
    output_bits = output.view("<u4")
    lane_matches = [int(np.count_nonzero(output_bits[:, lane] == source_bits)) for lane in range(4)]
    one_bits = np.float32(1.0).view("<u4")
    one_matches = [int(np.count_nonzero(output_bits[:, lane] == one_bits)) for lane in range(4)]
    pixels = int(source.size)
    require(lane_matches[:3] == [pixels, pixels, pixels], f"{run_dir}: RGB replication")
    require(one_matches[3] == pixels, f"{run_dir}: alpha fill")
    return {
        "run": run_dir.name,
        "pixels": pixels,
        "lane_matches_source": lane_matches,
        "lane_matches_one": one_matches,
        "source_sha256": packet["source_sha256"],
        "output_sha256": packet["output_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dirs", nargs="*", type=Path)
    args = parser.parse_args()
    digest = verify_static()
    print(f"static_create_stereo_mono_replication=OK libcp={digest}")
    for run_dir in (args.run_dirs or DEFAULT_RUNS):
        print(
            "create_stereo_mono_replication=OK "
            + json.dumps(verify_run(run_dir), sort_keys=True)
        )


if __name__ == "__main__":
    main()
