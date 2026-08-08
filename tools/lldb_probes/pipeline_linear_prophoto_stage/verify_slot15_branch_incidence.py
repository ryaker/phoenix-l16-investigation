#!/usr/bin/env python3
"""Verify slot-15 branch sites and, when requested, runtime reports."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
RUNS = ROOT / "runs/pipeline_linear_prophoto_stage"
EXPECTED_CONFIG = bytes.fromhex(
    "6c344c3fb16f0a3e6c6c003d017a933e623d363fd6b9b338"
    "0000000000000000f640533f8dfbb03ed08cb73e0500000005000000"
)
EXPECTED_CONFIG_SHA256 = hashlib.sha256(EXPECTED_CONFIG).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("slot15_static_helper", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


RANGES = {
    (0x34A610, 0x34A6D7): "73ab2dfd7195441f39246835e010afaae3886e2405be2a82a272411ef37ffebe",
    (0x34A780, 0x34A847): "88511a8e6046e96a7aa52bff1fd8d8d02ec6b1605f0c7c0ddca43ee3badc5dd6",
    (0x34A8F0, 0x34A9B7): "4871a7188d7e3f7d6493ecb78b97df2761e2d758324267715cf344efa39b1219",
}

SITES = {
    0x34A6AD: ("Bayer", "equal_copy", "add", "rsp, 8"),
    0x34A6B4: ("Bayer", "unequal_convert", "call", "0x2d6cd0"),
    0x34A81D: ("BayerFloat", "equal_copy", "add", "rsp, 8"),
    0x34A824: ("BayerFloat", "unequal_convert", "call", "0x2d6cd0"),
    0x34A98D: ("Color", "equal_copy", "add", "rsp, 8"),
    0x34A994: ("Color", "unequal_convert", "call", "0x2d6cd0"),
}


def verify_static() -> None:
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    require(hashlib.sha256(data).hexdigest() == static.LIBCP_SHA256, "libcp digest changed")
    for (start, end), expected in RANGES.items():
        actual = hashlib.sha256(static.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"slot-15 wrapper changed at 0x{start:x}")
    for address, (_, _, mnemonic, operands) in SITES.items():
        item = static.instruction(data, mapping, address)
        require(item.mnemonic == mnemonic and item.op_str == operands,
                f"branch site changed at 0x{address:x}: {item.mnemonic} {item.op_str}")


def verify_report(name: str) -> tuple[int, int]:
    path = RUNS / f"slot15_{name}.json"
    require(path.is_file(), f"missing report {path}")
    report = json.loads(path.read_text())
    require(report.get("process_exit_status") == 0, f"{name}: render did not exit 0")
    require(not report.get("errors"), f"{name}: probe errors {report.get('errors')}")

    equal = 0
    unequal = 0
    for wrapper in ("Bayer", "BayerFloat", "Color"):
        counts = report["counts"][wrapper]
        equal += counts["equal_copy"]
        unequal += counts["unequal_convert"]
    require(equal + unequal > 0, f"{name}: no slot-15 branch hits")

    for key in report["config_counts"]:
        require(key.rsplit("|", 1)[-1] == EXPECTED_CONFIG_SHA256,
                f"{name}: unexpected current config {key}")

    for sample in report.get("samples", []):
        config = bytes.fromhex(sample["config_hex"])
        require(config == EXPECTED_CONFIG, f"{name}: sample config bytes differ")
        require(hashlib.sha256(config).hexdigest() == sample["config_sha256"],
                f"{name}: sample config digest mismatch")
        if sample["bit_exact_linear_prophoto_target"]:
            require(sample["outcome"] == "equal_copy",
                    f"{name}: target config unexpectedly converted")
        if sample["outcome"] == "equal_copy":
            require(sample["bit_exact_linear_prophoto_target"],
                    f"{name}: equal branch carried a different config")
    print(f"{name}: equal_copy={equal} unequal_convert={unequal} unique_configs={len(report['config_counts'])}")
    return equal, unequal


def verify_zero_report(name: str) -> None:
    path = RUNS / f"slot15_{name}.json"
    require(path.is_file(), f"missing report {path}")
    report = json.loads(path.read_text())
    require(report.get("process_exit_status") == 0, f"{name}: render did not exit 0")
    require(not report.get("errors"), f"{name}: probe errors {report.get('errors')}")
    require(set(report["breakpoints"]) == {
        "Bayer_unequal_convert", "BayerFloat_unequal_convert"
    }, f"{name}: zero report has wrong breakpoint set")
    unequal = sum(
        report["counts"][wrapper]["unequal_convert"]
        for wrapper in ("Bayer", "BayerFloat", "Color")
    )
    require(unequal == 0, f"{name}: observed {unequal} unequal conversions")
    print(f"{name}: completed mismatch-only census unequal_convert=0")


def verify_sample_report(name: str) -> None:
    path = RUNS / f"slot15_{name}_sample.json"
    require(path.is_file(), f"missing sample report {path}")
    report = json.loads(path.read_text())
    require(not report.get("errors"), f"{name}: sample probe errors {report.get('errors')}")
    samples = report.get("samples", [])
    require(samples, f"{name}: no positive equal-branch sample")
    for sample in samples:
        config = bytes.fromhex(sample["config_hex"])
        require(config == EXPECTED_CONFIG, f"{name}: sample config bytes differ")
        require(hashlib.sha256(config).hexdigest() == sample["config_sha256"],
                f"{name}: sample config digest mismatch")
        require(sample["outcome"] == "equal_copy", f"{name}: sample is not equal branch")
        require(sample["bit_exact_linear_prophoto_target"],
                f"{name}: equal sample is not exact target config")
    print(f"{name}: positive equal-branch samples={len(samples)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require", nargs="*", default=[])
    parser.add_argument("--require-zero", nargs="*", default=[])
    parser.add_argument("--require-sample", nargs="*", default=[])
    args = parser.parse_args()

    verify_static()
    print("slot15_branch_layout=OK sites=6 wrappers=Bayer,BayerFloat,Color")
    for name in args.require:
        verify_report(name)
    for name in args.require_zero:
        verify_zero_report(name)
    for name in args.require_sample:
        verify_sample_report(name)


if __name__ == "__main__":
    main()
