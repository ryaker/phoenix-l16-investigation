#!/usr/bin/env python3
"""Census LELR record/schema coverage across the local LRI corpus."""

from __future__ import annotations

import argparse
import glob
import json
import struct
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


LIGHTHEADER_FIELDS = set(range(1, 21)) | set(range(22, 28))
VIEW_PREFERENCE_FIELDS = set(range(1, 8)) | set(range(9, 20))
GPS_FIELDS = set(range(1, 10))


def fields(blob):
    return list(parse_proto_fields(blob))


def f32(raw):
    return struct.unpack("<f", struct.pack("<I", raw))[0]


def classify_type0(payload, msg_offset):
    parsed = fields(payload)
    numbers = {number for number, _wire, _value in parsed}
    if msg_offset > 32 and any(number == 12 for number, _wire, _value in parsed):
        return "raw_sensor_chunk"
    calibrations = [
        value for number, wire, value in parsed if number == 13 and wire == 2
    ]
    nested = {
        number
        for calibration in calibrations
        for number, _wire, _value in fields(calibration)
    }
    if 3 in nested:
        return "geometry"
    if 4 in nested:
        return "vignetting"
    if 2 in nested:
        return "color"
    if 16 in numbers:
        return "sensor_characterization"
    if 14 in numbers:
        return "device_calibration"
    if 19 in numbers:
        return "wrapped_view_preferences"
    return "lightheader_fragment"


def preference_messages(block):
    parsed = fields(block["payload"])
    if block["msg_type"] == 1:
        yield parsed
    if block["msg_type"] == 0:
        for number, wire, value in parsed:
            if number == 19 and wire == 2:
                yield fields(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-root", type=Path, default=Path("/Volumes/Base Photos/Light")
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    paths = sorted(
        Path(item)
        for item in glob.glob(str(args.corpus_root / "**/*.lri"), recursive=True)
    )
    if not paths:
        raise AssertionError(f"no LRIs below {args.corpus_root}")

    record_types = Counter()
    record_sequences = Counter()
    role_sequences = Counter()
    complete_role_presence = Counter()
    complete_preference_presence = Counter()
    orientation_values = Counter()
    orientation_samples = {}
    orientation_focal_values = Counter()
    orientation_focal_samples = {}
    aspect_ratio_values = Counter()
    awb_mode_values = Counter()
    complete = 0
    incomplete = 0
    unknown_record_types = Counter()
    unknown_fields = Counter()
    parse_failures = []
    complete_missing_critical = []

    critical_roles = {
        "raw_sensor_chunk",
        "geometry",
        "vignetting",
        "sensor_characterization",
        "color",
    }
    for index, path in enumerate(paths, start=1):
        try:
            blocks = scan_lri_blocks(str(path))
            is_complete = (
                bool(blocks)
                and sum(block["total_size"] for block in blocks) == path.stat().st_size
            )
            complete += int(is_complete)
            incomplete += int(not is_complete)
            types = tuple(block["msg_type"] for block in blocks)
            record_sequences[types] += 1
            roles = []
            preference_fields = set()
            merged_orientation = None
            image_focal_length = None
            for block in blocks:
                record_type = block["msg_type"]
                record_types[record_type] += 1
                if record_type == 0:
                    parsed = fields(block["payload"])
                    for number, wire, value in parsed:
                        if number == 4 and wire == 0:
                            image_focal_length = value
                    extra = {number for number, _wire, _value in parsed} - LIGHTHEADER_FIELDS
                    if extra:
                        unknown_fields[("LightHeader", tuple(sorted(extra)))] += 1
                    roles.append(
                        classify_type0(block["payload"], block["msg_offset"])
                    )
                elif record_type == 1:
                    parsed = fields(block["payload"])
                    extra = (
                        {number for number, _wire, _value in parsed}
                        - VIEW_PREFERENCE_FIELDS
                    )
                    if extra:
                        unknown_fields[("ViewPreferences", tuple(sorted(extra)))] += 1
                    roles.append("standalone_view_preferences")
                elif record_type == 2:
                    parsed = fields(block["payload"])
                    extra = {number for number, _wire, _value in parsed} - GPS_FIELDS
                    if extra:
                        unknown_fields[("GPSData", tuple(sorted(extra)))] += 1
                    roles.append("standalone_gps_data")
                else:
                    unknown_record_types[record_type] += 1
                    roles.append(f"unknown_type_{record_type}")

                for preference in preference_messages(block):
                    for number, wire, value in preference:
                        preference_fields.add(number)
                        if number == 7 and wire == 0:
                            awb_mode_values[value] += 1
                        elif number == 9 and wire == 0:
                            merged_orientation = value
                        elif number == 13 and wire == 0:
                            aspect_ratio_values[value] += 1
                        elif number in (2, 10, 18) and wire == 5:
                            f32(value)

            role_sequences[tuple(roles)] += 1
            if is_complete:
                if merged_orientation is not None:
                    orientation_values[merged_orientation] += 1
                    orientation_samples.setdefault(
                        str(merged_orientation), str(path)
                    )
                    if image_focal_length is not None:
                        focal_key = f"{merged_orientation}:{image_focal_length}"
                        orientation_focal_values[focal_key] += 1
                        orientation_focal_samples.setdefault(focal_key, str(path))
                role_set = set(roles)
                for role in role_set:
                    complete_role_presence[role] += 1
                for number in preference_fields:
                    complete_preference_presence[number] += 1
                missing = sorted(critical_roles - role_set)
                if missing:
                    complete_missing_critical.append(
                        {"path": str(path), "missing": missing, "roles": roles}
                    )
        except Exception as exc:
            parse_failures.append({"path": str(path), "error": repr(exc)})
        if index % 1000 == 0:
            print(f"LRI_BLOCK_CONTRACT_PROGRESS {index}/{len(paths)}", flush=True)

    report = {
        "status": "PASS"
        if not unknown_record_types and not unknown_fields and not parse_failures
        else "PARTIAL",
        "lri_count": len(paths),
        "complete_count": complete,
        "incomplete_count": incomplete,
        "record_type_counts": {str(key): value for key, value in sorted(record_types.items())},
        "record_sequence_counts": {
            ",".join(map(str, key)): value
            for key, value in sorted(record_sequences.items())
        },
        "role_sequence_counts": {
            ",".join(key): value for key, value in sorted(role_sequences.items())
        },
        "complete_role_presence": dict(sorted(complete_role_presence.items())),
        "complete_preference_field_presence": {
            str(key): value for key, value in sorted(complete_preference_presence.items())
        },
        "orientation_values": {
            str(key): value for key, value in sorted(orientation_values.items())
        },
        "orientation_samples": dict(sorted(orientation_samples.items())),
        "orientation_focal_values": dict(sorted(orientation_focal_values.items())),
        "orientation_focal_samples": dict(sorted(orientation_focal_samples.items())),
        "aspect_ratio_values": {
            str(key): value for key, value in sorted(aspect_ratio_values.items())
        },
        "awb_mode_values": {
            str(key): value for key, value in sorted(awb_mode_values.items())
        },
        "unknown_record_types": {
            str(key): value for key, value in sorted(unknown_record_types.items())
        },
        "unknown_fields": {
            f"{message}:{','.join(map(str, numbers))}": count
            for (message, numbers), count in sorted(unknown_fields.items())
        },
        "parse_failure_count": len(parse_failures),
        "parse_failure_samples": parse_failures[:24],
        "complete_missing_critical_count": len(complete_missing_critical),
        "complete_missing_critical_samples": complete_missing_critical[:24],
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
