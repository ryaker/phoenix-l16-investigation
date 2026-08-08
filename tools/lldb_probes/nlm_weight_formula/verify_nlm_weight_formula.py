#!/usr/bin/env python3
"""Verify the installed PatchNLM<4> tent formula and one live operand packet."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "runs/nlm_weight_formula/unit1_28mm.json"
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("nlm_static_helper", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def verify_static():
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == static.LIBCP_SHA256, f"libcp digest changed: {digest}")
    hashes = {
        (0x3066D0, 0x306D40): "bfebe7619117a2db022e28894a2dbc2456fe8f2d255306939a508675d91b3da8",
        (0x3070E0, 0x307D90): "862f185f5d4cd3d365ebf5ff65091520b2697cdd9d83a1e8bf4c42a4b2a5ddbb",
        (0x307D90, 0x307EA7): "1415cf342baae4666c4a15d84d99acb004eff16de46a3c71dd042643de8d5cab",
        (0x307700, 0x307792): "3000be93c541a38911d36fe956ec1942cf3df4f7c2c2102fd4178ad181d7abbb",
        (0x3076AE, 0x3076CA): "102fa1ad109ef212616133f4d4e7fc86e5a7a79cd48f039980f52f807f714ee7",
        (0x2F57E7, 0x2F5826): "c8229b174916baad2cf67e523c1547519989d4e7ec89101125946fa52b90ada8",
        (0x2F5B03, 0x2F5B31): "b458de38366c215988c85239939cac082eee1b22b9e7cbbe76dec4fbaf94a3f6",
    }
    for (start, end), expected in hashes.items():
        actual = hashlib.sha256(static.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed: {actual}")
    constants = {
        0x5A81F0: struct.pack("<4I", *([0x7FFFFFFF] * 4)),
        0x5A8920: struct.pack("<4f", *([1.0] * 4)),
        0x5AB040: struct.pack("<4f", *([16.0] * 4)),
    }
    for va, expected in constants.items():
        require(static.bytes_at(data, mapping, va, 16) == expected, f"constant 0x{va:x} changed")
    # Pin the semantic opcodes inside the already SHA-pinned windows.
    formula = static.bytes_at(data, mapping, 0x30775B, 0x307792 - 0x30775B)
    for opcode in (b"\x0f\x5f", b"\xf3\x0f\x5f", b"\x0f\x5c", b"\x0f\x59"):
        require(opcode in formula, f"missing formula opcode {opcode.hex()}")
    normalize = static.bytes_at(data, mapping, 0x307E16, 0x307E82 - 0x307E16)
    require(normalize.count(b"\x0f\x53") == 3, "normalizer must use three unrefined rcpps sites")
    require(normalize.count(b"\x66\x0f\x3a\x0c") == 3, "normalizer alpha-preserve blend count changed")
    print(f"static_nlm_weight_formula=OK libcp={digest} patch_vec4_count=16 threshold_scale=16")


def verify_runtime():
    report = json.loads(REPORT.read_text())
    require(report["process"]["exit_status"] == 0, "instrumented render did not exit 0")
    require(not report["errors"], f"probe errors: {report['errors']}")
    require(len(report["samples"]) == 1, f"expected one paired sample: {len(report['samples'])}")
    sample = report["samples"][0]
    entry = report["entry"]
    require(entry is not None and entry["coefficient"] is not None, "missing parent coefficient packet")
    require(entry["search_divisor_r9d"] > 0, "invalid search divisor")
    require(entry["coefficient"][3] == entry["coefficient"][0], "coefficient endpoint lanes differ")
    require(entry["coefficient"][2] == entry["coefficient"][1], "coefficient middle lanes differ")
    distance = sample["distance_broadcast"]
    threshold = sample["threshold"]
    reciprocal = sample["threshold_rcpps"]
    weight = sample["weight"]
    require(all(math.isfinite(x) for x in distance[:3] + threshold[:3] + reciprocal[:3] + weight[:3]), "non-finite live RGB operand")
    require(max(distance) - min(distance) <= 1.0e-7, "distance was not broadcast")
    expected = []
    for d, v, r in zip(distance[:3], threshold[:3], reciprocal[:3]):
        expected.append(f32(max(0.0, f32(1.0 - f32(max(0.0, f32(d - v)) * r)))))
        require(abs(f32(v * r) - 1.0) < 5.0e-4, "rcpps packet outside expected approximation")
    delta = max(abs(a - b) for a, b in zip(expected, weight[:3]))
    require(delta <= 2.0e-6, f"live tent replay mismatch: {delta}")
    require(threshold[3] == 0.0 and math.isinf(reciprocal[3]) and weight[3] == 0.0, "lane-3 zero-weight policy changed")
    print(
        "runtime_nlm_weight_formula=OK "
        f"distance={distance[0]:.9g} threshold={threshold} reciprocal={reciprocal} weight={weight} delta={delta:.3g}"
    )


def main():
    verify_static()
    verify_runtime()
    print("nlm_weight_formula_verification=OK")


if __name__ == "__main__":
    main()
