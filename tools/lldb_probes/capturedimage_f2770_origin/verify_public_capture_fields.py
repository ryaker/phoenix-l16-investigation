#!/usr/bin/env python3
"""Verify public CameraModule origins for direct CapturedImage fields."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
AUDIT_PATH = ROOT / "tools/lane_b_index5_public_meaning_audit.py"
EXPECTED_LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
UNIT2_LRIS = (
    Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
    Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
)
UNIT2_RUNTIME_LRI = UNIT2_LRIS[0]
UNIT2_RUNTIME_REPORT = (
    ROOT
    / "runs/capturedimage_f2770_origin/f2770_origin_unit2_28mm.json"
)
UNIT2_RUNTIME_HDR = (
    ROOT
    / "runs/capturedimage_f2770_origin/f2770_origin_unit2_28mm.hdr"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_audit_module():
    spec = importlib.util.spec_from_file_location("lane_b_audit", AUDIT_PATH)
    require(spec is not None and spec.loader is not None, "cannot load Lane B audit")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def disassemble() -> str:
    result = subprocess.run(
        [
            "arch",
            "-x86_64",
            "lldb",
            "--batch",
            str(LIBCP),
            "-o",
            "disassemble --start-address 0xf2770 --end-address 0xf2837",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.stdout


def public_modules(audit, lri_path: Path) -> dict[int, dict[int, int]]:
    modules: dict[int, dict[int, int]] = {}
    for block in audit.scan_lri_blocks(str(lri_path)):
        for module in audit.field_values(block["payload"], 12, wire_type=2):
            camera_id = audit.first_field(module, 2, wire_type=0)
            if not isinstance(camera_id, int) or not 0 <= camera_id <= 15:
                continue
            modules[camera_id] = {
                field_no: value
                for field_no, wire_type, value in audit.parse_fields(module)
                if wire_type in (0, 5) and isinstance(value, int)
            }
    return modules


def calibration_hash(audit, lri_path: Path) -> str:
    payloads = [
        block["payload"]
        for block in audit.scan_lri_blocks(str(lri_path))
        if block["payload_size"] == 32833
    ]
    require(len(payloads) == 1, f"{lri_path}: missing Unit-2 calibration payload")
    return hashlib.sha256(payloads[0]).hexdigest()


def verify_event(event: dict, modules: dict[int, dict[int, int]], label: str) -> None:
    source = event["input_fields"]
    captured = event["output_fields"]
    camera_id = captured["u32_0x60"]
    require(camera_id in modules, f"{label}/{camera_id}: missing public camera")
    module = modules[camera_id]
    require(source["u32_0x3c"] == module[7], f"{label}/{camera_id}: analog gain")
    require(captured["u32_0x40"] == module[7], f"{label}/{camera_id}: captured analog gain")
    require(source["ptr_0x40"] == module[8], f"{label}/{camera_id}: exposure")
    if "u64_0x38" in captured:
        require(captured["u64_0x38"] == module[8], f"{label}/{camera_id}: captured exposure")
    require(source["u32_0x50"] == module[14], f"{label}/{camera_id}: digital gain")
    if "u32_0x44" in captured:
        require(captured["u32_0x44"] == module[14], f"{label}/{camera_id}: captured digital gain")
    require(source["u32_0x10_flags"] & 0x800, f"{label}/{camera_id}: digital gain absent")
    require(source["u32_0x48"] * 2 == module[10], f"{label}/{camera_id}: temperature")
    require(
        captured["u32_0x104"] == source["u32_0x48"],
        f"{label}/{camera_id}: captured temperature",
    )


def main() -> None:
    require(
        hashlib.sha256(LIBCP.read_bytes()).hexdigest() == EXPECTED_LIBCP_SHA256,
        "installed libcp hash drift",
    )
    text = disassemble()
    needles = [
        "movq   0x40(%r14), %rax",
        "movq   %rax, 0x38(%rdx)",
        "movl   0x3c(%r14), %eax",
        "movl   %eax, 0x40(%rdx)",
        "testb  $0x8, %ch",
        "movl   0x50(%r14), %eax",
        "movl   %eax, 0x44(%rdx)",
        "movl   0x48(%r14), %eax",
        "movl   %eax, 0x104(%rdx)",
    ]
    missing = [needle for needle in needles if needle not in text]
    require(not missing, f"f2770 static copy anchors missing: {missing}")

    audit = load_audit_module()
    raw_values = {7: set(), 8: set(), 14: set()}
    event_count = 0
    for tier in audit.TIERS:
        packet_path = (
            ROOT
            / "runs/capturedimage_f2770_origin"
            / f"f2770_origin_{tier}.json"
        )
        packet = json.loads(packet_path.read_text())
        require(not packet.get("errors"), f"{tier}: constructor report has errors")
        modules = public_modules(audit, Path(audit.TIERS[tier]))
        for event in packet["events"]:
            verify_event(event, modules, tier)
            camera_id = event["output_fields"]["u32_0x60"]
            module = modules[camera_id]
            for field_no in raw_values:
                raw_values[field_no].add(module[field_no])
            event_count += 1

    require(event_count == 42, f"expected 42 constructor events, got {event_count}")
    require(len(raw_values[7]) >= 2, "sensor_analog_gain lacks discriminating values")
    require(len(raw_values[8]) >= 20, "sensor_exposure lacks discriminating values")
    require(len(raw_values[14]) >= 2, "sensor_digital_gain lacks discriminating values")

    unit2_counts = []
    for lri_path in UNIT2_LRIS:
        require(
            calibration_hash(audit, lri_path).startswith("223961c6bce6153e"),
            f"{lri_path}: Unit-2 calibration identity mismatch",
        )
        modules = public_modules(audit, lri_path)
        require(modules, f"{lri_path}: no public CameraModule records")
        require(
            all({7, 8, 10, 14} <= set(module) for module in modules.values()),
            f"{lri_path}: public source fields are incomplete",
        )
        unit2_counts.append(len(modules))

    unit2_packet = json.loads(UNIT2_RUNTIME_REPORT.read_text())
    require(not unit2_packet.get("errors"), "Unit-2 runtime constructor errors")
    require(unit2_packet["counts"] == {"pre": 10, "post": 10}, "Unit-2 paired counts")
    require(len(unit2_packet["events"]) == 10, "Unit-2 event count")
    require(
        UNIT2_RUNTIME_HDR.read_bytes().startswith(b"#?RADIANCE"),
        "Unit-2 output is not populated Radiance HDR",
    )
    unit2_runtime_modules = public_modules(audit, UNIT2_RUNTIME_LRI)
    unit2_runtime_keys = set()
    for event in unit2_packet["events"]:
        verify_event(event, unit2_runtime_modules, "unit2_28mm")
        unit2_runtime_keys.add(event["output_fields"]["u32_0x60"])
    require(
        unit2_runtime_keys == set(unit2_runtime_modules),
        "Unit-2 runtime/public camera-key coverage mismatch",
    )

    print(
        "capturedimage_public_capture_fields=OK "
        f"libcp={EXPECTED_LIBCP_SHA256} events={event_count} "
        f"field7_values={len(raw_values[7])} "
        f"field8_values={len(raw_values[8])} "
        f"field14_values={len(raw_values[14])} "
        f"unit2_modules={','.join(map(str, unit2_counts))} "
        f"unit2_runtime_events={len(unit2_packet['events'])} "
        f"unit2_runtime_keys={','.join(map(str, sorted(unit2_runtime_keys)))}"
    )


if __name__ == "__main__":
    main()
