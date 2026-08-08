#!/usr/bin/env python3
"""Cross-unit static verifier for Lane B public LRI carrier paths.

This verifier is deliberately render-free. It checks that the public carrier
paths used by the index-5 public-meaning audit are present with the same schema
on the canonical Unit-1 seeds and on exact-focal Unit-2 representatives.

It does not validate runtime index-5 custody on Unit-2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import lane_b_index5_public_meaning_audit as audit


UNIT1_SIG = "722a6e721636c9c4"
UNIT2_SIG = "223961c6bce6153e"

WIDE_FIRED = list(range(0, 10))
TELE_FIRED = list(range(5, 16))

EXACT_FOCAL_SEEDS = [
    {
        "role": "Unit-1 canonical",
        "tier": "28mm",
        "path": "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
        "unit_sig": UNIT1_SIG,
        "focal": 28,
        "fired": WIDE_FIRED,
    },
    {
        "role": "Unit-1 canonical",
        "tier": "35mm",
        "path": "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri",
        "unit_sig": UNIT1_SIG,
        "focal": 35,
        "fired": WIDE_FIRED,
    },
    {
        "role": "Unit-1 canonical",
        "tier": "70mm",
        "path": "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
        "unit_sig": UNIT1_SIG,
        "focal": 70,
        "fired": TELE_FIRED,
    },
    {
        "role": "Unit-1 canonical",
        "tier": "150mm",
        "path": "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
        "unit_sig": UNIT1_SIG,
        "focal": 149,
        "fired": TELE_FIRED,
    },
    {
        "role": "Unit-2 exact-focal representative",
        "tier": "28mm",
        "path": "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri",
        "unit_sig": UNIT2_SIG,
        "focal": 28,
        "fired": WIDE_FIRED,
    },
    {
        "role": "Unit-2 exact-focal representative",
        "tier": "35mm",
        "path": "/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri",
        "unit_sig": UNIT2_SIG,
        "focal": 35,
        "fired": WIDE_FIRED,
    },
    {
        "role": "Unit-2 exact-focal representative",
        "tier": "70mm",
        "path": "/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri",
        "unit_sig": UNIT2_SIG,
        "focal": 70,
        "fired": TELE_FIRED,
    },
    {
        "role": "Unit-2 exact-focal representative",
        "tier": "150mm",
        "path": "/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri",
        "unit_sig": UNIT2_SIG,
        "focal": 149,
        "fired": TELE_FIRED,
    },
]

SAME_NAME_SCOPE_CHECKS = [
    {
        "label": "Unit-2 same-name L16_03041 candidate",
        "path": "/Volumes/Base Photos/Light/2018-10-28/L16_03041.lri",
        "unit_sig": UNIT2_SIG,
        "actual_focal": 74,
        "actual_fired": TELE_FIRED,
        "scope_note": "same-name candidate is not an exact 35mm focal representative",
    },
    {
        "label": "Unit-2 same-name L16_03434 candidate",
        "path": "/Volumes/Base Photos/Light/2020-07-14/L16_03434.lri",
        "unit_sig": UNIT2_SIG,
        "actual_focal": 149,
        "actual_fired": TELE_FIRED,
        "scope_note": "same-name candidate is not an exact 70mm focal representative",
    },
]

REQUIRED_MODULE_FIELDS = {2, 3, 5, 8, 10, 15, 16}
OPTIONAL_MODULE_FIELDS = {4}
PRESENT_VALUES = {4160, 3120}
ABSENT_COMPUTED_VALUES = {2080, 1560, 10432, 7824, 8896, 6672, 4096, 1040, 520, 390}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def camera_names(camera_ids: list[int]) -> list[str]:
    return [audit.CAMERA_NAMES[camera_id] for camera_id in camera_ids]


def blocks_with_sixteen_field13(blocks: list[dict]) -> list[dict]:
    return [
        block for block in blocks
        if len(audit.field_values(block["payload"], 13, wire_type=2)) == 16
    ]


def intrinsics_block(blocks: list[dict]) -> dict:
    candidates = blocks_with_sixteen_field13(blocks)
    require(candidates, "no 16-record field_13 block found")
    return min(candidates, key=lambda block: block["payload_size"])


def warp_block(blocks: list[dict]) -> dict:
    candidates = [
        block for block in blocks_with_sixteen_field13(blocks)
        if block["payload_size"] > 200000
    ]
    require(len(candidates) == 1, f"expected one large warp field_13 block, got {len(candidates)}")
    return candidates[0]


def module_roi_is_4160x3120(module: bytes) -> bool:
    for field9 in audit.field_values(module, 9, wire_type=2):
        for field2 in audit.field_values(field9, 2, wire_type=2):
            width = audit.first_field(field2, 1, wire_type=0)
            height = audit.first_field(field2, 2, wire_type=0)
            if width == 4160 and height == 3120:
                return True
    return False


def collect_modules(blocks: list[dict]) -> dict[int, dict]:
    modules: dict[int, dict] = {}
    for block in blocks:
        for module in audit.field_values(block["payload"], 12, wire_type=2):
            camera_id = audit.first_field(module, 2, wire_type=0)
            if not isinstance(camera_id, int) or not 0 <= camera_id <= 15:
                continue
            fields = {
                field_no: value
                for field_no, wire_type, value in audit.parse_fields(module)
                if wire_type == 0 and isinstance(value, int)
            }
            modules[camera_id] = {
                "fields": fields,
                "roi_4160x3120": module_roi_is_4160x3120(module),
            }
    return modules


def validate_modules(blocks: list[dict], expected_fired: list[int], label: str) -> dict:
    modules = collect_modules(blocks)
    fired = sorted(modules)
    require(fired == expected_fired, f"{label}: fired cameras {fired} != {expected_fired}")
    for camera_id, module in modules.items():
        fields = module["fields"]
        missing = REQUIRED_MODULE_FIELDS - set(fields)
        require(not missing, f"{label}: camera {camera_id} missing module fields {sorted(missing)}")
        require(fields[2] == camera_id, f"{label}: camera {camera_id} field_2 is not camera id")
        require(module["roi_4160x3120"], f"{label}: camera {camera_id} missing CameraModule.f9.f2 ROI")
    field_presence = {
        str(camera_id): sorted(set(module["fields"]) & (REQUIRED_MODULE_FIELDS | OPTIONAL_MODULE_FIELDS))
        for camera_id, module in modules.items()
    }
    return {
        "fired_camera_ids": fired,
        "fired_camera_names": camera_names(fired),
        "field_presence": field_presence,
        "roi_path": "LightHeader.field_12[].field_9.field_2.field_1/field_2 = 4160/3120",
    }


def validate_intrinsics(blocks: list[dict], expected_sig: str, label: str) -> dict:
    block = intrinsics_block(blocks)
    entries = audit.field_values(block["payload"], 13, wire_type=2)
    camera_ids = [audit.first_field(entry, 1, wire_type=0) for entry in entries]
    require(camera_ids == list(range(16)), f"{label}: intrinsics camera ids {camera_ids}")
    distinct = len({hashlib.sha256(entry).hexdigest() for entry in entries})
    require(distinct == 16, f"{label}: intrinsics field_13 records are not pairwise distinct")
    digest = hashlib.sha256(block["payload"]).hexdigest()[:16]
    require(digest == expected_sig, f"{label}: unit signature {digest} != {expected_sig}")
    return {
        "block_index": block["index"],
        "payload_size": block["payload_size"],
        "sha256_16": digest,
        "field_13_count": len(entries),
        "distinct_field_13_records": distinct,
        "camera_ids": camera_ids,
    }


def validate_warp(blocks: list[dict], label: str) -> dict:
    block = warp_block(blocks)
    entries = audit.field_values(block["payload"], 13, wire_type=2)
    nominals: dict[int, list[int]] = {}
    for entry in entries:
        camera_id = audit.first_field(entry, 1, wire_type=0)
        mapping = audit.first_field(entry, 4, wire_type=2)
        require(isinstance(camera_id, int), f"{label}: warp entry missing camera id")
        require(isinstance(mapping, bytes), f"{label}: warp camera {camera_id} missing field_4 mapping")
        values = []
        for config in audit.field_values(mapping, 2, wire_type=2):
            nominal = audit.first_field(config, 1, wire_type=0)
            if isinstance(nominal, int):
                values.append(nominal)
        nominals[camera_id] = values
    require(sorted(nominals) == list(range(16)), f"{label}: warp camera ids mismatch")
    invalid = {
        camera_id: len(values)
        for camera_id, values in nominals.items()
        if len(values) not in {1, 4}
    }
    require(not invalid, f"{label}: unexpected nominal counts {invalid}")
    fixed = sorted(camera_id for camera_id, values in nominals.items() if len(values) == 1)
    four = sorted(camera_id for camera_id, values in nominals.items() if len(values) == 4)
    require(fixed and four, f"{label}: nominal table did not expose both one- and four-entry groups")
    return {
        "block_index": block["index"],
        "payload_size": block["payload_size"],
        "sha256_16": hashlib.sha256(block["payload"]).hexdigest()[:16],
        "field_13_count": len(entries),
        "one_nominal_cameras": camera_names(fixed),
        "four_nominal_cameras": camera_names(four),
    }


def validate_proto_value_scope(blocks: list[dict], label: str) -> dict:
    values: set[int] = set()
    for block in blocks:
        values |= audit.walk_proto_values(block["payload"])
    require(PRESENT_VALUES <= values, f"{label}: missing public ROI values")
    unexpected = sorted(ABSENT_COMPUTED_VALUES & values)
    require(not unexpected, f"{label}: computed dimensions are stored as proto values {unexpected}")
    return {
        "present_values": sorted(PRESENT_VALUES),
        "absent_computed_values": sorted(ABSENT_COMPUTED_VALUES),
    }


def validate_seed(seed: dict) -> dict:
    label = f"{seed['role']} {seed['tier']}"
    path = Path(seed["path"])
    require(path.exists(), f"{label}: missing LRI {path}")
    blocks = audit.scan_lri_blocks(str(path))
    require(blocks, f"{label}: no LRI blocks parsed")
    focal = audit.first_field(blocks[0]["payload"], 4, wire_type=0)
    require(focal == seed["focal"], f"{label}: focal {focal} != {seed['focal']}")
    return {
        "label": label,
        "path": str(path),
        "focal": focal,
        "block_count": len(blocks),
        "modules": validate_modules(blocks, seed["fired"], label),
        "intrinsics": validate_intrinsics(blocks, seed["unit_sig"], label),
        "warp": validate_warp(blocks, label),
        "proto_values": validate_proto_value_scope(blocks, label),
    }


def validate_same_name_scope(check: dict) -> dict:
    label = check["label"]
    path = Path(check["path"])
    require(path.exists(), f"{label}: missing LRI {path}")
    blocks = audit.scan_lri_blocks(str(path))
    focal = audit.first_field(blocks[0]["payload"], 4, wire_type=0)
    require(focal == check["actual_focal"], f"{label}: focal {focal} != {check['actual_focal']}")
    modules = validate_modules(blocks, check["actual_fired"], label)
    intr = validate_intrinsics(blocks, check["unit_sig"], label)
    return {
        "label": label,
        "path": str(path),
        "actual_focal": focal,
        "actual_fired_camera_names": modules["fired_camera_names"],
        "unit_signature": intr["sha256_16"],
        "scope_note": check["scope_note"],
    }


def build_report() -> dict:
    exact = [validate_seed(seed) for seed in EXACT_FOCAL_SEEDS]
    same_name = [validate_same_name_scope(check) for check in SAME_NAME_SCOPE_CHECKS]
    return {
        "status": "OK",
        "scope": (
            "static public LRI carrier schema only; no Unit-2 runtime "
            "index-5 or merge-path custody is admitted"
        ),
        "exact_focal_seed_count": len(exact),
        "exact_focal_seeds": exact,
        "same_name_scope_checks": same_name,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, help="optional path for a JSON report")
    args = parser.parse_args()

    report = build_report()
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(
        "OK cross-unit public carriers: "
        f"{report['exact_focal_seed_count']} exact-focal seeds; "
        "Unit-1 canonical + Unit-2 exact-focal representatives"
    )
    for row in report["exact_focal_seeds"]:
        modules = row["modules"]
        intr = row["intrinsics"]
        warp = row["warp"]
        print(
            f"{row['label']}: focal={row['focal']} "
            f"fired={','.join(modules['fired_camera_names'])} "
            f"intrinsics={intr['payload_size']}B/{intr['sha256_16']} "
            f"warp={warp['payload_size']}B/{warp['sha256_16']}"
        )
    for row in report["same_name_scope_checks"]:
        print(
            f"scope {row['label']}: actual_focal={row['actual_focal']} "
            f"fired={','.join(row['actual_fired_camera_names'])}; "
            f"{row['scope_note']}"
        )


if __name__ == "__main__":
    main()
