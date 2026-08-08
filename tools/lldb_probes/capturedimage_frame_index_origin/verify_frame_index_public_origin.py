#!/usr/bin/env python3
"""Verify the public CameraModule.frame_index to RawImageFactory lookup chain."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
EXPECTED_LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
)
SCHEMA_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
AUDIT_PATH = ROOT / "tools/lane_b_index5_public_meaning_audit.py"
MULTIFRAME_SAMPLES = (
    (
        "Unit-1",
        Path("/Volumes/Base Photos/Light/2018-07-23/L16_02153.lri"),
        28,
        "722a6e721636c9c4",
        "c5796b9e960687ac14afc83d5e387964a834e502a28a1d9d8329f330fbae3136",
    ),
    (
        "Unit-2",
        Path("/Volumes/Base Photos/Light/2020-07-14/L16_03275.lri"),
        35,
        "223961c6bce6153e",
        "2c9401829b9b1b5ef7ca51d5df5fa48a2472ac6243a8e2486be4621cdd12086c",
    ),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_schema(schema, data: bytes) -> str:
    descriptor = schema.decode_file_descriptor(
        data, schema.locate_descriptor(data, "camera_module.proto")
    )
    fields = schema.field_map([descriptor])
    schema.require_field(fields, ".ltpb.CameraModule", 15, "frame_index", "uint32")
    return descriptor["serialized_sha256"]


def verify_static_chain(static, data: bytes) -> None:
    mapping = static.segments(data)
    expected_ops = {
        # CameraModule generated protobuf parser identity.
        0x163633: "eax, 0x10",  # field 2: id
        0x16369E: "eax, 0x20",  # field 4: mirror_position
        0x1636CD: "dword ptr [r12 + 0x34], eax",
        0x1636DB: "eax, 0x28",  # field 5: lens_position
        0x16370A: "dword ptr [r12 + 0x38], eax",
        0x163718: "eax, 0x3d",  # field 7: sensor_analog_gain
        0x163744: "dword ptr [r12 + 0x3c], ecx",
        0x163752: "eax, 0x40",  # field 8: sensor_exposure
        0x163779: "qword ptr [r12 + 0x40], rcx",
        0x1637BC: "eax, 0x50",  # field 10: sensor_temparature
        0x163B63: "dword ptr [r12 + 0x48], eax",
        0x1638AF: "eax, 0x75",  # field 14: sensor_digital_gain
        0x1638DB: "dword ptr [r12 + 0x50], ecx",
        # Field 15: frame_index.
        0x1638E9: "eax, 0x78",
        0x1638F2: "byte ptr [r12 + 0x11], 0x10",
        0x163913: "dword ptr [r12 + 0x54], esi",
        0x163BB3: "dword ptr [r12 + 0x54], eax",
        # CapturedImage constructor copy, guarded by the same 0x1000 has-bit.
        0xF27E3: "ch, 0x10",
        0xF27E8: "eax, dword ptr [r14 + 0x54]",
        0xF27EC: "dword ptr [rdx + 0x64], eax",
        # RawImageFactory selected-frame storage and lookup load.
        0x3C93D1: "edx, edx",
        0x1BD2B8: "dword ptr [r15 + 0x10], r14d",
        0x1BE983: "edx, dword ptr [rsi + 0x10]",
        # CapturedImage accessors used by the two-key CaptureStack scan.
        0xF2724: "eax, dword ptr [rdi + 0x60]",
        0xF3324: "eax, dword ptr [rdi + 0x64]",
    }
    for va, expected in expected_ops.items():
        actual = static.instruction(data, mapping, va).op_str
        require(actual == expected, f"0x{va:x}: {actual!r} != {expected!r}")

    expected_calls = {
        0x3C93D6: 0x1BDC70,
        0x1BE98B: 0xE6BA0,
        0xE6BD3: 0xF3320,
        0xE6BE0: 0xF2720,
    }
    for va, expected in expected_calls.items():
        actual = static.direct_call_target(static.instruction(data, mapping, va))
        require(actual == expected, f"0x{va:x}: call 0x{actual:x} != 0x{expected:x}")

    trampoline = static.instruction(data, mapping, 0x1BDC75)
    require(
        trampoline.mnemonic == "jmp"
        and len(trampoline.operands) == 1
        and trampoline.operands[0].imm == 0x1BD270,
        "RawImageFactory constructor trampoline changed",
    )


def public_capture(audit, path: Path) -> tuple[int, list[tuple[int, int]], str]:
    focal = None
    rows: list[tuple[int, int]] = []
    calibration_signature = None
    for block in audit.scan_lri_blocks(str(path)):
        payload = block["payload"]
        if focal is None:
            focal = audit.first_field(payload, 4, wire_type=0)
        for module in audit.field_values(payload, 12, wire_type=2):
            camera_id = audit.first_field(module, 2, wire_type=0)
            frame_index = audit.first_field(module, 15, wire_type=0)
            if isinstance(camera_id, int) and isinstance(frame_index, int):
                rows.append((camera_id, frame_index))
        if block["payload_size"] in (32832, 32833):
            calibration_signature = hashlib.sha256(payload).hexdigest()[:16]
    require(isinstance(focal, int), f"{path}: missing public focal length")
    require(calibration_signature is not None, f"{path}: missing calibration payload")
    return focal, rows, calibration_signature


def verify_multiframe_samples(audit) -> list[str]:
    labels = []
    expected_pairs = {(camera_id, frame_index) for camera_id in range(10) for frame_index in range(4)}
    for unit, path, expected_focal, expected_calibration, expected_sha in MULTIFRAME_SAMPLES:
        require(path.is_file(), f"missing multiframe sample: {path}")
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual_sha == expected_sha, f"{path}: file SHA-256 drift")
        focal, rows, calibration = public_capture(audit, path)
        require(focal == expected_focal, f"{path}: focal {focal} != {expected_focal}")
        require(calibration == expected_calibration, f"{path}: calibration body drift")
        require(len(rows) == 40, f"{path}: expected 40 CameraModule rows, got {len(rows)}")
        require(set(rows) == expected_pairs, f"{path}: incomplete camera/frame grid")
        labels.append(f"{unit}:{expected_focal}mm:{calibration}")
    return labels


def verify_existing_runtime() -> int:
    event_count = 0
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        path = (
            ROOT
            / "runs/capturedimage_f2770_origin"
            / f"f2770_origin_{tier}.json"
        )
        packet = json.loads(path.read_text())
        require(not packet.get("errors"), f"{tier}: constructor report errors")
        for event in packet["events"]:
            source = event["input_fields"]
            captured = event["output_fields"]
            require(source["u32_0x10_flags"] & 0x1000, f"{tier}: frame_index absent")
            require(source["u32_0x54"] == 0, f"{tier}: unexpected selected frame")
            require(captured["u32_0x64"] == 0, f"{tier}: CapturedImage frame mismatch")
            event_count += 1
    require(event_count == 42, f"expected 42 completed runtime events, got {event_count}")
    return event_count


def scan_corpus(audit, root: Path) -> tuple[int, dict[tuple[int, ...], int]]:
    scanned = 0
    value_sets: dict[tuple[int, ...], int] = {}
    for path in sorted(root.glob("*/*.lri")):
        values: set[int] = set()
        try:
            for block in audit.scan_lri_blocks(str(path)):
                for module in audit.field_values(block["payload"], 12, wire_type=2):
                    value = audit.first_field(module, 15, wire_type=0)
                    if isinstance(value, int):
                        values.add(value)
        except (OSError, ValueError):
            continue
        if values:
            scanned += 1
            key = tuple(sorted(values))
            value_sets[key] = value_sets.get(key, 0) + 1
    return scanned, value_sets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scan-corpus",
        type=Path,
        help="optionally census CameraModule.frame_index values under date-folder LRIs",
    )
    args = parser.parse_args()

    static = load_module("index5_static", STATIC_PATH)
    schema = load_module("embedded_schema", SCHEMA_PATH)
    audit = load_module("lane_b_audit", AUDIT_PATH)
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == EXPECTED_LIBCP_SHA256, "installed libcp SHA-256 drift")
    descriptor_sha = verify_schema(schema, data)
    verify_static_chain(static, data)
    samples = verify_multiframe_samples(audit)
    runtime_events = verify_existing_runtime()

    suffix = ""
    if args.scan_corpus:
        scanned, value_sets = scan_corpus(audit, args.scan_corpus)
        suffix = f" corpus_scanned={scanned} value_sets={value_sets}"

    print(
        "capturedimage_frame_index_public_origin=OK "
        f"libcp={digest} camera_module_proto={descriptor_sha[:16]} "
        f"samples={','.join(samples)} runtime_zero_events={runtime_events} "
        "chain=CameraModule.frame_index->protobuf+0x54->CapturedImage+0x64"
        "->RawImageFactory+0x10_lookup"
        f"{suffix}"
    )


if __name__ == "__main__":
    main()
