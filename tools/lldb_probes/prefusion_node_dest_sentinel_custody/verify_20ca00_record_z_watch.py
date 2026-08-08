#!/usr/bin/env python3
"""Validate the Unit-1 70mm 0x20ca00 record+0x10 watch report."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "runs" / "prefusion_20ca00_record_z_watch"
STEM = "record_z_watch_unit1_70mm"

ARM_SITE = 0x20D737
PARENT_SCAN_SITE = 0x20C3F9
SIBLING_PROPAGATION_SITE = 0x23A224
POSITIVE_RECORD_GATE_SITE = 0x2189C4
STATE_RECORD_TEST_SITE = 0x2295B7
HELPER_SITES = {0x23D1D3, 0x23D5ED, 0x23D887}
EXPECTED_TOP_COUNTS = {
    PARENT_SCAN_SITE: 1,
    SIBLING_PROPAGATION_SITE: 9,
    STATE_RECORD_TEST_SITE: 5,
    POSITIVE_RECORD_GATE_SITE: 37,
    0x23D1D3: 8,
    0x23D5ED: 2,
    0x23D887: 2,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report_path = RUN_DIR / f"{STEM}.json"
    log_path = RUN_DIR / f"{STEM}.log"
    hdr_path = RUN_DIR / f"{STEM}.hdr"

    report = json.loads(report_path.read_text())
    log = log_path.read_text(errors="replace")
    require("Process " in log and "launched" in log, "process launch missing")
    require("Written:" in log and "(10432x7824)" in log, "HDR write marker missing")
    require("Traceback" not in log, "callback traceback present")
    require("error:" not in log.lower(), "LLDB error present")
    require("lost connection" not in log.lower(), "debugserver connection lost")
    with hdr_path.open("rb") as handle:
        require(handle.read(10) == b"#?RADIANCE", "HDR output magic mismatch")

    require(report.get("process_exit_status") == 0, "report process exit not zero")
    require(report.get("drive_hit_step_cap") is False, "drive hit step cap")
    require(report.get("errors") == [], f"probe errors: {report.get('errors')}")

    armed = report.get("armed") or {}
    require(armed.get("stack", [{}])[0].get("libcp_va") == ARM_SITE, "arm stack top is not 0x20d737")
    require(armed.get("z_at_arm", {}).get("read_ok") is True, "armed z unreadable")
    require(armed.get("z_at_arm", {}).get("hex") == "deb55a45", "armed z hex drift")
    require(armed.get("z_at_arm", {}).get("value") == 3499.36669921875, "armed z value drift")
    require(armed.get("gate_index") == 3906, "armed gate index drift")
    require(armed.get("record_offset") == 19530, "armed record offset drift")
    require(armed.get("record_offset") == 5 * armed.get("gate_index"), "offset/gate formula mismatch")

    counts = report.get("counts") or {}
    samples = report.get("samples") or []
    require(counts.get("watchpoints_armed") == 1, "expected one watchpoint")
    require(counts.get("watchpoint_hits") == 64, "expected capped 64 watchpoint hits")
    require(counts.get("value_changes") == 0, "watched z changed")
    require(counts.get("value_unchanged") == 64, "unchanged count mismatch")
    require(len(samples) == 64, "sample count mismatch")

    armed_hex = armed["z_at_arm"]["hex"]
    top_counts = Counter(sample.get("libcp_va") for sample in samples)
    require(dict(top_counts) == EXPECTED_TOP_COUNTS, f"top VA counts drift: {top_counts}")
    for sample in samples:
        require(sample.get("changed") is False, f"sample {sample.get('ordinal')}: value changed")
        require(sample.get("z_now", {}).get("hex") == armed_hex, "watched z hex changed")
        require(sample.get("z_now", {}).get("value") == armed["z_at_arm"]["value"], "watched z value changed")

    first = samples[0]
    require(first.get("libcp_va") == PARENT_SCAN_SITE, "first watchpoint is not parent scan")
    require(first.get("stack", [])[1].get("libcp_va") == 0x22AE8C, "first sample State return drift")
    require(any(sample.get("libcp_va") == POSITIVE_RECORD_GATE_SITE for sample in samples), "missing 0x2189c4 downstream gate touch")
    require(any(sample.get("libcp_va") == SIBLING_PROPAGATION_SITE for sample in samples), "missing 0x23a224 propagation touch")
    require(any(sample.get("libcp_va") in HELPER_SITES for sample in samples), "missing 0x23c5f0 helper touch")

    print(f"report={report_path}")
    print(
        "armed="
        f"gate_index={armed['gate_index']} record_offset={armed['record_offset']} "
        f"z_addr=0x{armed['z_addr']:x} z={armed['z_at_arm']['value']:.9f}"
    )
    print(f"watchpoint_hits={len(samples)} value_changes={counts['value_changes']}")
    print("top_va_counts=" + ",".join(f"0x{va:x}:{count}" for va, count in sorted(top_counts.items())))
    print("first_touch=0x20c3f9 parent scan under State return 0x22ae8c")
    print("downstream_touch=0x2189c4 positive-record gate observed while z remained unchanged")
    print("scope=capped 64-hit Unit-1 70mm same-address record+0x10 watch; no terminality or image effect proven")


if __name__ == "__main__":
    main()
