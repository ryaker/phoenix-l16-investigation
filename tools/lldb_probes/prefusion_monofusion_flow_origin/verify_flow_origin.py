#!/usr/bin/env python3
"""Verify installed MonoFusion flow custody and one or more runtime reports."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("monofusion_flow_static", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


def call_target(data, mapping, address):
    raw = static.bytes_at(data, mapping, address, 5)
    require(raw[0] == 0xE8, f"0x{address:x}: not a direct call")
    return address + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify_static():
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == static.LIBCP_SHA256, f"libcp digest changed: {digest}")
    for address, target in (
        (0x1B25ED, 0x1991E0),
        (0x1B25FF, 0xF340),
        (0x1B3B61, 0x1A3C00),
        (0x1A481D, 0x1A2520),
    ):
        require(call_target(data, mapping, address) == target, f"call 0x{address:x} changed")
    use = static.bytes_at(data, mapping, 0x1A4713, 0x74)
    require(hashlib.sha256(use).hexdigest() == "c2ed9de527e6f259ccfcd9f9dfc15c4f47bc0eb9366c4c862e1c245f1a3077d1", "flow-use window changed")
    require(static.bytes_at(data, mapping, 0x1A477E, 9) == bytes.fromhex("0fbf04910fbf4c9102"), "flow is not packed signed int16 x/y")
    print(f"static_monofusion_flow_custody=OK libcp={digest}")


def verify_report(path):
    report = json.loads(path.read_text())
    require(not report["errors"], f"{path}: probe errors {report['errors']}")
    require(report["producer_entries"], f"{path}: no producer entry")
    require(report["producer_returns"], f"{path}: no producer return")
    require(report["vector_copies"], f"{path}: no vector copy")
    require(report["worker_entries"], f"{path}: no worker entry")
    require(report["flow_uses"], f"{path}: no live flow reads")
    require(report["variant_hits"], f"{path}: no flow-kernel specialization hit")
    produced = report["producer_returns"][0]
    worker = report["worker_entries"][0]["flow_records"][0]
    copied = report["vector_copies"][0]
    for name, item in (("produced", produced), ("worker", worker)):
        descriptor = item["output"] if name == "produced" else item["descriptor"]
        require(descriptor["size"] == [519, 389], f"{path}: {name} dimensions")
        require(item["flow"]["storage"] == "packed little-endian int16 dx, int16 dy", f"{path}: {name} storage")
    digest = produced["flow"]["sha256"]
    require(copied["source_flow"]["sha256"] == digest, f"{path}: producer/copy digest")
    require(worker["flow"]["sha256"] == digest, f"{path}: copy/worker digest")
    require(produced["flow"]["nonzero_pairs"] > 0, f"{path}: all-zero flow")
    for sample in report["flow_uses"]:
        require(sample["linear_index"] >= 0, f"{path}: negative flow index")
        require(len(sample["flow"]) == 2, f"{path}: incomplete flow pair")
    require(report["terminated_after_samples"], f"{path}: capture did not terminate deliberately")
    print(
        f"runtime_monofusion_flow={report['label']}=OK "
        f"sha256={digest} min={produced['flow']['min']} max={produced['flow']['max']} "
        f"nonzero={produced['flow']['nonzero_pairs']}/{produced['flow']['pair_count']}"
    )
    print(
        "runtime_flow_variants="
        + ",".join(sorted({sample["variant"] for sample in report["variant_hits"]}))
    )


def main():
    verify_static()
    require(len(sys.argv) > 1, "provide at least one report")
    for item in sys.argv[1:]:
        verify_report(Path(item))
    print("monofusion_flow_origin_verification=OK")


if __name__ == "__main__":
    main()
