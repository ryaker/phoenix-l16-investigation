#!/usr/bin/env python3
"""Census public LightHeader firing sets across the local LRI corpus.

Only LELR headers and protobuf payloads are read. Raw sensor byte surfaces are
skipped through the block lengths, so this remains practical for the full
corpus while retaining a deterministic path-level exception register.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields  # noqa: E402


CAMERA_NAMES = [
    "A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3",
    "B4", "B5", "C1", "C2", "C3", "C4", "C5", "C6",
]
WIDE_SET = tuple(range(10))
TELE_SET = tuple(range(5, 16))


def fields(blob: bytes):
    return list(parse_proto_fields(blob))


def first_varint(parsed, number: int):
    return next((value for field, wire, value in parsed if field == number and wire == 0), None)


def first_bytes(parsed, number: int):
    return next((value for field, wire, value in parsed if field == number and wire == 2), None)


def f32_word(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def point2f(blob: bytes) -> list[float]:
    parsed = fields(blob)
    x = next(value for number, wire, value in parsed if number == 1 and wire == 5)
    y = next(value for number, wire, value in parsed if number == 2 and wire == 5)
    return [f32_word(x), f32_word(y)]


def preference_update(blob: bytes, current: dict) -> None:
    for number, wire, value in fields(blob):
        if number == 9 and wire == 0:
            current["orientation"] = value
        elif number == 14 and wire == 2:
            crop = fields(value)
            start = point2f(first_bytes(crop, 1))
            size = point2f(first_bytes(crop, 2))
            current["crop"] = [
                start[0], start[1],
                f32_word(struct.unpack("<I", struct.pack("<f", start[0] + size[0]))[0]),
                f32_word(struct.unpack("<I", struct.pack("<f", start[1] + size[1]))[0]),
            ]


def walk_payloads(path: Path):
    file_size = path.stat().st_size
    with path.open("rb") as stream:
        offset = 0
        index = 0
        while offset < file_size:
            stream.seek(offset)
            header = stream.read(32)
            if len(header) != 32 or header[:4] != b"LELR":
                break
            total_size = struct.unpack_from("<Q", header, 4)[0]
            message_offset = struct.unpack_from("<Q", header, 12)[0]
            message_size = struct.unpack_from("<I", header, 20)[0]
            message_type = header[24]
            if total_size < 32 or message_offset + message_size > total_size:
                break
            stream.seek(offset + message_offset)
            payload = stream.read(message_size)
            if len(payload) != message_size:
                break
            yield index, message_type, payload, total_size
            offset += total_size
            index += 1
    return offset, file_size


def inspect_lri(path: Path) -> dict:
    module_ids = set()
    focal = None
    reference_camera = None
    model = None
    firmware = None
    asic_firmware = None
    intrinsics_signature = None
    preferences = {}
    block_count = 0
    consumed_size = 0

    iterator = walk_payloads(path)
    while True:
        try:
            _index, message_type, payload, total_size = next(iterator)
        except StopIteration as stop:
            if stop.value:
                consumed_size, _file_size = stop.value
            break
        block_count += 1
        consumed_size += total_size
        if message_type == 1:
            preference_update(payload, preferences)
            continue
        if message_type != 0:
            continue
        parsed = fields(payload)
        focal = first_varint(parsed, 4) if first_varint(parsed, 4) is not None else focal
        reference_camera = (
            first_varint(parsed, 5) if first_varint(parsed, 5) is not None else reference_camera
        )
        for number, wire, value in parsed:
            if number == 8 and wire == 2:
                model = value.decode("utf-8", "replace")
            elif number == 9 and wire == 2:
                firmware = value.decode("utf-8", "replace")
            elif number == 10 and wire == 2:
                asic_firmware = value.decode("utf-8", "replace")
            elif number == 12 and wire == 2:
                camera_id = first_varint(fields(value), 2)
                if isinstance(camera_id, int) and 0 <= camera_id < 16:
                    module_ids.add(camera_id)
            elif number == 19 and wire == 2:
                preference_update(value, preferences)

        calibration_records = [
            value for number, wire, value in parsed if number == 13 and wire == 2
        ]
        if len(calibration_records) == 16:
            digest = hashlib.sha256(payload).hexdigest()[:16]
            if intrinsics_signature is None or len(payload) < intrinsics_signature[0]:
                intrinsics_signature = (len(payload), digest)

    ids = tuple(sorted(module_ids))
    if ids == WIDE_SET:
        firing_class = "canonical_wide"
    elif ids == TELE_SET:
        firing_class = "canonical_tele"
    else:
        firing_class = "outlier"
    return {
        "path": str(path),
        "complete": block_count > 0 and consumed_size == path.stat().st_size,
        "file_size": path.stat().st_size,
        "block_count": block_count,
        "focal": focal,
        "reference_camera": reference_camera,
        "model": model,
        "firmware": firmware,
        "asic_firmware": asic_firmware,
        "unit_signature": intrinsics_signature[1] if intrinsics_signature else None,
        "firing_ids": list(ids),
        "firing_names": [CAMERA_NAMES[value] for value in ids],
        "firing_class": firing_class,
        "crop": preferences.get("crop"),
        "orientation": preferences.get("orientation"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", type=Path, default=Path("/Volumes/Base Photos/Light"))
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    paths = sorted(
        Path(value)
        for value in glob.glob(str(args.corpus_root / "**/*.lri"), recursive=True)
    )
    if args.limit:
        paths = paths[: args.limit]
    if not paths:
        raise AssertionError(f"no LRIs below {args.corpus_root}")

    rows = []
    failures = []
    for index, path in enumerate(paths, 1):
        try:
            rows.append(inspect_lri(path))
        except Exception as exc:
            failures.append({"path": str(path), "error": repr(exc)})
        if index % 500 == 0 and not args.quiet:
            print(f"LRI_FIRING_SET_PROGRESS {index}/{len(paths)}", flush=True)

    counts = Counter()
    focal_counts = Counter()
    unit_counts = Counter()
    firmware_counts = Counter()
    reference_counts = Counter()
    crop_counts = Counter()
    exceptional_rows = []
    exact_focal_exceptions = []
    focal_route_exceptions = []
    for row in rows:
        set_key = ",".join(row["firing_names"]) or "EMPTY"
        status = "complete" if row["complete"] else "incomplete"
        counts[(status, set_key)] += 1
        focal_counts[(status, str(row["focal"]), set_key)] += 1
        unit_counts[(status, str(row["unit_signature"]), set_key)] += 1
        firmware_counts[(status, str(row["firmware"]), str(row["asic_firmware"]), set_key)] += 1
        reference_counts[(status, str(row["reference_camera"]), set_key)] += 1
        crop_key = ",".join(format(value, ".9g") for value in row["crop"]) if row["crop"] else "None"
        crop_counts[(status, str(row["reference_camera"]), crop_key)] += 1
        expected = WIDE_SET if row["focal"] in (28, 35) else TELE_SET if row["focal"] in (70, 149, 150) else None
        route_expected = (
            WIDE_SET if isinstance(row["focal"], int) and row["focal"] < 70
            else TELE_SET if isinstance(row["focal"], int)
            else None
        )
        is_exception = row["firing_class"] == "outlier"
        if expected is not None and tuple(row["firing_ids"]) != expected:
            exact_focal_exceptions.append(row)
            is_exception = True
        if route_expected is not None and tuple(row["firing_ids"]) != route_expected:
            focal_route_exceptions.append(row)
            is_exception = True
        if is_exception:
            exceptional_rows.append(row)

    def encode(counter: Counter) -> dict:
        return {"|".join(key): value for key, value in sorted(counter.items())}

    report = {
        "status": "PASS" if not failures else "PARTIAL",
        "lri_count": len(paths),
        "decoded_count": len(rows),
        "failure_count": len(failures),
        "failures": failures,
        "complete_count": sum(row["complete"] for row in rows),
        "incomplete_count": sum(not row["complete"] for row in rows),
        "firing_set_counts": encode(counts),
        "focal_firing_set_counts": encode(focal_counts),
        "unit_firing_set_counts": encode(unit_counts),
        "firmware_firing_set_counts": encode(firmware_counts),
        "reference_firing_set_counts": encode(reference_counts),
        "reference_crop_counts": encode(crop_counts),
        "exception_count": len(exceptional_rows),
        "exceptions": exceptional_rows,
        "exact_focal_exception_count": len(exact_focal_exceptions),
        "exact_focal_exceptions": exact_focal_exceptions,
        "focal_route_exception_count": len(focal_route_exceptions),
        "focal_route_exceptions": focal_route_exceptions,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered)
    if not args.quiet:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
