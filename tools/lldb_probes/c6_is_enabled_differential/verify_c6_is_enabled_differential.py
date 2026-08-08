#!/usr/bin/env python3
"""Verify C6 post-clear differential reports and compare completed HDR outputs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/c6_is_enabled_differential"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
PUBLIC_ORIGIN_VERIFIER = (
    ROOT
    / "tools/lldb_probes/prefusion_bayer_override_public_origin"
    / "verify_bayer_override_public_origin.py"
)
TIERS = ("70mm", "150mm")
CONDITIONS = ("baseline", "forced")
REPEATS = (1, 2)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("c6_differential_static_helpers", STATIC_PATH)


def verify_static() -> None:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    constructor = STATIC.bytes_at(data, mapping, 0x3E74E0, 0x3E77C8 - 0x3E74E0)
    require(
        hashlib.sha256(constructor).hexdigest()
        == "4d8fbc0477f7577e984229cf1a879b19ba35ac61640c6df22de13de81ce2cec9",
        "SourceImageCache constructor changed",
    )
    require(
        STATIC.cstring(data, mapping, 0x63543E)
        == b"Super-res does not support mono modules!",
        "mono-module rejection string changed",
    )
    byte_guards = {
        0x3E763C: "e81f6cffff",      # object accessor
        0x3E7644: "e807b1d0ff",      # f2750 -> item+0x58
        0x3E7649: "8b48040b080f88",  # OR x/y and branch on sign
        0x3E771D: "488d351add2400",  # rejection-string xref
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        require(
            STATIC.bytes_at(data, mapping, va, len(expected)) == expected,
            f"opcode drift at 0x{va:x}",
        )

    public_origin = subprocess.run(
        [sys.executable, str(PUBLIC_ORIGIN_VERIFIER)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    require(
        "bayer_override_public_origin=OK" in public_origin.stdout,
        "public bayer-override verifier failed",
    )
    print(f"static_c6_terminal_filter=OK libcp={digest}")


def mae(left: Path, right: Path) -> tuple[float, float]:
    result = subprocess.run(
        ["compare", "-metric", "MAE", str(left), str(right), "null:"],
        capture_output=True,
        text=True,
    )
    require(result.returncode in (0, 1), f"compare failed: {result.stderr}")
    match = re.search(r"([0-9.eE+-]+)\s+\(([0-9.eE+-]+)\)", result.stderr)
    require(match is not None, f"cannot parse MAE: {result.stderr!r}")
    return float(match.group(1)), float(match.group(2))


def verify_report(tier: str, condition: str, repeat: int) -> Path | None:
    stem = f"{tier}_{condition}_{repeat}"
    report_path = RUN_ROOT / f"{stem}.json"
    image_path = RUN_ROOT / f"{stem}.hdr"
    require(report_path.exists(), f"missing {report_path}")
    require(image_path.exists(), f"missing {image_path}")
    report = json.loads(report_path.read_text())
    require(not report["errors"], f"{stem}: errors {report['errors']}")
    require(report["key15_hits"] == 1, f"{stem}: key15 hits")
    require(len(report["transactions"]) == 1, f"{stem}: transactions")
    transaction = report["transactions"][0]
    require(transaction["key"] == 15, f"{stem}: key")
    require(transaction["active_before"] == 0, f"{stem}: clear not observed")
    expected = 1 if condition == "forced" else 0
    require(transaction["active_after"] == expected, f"{stem}: active after")
    if condition == "forced":
        require(transaction["write_count"] == 1, f"{stem}: write count")
        require(transaction["write_error"] is None, f"{stem}: write error")
        require(report["process_exit_status"] == 1, f"{stem}: forced process exit")
        require(image_path.stat().st_size == 0, f"{stem}: forced output is not empty")
        log = (RUN_ROOT / f"{stem}.log").read_text()
        require(
            "writeImage() failed: Super-res does not support mono modules!" in log,
            f"{stem}: missing mono rejection",
        )
        require("Written:" not in log, f"{stem}: forced run unexpectedly wrote output")
        return None

    require(report["process_exit_status"] == 0, f"{stem}: baseline process exit")
    require(image_path.stat().st_size > 0, f"{stem}: empty baseline output")
    log = (RUN_ROOT / f"{stem}.log").read_text()
    require("Written:" in log, f"{stem}: baseline missing output marker")
    return image_path


def main() -> None:
    verify_static()
    for tier in TIERS:
        images = {
            (condition, repeat): verify_report(tier, condition, repeat)
            for condition in CONDITIONS
            for repeat in REPEATS
        }
        baseline_1 = images[("baseline", 1)]
        baseline_2 = images[("baseline", 2)]
        require(baseline_1 is not None and baseline_2 is not None, f"{tier}: baseline paths")
        require(
            images[("forced", 1)] is None and images[("forced", 2)] is None,
            f"{tier}: forced paths",
        )
        within_baseline = mae(baseline_1, baseline_2)
        payload = {
            "tier": tier,
            "sha256": {
                f"baseline_{repeat}": sha256(images[("baseline", repeat)])
                for repeat in REPEATS
            },
            "within_baseline_mae": within_baseline,
            "forced_active": {
                "repeats": 2,
                "exit_status": 1,
                "output_bytes": 0,
                "error": "Super-res does not support mono modules!",
            },
        }
        (RUN_ROOT / f"{tier}_comparison.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(payload, sort_keys=True))
    print("c6_is_enabled_differential=OK")


if __name__ == "__main__":
    main()
