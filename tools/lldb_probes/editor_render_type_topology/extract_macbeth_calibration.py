#!/usr/bin/env python3
"""Extract public ColorCalibration.macbeth_data from calibration LRIs."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


def first(fields: list[tuple[int, int, object]], number: int) -> object:
    return next(value for field, _, value in fields if field == number)


def point3f(payload: bytes) -> tuple[float, float, float]:
    values = {field: raw for field, wire, raw in parse_proto_fields(payload) if wire == 5}
    if set(values) != {1, 2, 3}:
        raise ValueError(f"Point3F fields are {sorted(values)}")
    return tuple(
        struct.unpack("<f", struct.pack("<I", values[field]))[0]
        for field in (1, 2, 3)
    )


def extract(path: Path, output_dir: Path, body: str) -> dict:
    blocks = scan_lri_blocks(str(path))
    candidates = []
    for block in blocks:
        fields = list(parse_proto_fields(block["payload"]))
        color_records = [
            item for item in fields if item[0] == 13 and item[1] == 2
        ]
        if len(color_records) == 42:
            candidates.append((block["idx"], fields))
    if len(candidates) != 1:
        raise ValueError(
            f"{path}: expected one 42-record color-calibration block, "
            f"got {len(candidates)}"
        )
    block_index, calibration_fields = candidates[0]
    records = []
    for module_field, module_wire, module_raw in calibration_fields:
        if module_field != 13 or module_wire != 2:
            continue
        module = list(parse_proto_fields(module_raw))
        camera_id = int(first(module, 1))
        color_payload = first(module, 2)
        color = list(parse_proto_fields(color_payload))
        illuminant_type = int(first(color, 1))
        points = [point3f(raw) for field, wire, raw in color if field == 6 and wire == 2]
        if len(points) != 24:
            raise ValueError(
                f"{path}: camera {camera_id} type {illuminant_type}: "
                f"expected 24 points, got {len(points)}"
            )
        raw = b"".join(struct.pack("<3f", *point) for point in points)
        name = f"camera_{camera_id:02d}_type_{illuminant_type}_macbeth_f32.raw"
        body_dir = output_dir / body
        body_dir.mkdir(parents=True, exist_ok=True)
        raw_path = body_dir / name
        raw_path.write_bytes(raw)
        records.append(
            {
                "camera_id": camera_id,
                "illuminant_type": illuminant_type,
                "macbeth_field": 6,
                "point_count": len(points),
                "raw_path": str(raw_path),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "has_spectral_data": any(field == 8 for field, _, _ in color),
                "points": points,
            }
        )
    records.sort(key=lambda item: (item["camera_id"], item["illuminant_type"]))
    if len(records) != 42:
        raise ValueError(f"{path}: expected 42 color records, got {len(records)}")
    return {
        "body": body,
        "calibration_lri": str(path),
        "calibration_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "calibration_block_index": block_index,
        "record_count": len(records),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit1", type=Path, required=True)
    parser.add_argument("--unit2", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "schema": {
            "message": "ltpb.ColorCalibration",
            "field": 6,
            "name": "macbeth_data",
            "type": "repeated ltpb.Point3F",
        },
        "bodies": [
            extract(args.unit1, args.output_dir, "unit1"),
            extract(args.unit2, args.output_dir, "unit2"),
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
