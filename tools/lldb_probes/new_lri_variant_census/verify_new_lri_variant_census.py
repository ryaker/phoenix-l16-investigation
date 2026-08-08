#!/usr/bin/env python3
"""Verify new intermediate-focal routes and HotPixel leakage exclusion."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/new_lri/variant_census"
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
HOTPIXEL_OPERATOR_SHA256 = "d6171d861a49366186401ed1f1c5360969576305c511ae669292c1dfd1999a14"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_static(stage) -> dict:
    digest = stage.verify_static()
    require(digest == LIBCP_SHA256, "stage verifier used unexpected libcp")
    data = LIBCP.read_bytes()
    body = data[0x3412F0:0x3416C5]
    require(hashlib.sha256(body).hexdigest() == HOTPIXEL_OPERATOR_SHA256,
            "HotPixel leakage operator body changed")
    mapping = stage.static.segments(data)
    require(stage.static.u64(stage.static.bytes_at(data, mapping, 0x65B378, 8)) == 0x3412F0,
            "HotPixel leakage callable vtable slot changed")
    decoded = {
        address: (instruction.mnemonic, instruction.op_str)
        for address in (0x341311, 0x341319, 0x341326, 0x34132B, 0x341444)
        for instruction in [stage.static.instruction(data, mapping, address)]
    }
    expected = {
        0x341311: ("cmp", "byte ptr [r15 + 0x90], 0"),
        0x341319: ("je", "0x341605"),
        0x341326: ("call", "0x10b1c0"),
        0x34132B: ("test", "al, al"),
        0x341444: ("call", "0x10acd0"),
    }
    require(decoded == expected, f"HotPixel guard/call instructions changed: {decoded}")
    require(b"no hp leakage calibration found!" in data, "missing no-calibration guard string")
    return {
        "libcp_sha256": digest,
        "operator_body_sha256": HOTPIXEL_OPERATOR_SHA256,
        "callable_vtable": "0x65b348",
        "operator": "0x3412f0",
        "correction_helper": "0x10acd0",
    }


def verify_pipeline(stage, filename: str, expected_family: str) -> dict:
    report = json.loads((RUN / filename).read_text())
    require(report["process"] == {"valid": True, "state": "exited", "exit_status": 0},
            f"{filename}: process did not exit cleanly")
    require(report["errors"] == [], f"{filename}: probe errors {report['errors']}")
    require(report["gate_hits"] == 1, f"{filename}: visible-src1 gate count")
    observed = stage.parse_targets(report)
    expected = stage.EXPECTED[expected_family]
    require(observed == expected, f"{filename}: target family changed")
    require(0x65B348 not in set().union(*observed.values()),
            f"{filename}: HotPixel leakage callable unexpectedly active")
    return {
        "expected_family": expected_family,
        "targets": {
            payload: [f"0x{vtable:x}->0x{stage.VTABLES[vtable][0]:x}"
                      for vtable in sorted(vtables)]
            for payload, vtables in observed.items()
        },
        "virtual_counts": report["virtual_counts"],
    }


def verify_hotpixel_report(filename: str) -> dict:
    report = json.loads((RUN / filename).read_text())
    require(report.get("process") == {"valid": True, "state": "exited", "exit_status": 0},
            f"{filename}: process did not exit cleanly: {report.get('process')}")
    require(report["counts"] and all(count == 0 for count in report["counts"].values()),
            f"{filename}: HotPixel leakage path became live: {report['counts']}")
    require(report["samples"] == [], f"{filename}: unexpected HotPixel samples")
    return {
        "label": report["label"],
        "process": report["process"],
        "counts": report["counts"],
    }


def main() -> None:
    stage = load_module(
        "new_lri_stage_verifier",
        ROOT / "tools/lldb_probes/src1_virtual_target_census/verify_pipeline_stage_order.py",
    )
    report = {
        "static": verify_static(stage),
        "pipeline_64mm": verify_pipeline(stage, "pipeline_64mm.json", "35mm"),
        "pipeline_71mm": verify_pipeline(stage, "pipeline_71mm.json", "70mm"),
        "hotpixel_64mm": verify_hotpixel_report("hotpixel_64mm.json"),
        "hotpixel_71mm": verify_hotpixel_report("hotpixel_71mm.json"),
        "hotpixel_old150": verify_hotpixel_report("hotpixel_old150.json"),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print("new_lri_variant_census=OK 64mm=wide 71mm=tele old150=complete")
    print("new_lri_hotpixel_leakage=ZERO_HITS runs=3")


if __name__ == "__main__":
    main()
