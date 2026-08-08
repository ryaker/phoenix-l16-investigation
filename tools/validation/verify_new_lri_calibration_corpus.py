#!/usr/bin/env python3
"""Verify the two recovered calibration packages and adjacent LRI corpus.

This is a static, read-only verifier. It distinguishes complete photographs
from calibration-only LELR containers and recovered/truncated files, then
joins package calibration payloads to the payloads embedded in photographs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


DEFAULT_NEW_ROOT = Path("/Volumes/Base Photos/New LRI")
DEFAULT_REFERENCE_ROOT = Path("/Volumes/Base Photos/Light")
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
KNOWN_UNITS = {
    "722a6e721636c9c4": "canonical Unit-1",
    "223961c6bce6153e": "canonical Unit-2",
}
CAMERA_NAMES = (
    "A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3",
    "B4", "B5", "C1", "C2", "C3", "C4", "C5", "C6",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fields(blob: bytes) -> list[tuple[int, int, object]]:
    return list(parse_proto_fields(blob))


def values(blob: bytes, number: int, wire: int | None = None) -> list[object]:
    return [
        value for field, field_wire, value in fields(blob)
        if field == number and (wire is None or field_wire == wire)
    ]


def first(blob: bytes, number: int, wire: int | None = None) -> object | None:
    found = values(blob, number, wire)
    return found[0] if found else None


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def f32_word(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word))[0]


def signed32(value: int) -> int:
    return value - (1 << 32) if value & (1 << 31) else value


def device_key(payload: bytes) -> str:
    low = first(payload, 6, 0)
    high = first(payload, 7, 0)
    require(isinstance(low, int) and isinstance(high, int), "missing device UUID words")
    return f"{high:016x}{low:016x}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def complete(path: Path, blocks: list[dict]) -> bool:
    return bool(blocks) and sum(block["total_size"] for block in blocks) == path.stat().st_size


def block_bytes(path: Path, block: dict) -> bytes:
    with path.open("rb") as handle:
        handle.seek(block["block_offset"])
        data = handle.read(block["total_size"])
    require(len(data) == block["total_size"], f"{path}: truncated block {block['idx']}")
    return data


def calibration_role(payload: bytes) -> str | None:
    top = fields(payload)
    calibrations = [value for number, wire, value in top if number == 13 and wire == 2]
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
    sensor_messages = [
        value for number, wire, value in top
        if number == 16 and wire == 2 and isinstance(value, bytes)
    ]
    if any(
        isinstance(first(sensor, 1, 0), int)
        and isinstance(first(sensor, 2, 2), bytes)
        for sensor in sensor_messages
    ):
        return "sensor_characterization"
    if any(number == 14 and wire == 2 for number, wire, _value in top):
        return "device_calibration"
    return None


def calibration_payloads(blocks: list[dict]) -> dict[str, dict]:
    result = {}
    for block in blocks:
        role = calibration_role(block["payload"])
        if role:
            result.setdefault(role, {
                "index": block["idx"],
                "payload_size": block["payload_size"],
                "payload_sha256": sha256(block["payload"]),
            })
    return result


def sensor_characterization(payload: bytes) -> dict | None:
    sensor = next(
        (
            value for number, wire, value in fields(payload)
            if number == 16 and wire == 2 and isinstance(value, bytes)
            and isinstance(first(value, 1, 0), int)
            and isinstance(first(value, 2, 2), bytes)
        ),
        None,
    )
    if sensor is None:
        return None
    data = first(sensor, 2, 2)
    require(isinstance(data, bytes), "sensor characterization missing data")
    rows = []
    for model in values(data, 4, 2):
        require(isinstance(model, bytes), "invalid VST model")
        row = {
            "gain": first(model, 1, 0),
            "threshold_word": first(model, 2, 5),
            "scale_word": first(model, 3, 5),
        }
        for field_number, name in ((4, "red"), (5, "green"), (6, "blue"), (7, "panchromatic")):
            channel = first(model, field_number, 2)
            row[name] = {
                "a_word": first(channel, 1, 5) if isinstance(channel, bytes) else None,
                "b_word": first(channel, 2, 5) if isinstance(channel, bytes) else None,
            }
        rows.append(row)
    semantic_blob = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "sensor_type": first(sensor, 1, 0),
        "black_level_word": first(data, 1, 5),
        "white_level_word": first(data, 2, 5),
        "cliff_slope_word": first(data, 3, 5),
        "vst_model_count": len(rows),
        "vst_gain_keys": [row["gain"] for row in rows],
        "vst_rows_sha256": sha256(semantic_blob),
    }


def modules(blocks: list[dict]) -> list[bytes]:
    return [
        module
        for block in blocks
        for module in values(block["payload"], 12, 2)
        if isinstance(module, bytes)
    ]


def photograph_row(path: Path, blocks: list[dict]) -> dict | None:
    module_messages = modules(blocks)
    if not module_messages:
        return None
    ids = sorted(
        int(camera_id)
        for module in module_messages
        if isinstance((camera_id := first(module, 2, 0)), int) and 0 <= camera_id < 16
    )
    top_payloads = [block["payload"] for block in blocks]
    image_id_low = next(
        (value for payload in top_payloads if isinstance((value := first(payload, 1, 0)), int)),
        None,
    )
    image_id_high = next(
        (value for payload in top_payloads if isinstance((value := first(payload, 2, 0)), int)),
        None,
    )
    focal = next(
        (value for payload in top_payloads if isinstance((value := first(payload, 4, 0)), int)),
        None,
    )
    reference = next(
        (value for payload in top_payloads if isinstance((value := first(payload, 5, 0)), int)),
        None,
    )
    firmware_blob = next(
        (value for payload in top_payloads if isinstance((value := first(payload, 9, 2)), bytes)),
        None,
    )
    cal = calibration_payloads(blocks)
    sensor_block = next(
        (block for block in blocks if calibration_role(block["payload"]) == "sensor_characterization"),
        None,
    )
    sensor_semantics = (
        sensor_characterization(sensor_block["payload"])
        if sensor_block is not None else None
    )
    geometry = cal.get("geometry")
    unit_signature = geometry["payload_sha256"][:16] if geometry else None
    dpc = Counter()
    for module in module_messages:
        explicit = first(module, 16, 0)
        dpc["default_true" if explicit is None else str(bool(explicit)).lower()] += 1
    nested_calibration_fields = Counter()
    for block in blocks:
        for calibration in values(block["payload"], 13, 2):
            if isinstance(calibration, bytes):
                nested_calibration_fields.update(number for number, _wire, _value in fields(calibration))
    return {
        "path": str(path),
        "image_key": (
            f"{image_id_high:016x}{image_id_low:016x}"
            if image_id_low is not None and image_id_high is not None else None
        ),
        "focal": focal,
        "reference_camera": reference,
        "firing_ids": ids,
        "firing_names": [CAMERA_NAMES[camera_id] for camera_id in ids],
        "firmware": firmware_blob.decode("utf-8", "replace") if firmware_blob else None,
        "unit_signature": unit_signature,
        "unit_identity": KNOWN_UNITS.get(unit_signature, "unknown"),
        "sensor_dpc_on": dict(sorted(dpc.items())),
        "factory_module_field_presence": {
            str(number): count for number, count in sorted(nested_calibration_fields.items())
        },
        "calibration_payloads": cal,
        "sensor_characterization": sensor_semantics,
    }


def load_schema_helper():
    path = (
        ROOT / "tools/lldb_probes/prefusion_node_dest_sentinel_custody/"
        "verify_embedded_calibration_proto_schema.py"
    )
    spec = importlib.util.spec_from_file_location("new_lri_schema_helper", path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hotpixel_schema() -> dict:
    helper = load_schema_helper()
    data = LIBCP.read_bytes()
    descriptors = helper.locate_all_descriptors(data)
    descriptor = next(item for item in descriptors if item["name"] == "hot_pixel_map.proto")
    return {
        "descriptor_sha256": descriptor["serialized_sha256"],
        "messages": descriptor["messages"],
    }


def hotpixel_package(path: Path) -> dict:
    blocks = scan_lri_blocks(str(path))
    require(len(blocks) == 1 and complete(path, blocks), f"{path}: invalid HotPixel LELR")
    block = blocks[0]
    records = values(block["payload"], 13, 2)
    require(len(records) == 16, f"{path}: expected 16 module records")
    camera_rows = []
    with path.open("rb") as handle:
        file_data = handle.read()
    for record in records:
        require(isinstance(record, bytes), f"{path}: nonbytes module record")
        camera_id = first(record, 1, 0)
        hotmap = first(record, 5, 2)
        require(isinstance(camera_id, int) and isinstance(hotmap, bytes),
                f"{path}: malformed hot-pixel module record")
        measurements = []
        for measurement in values(hotmap, 1, 2):
            require(isinstance(measurement, bytes), f"{path}: malformed HotPixelMeasurement")
            data_offset = first(measurement, 1, 0)
            data_size = first(measurement, 2, 0)
            exposure = first(measurement, 3, 0)
            temperature = first(measurement, 4, 0)
            gain_word = first(measurement, 5, 5)
            variance_word = first(measurement, 6, 5)
            threshold_word = first(measurement, 7, 5)
            require(all(isinstance(value, int) for value in (
                data_offset, data_size, exposure, temperature, gain_word
            )), f"{path}: incomplete HotPixelMeasurement")
            end = data_offset + data_size
            require(32 <= data_offset < end <= block["msg_offset"],
                    f"{path}: HotPixelMeasurement data range outside body")
            blob = file_data[data_offset:end]
            require(len(blob) >= 20, f"{path}: HotPixelMeasurement body too short")
            body_tag, body_reserved, compressed_size, width, height = struct.unpack(
                "<5I", blob[:20]
            )
            require(body_reserved == 0, f"{path}: nonzero HotPixel body reserved word")
            require(compressed_size == len(blob) - 20,
                    f"{path}: HotPixel compressed-size mismatch")
            require((width, height) == (4160, 3120), f"{path}: unexpected HotPixel dimensions")
            decoded = zlib.decompress(blob[20:])
            require(len(decoded) == width * height,
                    f"{path}: unexpected HotPixel decoded size {len(decoded)}")
            nonzero_pixels = sum(value != 0 for value in decoded)
            min_pixel = min(decoded)
            max_pixel = max(decoded)
            measurements.append({
                "data_offset": data_offset,
                "data_size": data_size,
                "data_sha256": sha256(blob),
                "data_prefix_hex": blob[:16].hex(),
                "body_tag_hex": f"0x{body_tag:08x}",
                "compressed_size": compressed_size,
                "width": width,
                "height": height,
                "decoded_size": len(decoded),
                "decoded_sha256": sha256(decoded),
                "decoded_nonzero_u8": nonzero_pixels,
                "decoded_min_u8": min_pixel,
                "decoded_max_u8": max_pixel,
                "data_exposure": exposure,
                "sensor_temparature": signed32(temperature & 0xFFFFFFFF),
                "sensor_gain": f32_word(gain_word),
                "pixel_variance": f32_word(variance_word) if isinstance(variance_word, int) else None,
                "threshold": f32_word(threshold_word) if isinstance(threshold_word, int) else None,
            })
        camera_rows.append({
            "camera_id": camera_id,
            "camera_name": CAMERA_NAMES[camera_id],
            "hot_pixel_map_size": len(hotmap),
            "hot_pixel_map_sha256": sha256(hotmap),
            "hot_pixel_map_fields": [number for number, _wire, _value in fields(hotmap)],
            "measurements": measurements,
        })
    return {
        "path": str(path),
        "file_size": path.stat().st_size,
        "file_sha256": file_sha256(path),
        "message_offset": block["msg_offset"],
        "payload_size": block["payload_size"],
        "payload_sha256": sha256(block["payload"]),
        "pre_message_body_size": block["msg_offset"] - 32,
        "camera_rows": camera_rows,
    }


def package_row(directory: Path) -> dict:
    calibration = directory / "calibration.lri"
    blocks = scan_lri_blocks(str(calibration))
    require(len(blocks) == 5 and complete(calibration, blocks),
            f"{calibration}: expected complete five-block package")
    roles = calibration_payloads(blocks)
    require(set(roles) == {
        "geometry", "vignetting", "sensor_characterization", "color", "device_calibration"
    }, f"{calibration}: unexpected roles {roles}")
    rec_matches = {}
    for filename, block_index in (("crosstalkcamparams.rec", 1), ("colorcamparams.rec", 3)):
        rec_path = directory / filename
        rec_matches[filename] = block_bytes(calibration, blocks[block_index]) == rec_path.read_bytes()
        require(rec_matches[filename], f"{rec_path}: not exact calibration block {block_index}")
    unit_signature = roles["geometry"]["payload_sha256"][:16]
    return {
        "directory_label": directory.name,
        "calibration_path": str(calibration),
        "calibration_file_sha256": file_sha256(calibration),
        "unit_signature": unit_signature,
        "unit_identity": KNOWN_UNITS.get(unit_signature, "unknown"),
        "device_key": device_key(blocks[0]["payload"]),
        "payloads": roles,
        "exact_rec_block_matches": rec_matches,
        "hotpixel": hotpixel_package(directory / "hotpixel.rec"),
    }


def geometry_by_camera(payload: bytes) -> dict[int, bytes]:
    result = {}
    for record in values(payload, 13, 2):
        require(isinstance(record, bytes), "nonbytes FactoryModuleCalibration")
        camera_id = first(record, 1, 0)
        geometry = first(record, 3, 2)
        require(isinstance(camera_id, int) and isinstance(geometry, bytes),
                "malformed geometry calibration record")
        result[camera_id] = geometry
    return result


def geometry_without_distortion(geometry: bytes) -> list[tuple[int, int, object]]:
    return [item for item in fields(geometry) if item[0] != 3]


def geometry_field_matches(left: bytes, right: bytes) -> dict[str, bool]:
    left_fields: dict[int, list[tuple[int, object]]] = defaultdict(list)
    right_fields: dict[int, list[tuple[int, object]]] = defaultdict(list)
    for number, wire, value in fields(left):
        left_fields[number].append((wire, value))
    for number, wire, value in fields(right):
        right_fields[number].append((wire, value))
    return {
        str(number): left_fields[number] == right_fields[number]
        for number in sorted(set(left_fields) | set(right_fields))
        if number != 3
    }


def zoom_rows(root: Path, packages: list[dict]) -> list[dict]:
    package_by_device = {row["device_key"]: row for row in packages}
    rows = []
    for path in sorted(root.glob("**/zoom_calib_v0*.lri")):
        blocks = scan_lri_blocks(str(path))
        require(len(blocks) == 1 and complete(path, blocks), f"{path}: invalid zoom calibration")
        payload = blocks[0]["payload"]
        module_records = values(payload, 13, 2)
        key = device_key(payload)
        package = package_by_device.get(key)
        require(package is not None, f"{path}: no matching package UUID")
        package_blocks = scan_lri_blocks(package["calibration_path"])
        package_geometry = geometry_by_camera(package_blocks[0]["payload"])
        zoom_geometry = geometry_by_camera(payload)
        projection_matches = {
            str(camera_id): geometry_without_distortion(zoom_geometry[camera_id])
            == geometry_without_distortion(package_geometry[camera_id])
            for camera_id in sorted(package_geometry)
        }
        field_matches = {
            str(camera_id): geometry_field_matches(
                zoom_geometry[camera_id], package_geometry[camera_id]
            )
            for camera_id in sorted(package_geometry)
        }
        require(all(any(number == 3 for number, _wire, _value in fields(item))
                    for item in package_geometry.values()), f"{path}: package distortion missing")
        require(all(not any(number == 3 for number, _wire, _value in fields(item))
                    for item in zoom_geometry.values()), f"{path}: zoom distortion unexpectedly present")
        rows.append({
            "path": str(path),
            "file_size": path.stat().st_size,
            "file_sha256": file_sha256(path),
            "payload_size": len(payload),
            "payload_sha256": sha256(payload),
            "device_key": key,
            "matched_package_label": package["directory_label"],
            "matched_unit_signature": package["unit_signature"],
            "module_record_count": len(module_records),
            "module_camera_ids": [first(record, 1, 0) for record in module_records],
            "exact_package_geometry_without_distortion": projection_matches,
            "package_geometry_field_matches_without_distortion": field_matches,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-root", type=Path, default=DEFAULT_NEW_ROOT)
    parser.add_argument("--reference-root", type=Path, default=DEFAULT_REFERENCE_ROOT)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    paths = sorted(args.new_root.glob("**/*.lri"))
    photographs = []
    incomplete = []
    calibration_only = []
    for path in paths:
        blocks = scan_lri_blocks(str(path))
        if not complete(path, blocks):
            incomplete.append(str(path))
            continue
        row = photograph_row(path, blocks)
        if row is None:
            calibration_only.append(str(path))
        else:
            photographs.append(row)

    require(len(photographs) == 81, f"expected 81 complete photographs, got {len(photographs)}")
    require(len(incomplete) == 1, f"expected one incomplete LRI, got {len(incomplete)}")
    package_rows = [package_row(args.new_root / "Unit 1"), package_row(args.new_root / "Unit 2")]
    package_by_sig = {row["unit_signature"]: row for row in package_rows}
    require(set(package_by_sig) == set(KNOWN_UNITS), f"unexpected package signatures {package_by_sig}")

    photo_counts = Counter(row["unit_signature"] for row in photographs)
    require(set(photo_counts) == set(KNOWN_UNITS), f"unexpected photo signatures {photo_counts}")
    payload_sets: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    payload_counts: Counter = Counter()
    payload_firmware_counts: Counter = Counter()
    sensor_semantic_counts: Counter = Counter()
    expected_gains = list(range(100, 800, 25))
    for row in photographs:
        sensor = row["sensor_characterization"]
        require(sensor is not None, f"{row['path']}: missing SensorCharacterization")
        require(sensor["sensor_type"] == 2, f"{row['path']}: unexpected sensor type")
        require(f32_word(sensor["black_level_word"]) == 42.0, f"{row['path']}: black level")
        require(f32_word(sensor["white_level_word"]) == 1023.0, f"{row['path']}: white level")
        require(f32_word(sensor["cliff_slope_word"]) == 2.0, f"{row['path']}: cliff slope")
        require(sensor["vst_model_count"] == 28, f"{row['path']}: VST row count")
        require(sensor["vst_gain_keys"] == expected_gains, f"{row['path']}: VST gains")
        sensor_semantic_counts[
            (row["unit_signature"], row["firmware"], sensor["vst_rows_sha256"])
        ] += 1
        for role, payload in row["calibration_payloads"].items():
            digest = payload["payload_sha256"]
            payload_sets[row["unit_signature"]][role].add(digest)
            payload_counts[(row["unit_signature"], role, digest)] += 1
            payload_firmware_counts[(row["unit_signature"], row["firmware"], role, digest)] += 1
    package_photo_matches = {}
    for signature, package in package_by_sig.items():
        role_matches = {}
        for role, payload in package["payloads"].items():
            observed = payload_sets[signature][role]
            role_matches[role] = {
                "package_digest_present_in_photos": payload["payload_sha256"] in observed,
                "observed_photo_variant_count": len(observed),
                "observed_photo_digests": sorted(observed),
            }
            require(role_matches[role]["package_digest_present_in_photos"],
                    f"{signature} {role}: package digest absent from photos {observed}")
        package_photo_matches[signature] = role_matches

    dpc_counts = Counter()
    hotmap_photo_records = 0
    deadmap_photo_records = 0
    for row in photographs:
        dpc_counts.update(row["sensor_dpc_on"])
        hotmap_photo_records += int(row["factory_module_field_presence"].get("5", 0))
        deadmap_photo_records += int(row["factory_module_field_presence"].get("6", 0))
    require(hotmap_photo_records == 0, "complete photographs unexpectedly embed HotPixelMap")
    require(deadmap_photo_records == 0, "complete photographs unexpectedly embed DeadPixelMap")

    focal_routes = Counter(
        (row["focal"], row["reference_camera"], tuple(row["firing_names"])) for row in photographs
    )

    reference_image_paths: dict[str, list[str]] = defaultdict(list)
    reference_sensor_counts: Counter = Counter()
    reference_sensor_semantic_counts: Counter = Counter()
    reference_complete_photographs = 0
    for path in sorted(args.reference_root.glob("**/*.lri")):
        blocks = scan_lri_blocks(str(path))
        if not complete(path, blocks):
            continue
        row = photograph_row(path, blocks)
        if row is None:
            continue
        reference_complete_photographs += 1
        if row["image_key"]:
            reference_image_paths[row["image_key"]].append(row["path"])
        sensor = row["calibration_payloads"].get("sensor_characterization")
        if sensor:
            reference_sensor_counts[
                (row["unit_signature"], row["firmware"], sensor["payload_sha256"])
            ] += 1
        semantics = row["sensor_characterization"]
        if semantics:
            reference_sensor_semantic_counts[
                (row["unit_signature"], row["firmware"], semantics["vst_rows_sha256"])
            ] += 1

    new_unique = [row["path"] for row in photographs if row["image_key"] not in reference_image_paths]
    relocated = {
        row["path"]: reference_image_paths[row["image_key"]]
        for row in photographs if row["image_key"] in reference_image_paths
    }
    report = {
        "new_root": str(args.new_root),
        "reference_root": str(args.reference_root),
        "complete_photograph_count": len(photographs),
        "incomplete_lri_paths": incomplete,
        "calibration_only_lri_paths": calibration_only,
        "photo_unit_counts": dict(sorted(photo_counts.items())),
        "focal_route_counts": {
            f"{focal}|ref={reference}|{','.join(firing)}": count
            for (focal, reference, firing), count in sorted(focal_routes.items())
        },
        "reference_complete_photograph_count": reference_complete_photographs,
        "new_unique_image_count": len(new_unique),
        "new_unique_image_paths": new_unique,
        "relocated_existing_image_count": len(relocated),
        "relocated_existing_image_paths": relocated,
        "reference_sensor_payload_counts": {
            f"{signature}|{firmware}|{digest}": count
            for (signature, firmware, digest), count in sorted(reference_sensor_counts.items())
        },
        "reference_sensor_semantic_counts": {
            f"{signature}|{firmware}|{digest}": count
            for (signature, firmware, digest), count
            in sorted(reference_sensor_semantic_counts.items())
        },
        "photo_sensor_semantic_counts": {
            f"{signature}|{firmware}|{digest}": count
            for (signature, firmware, digest), count in sorted(sensor_semantic_counts.items())
        },
        "photo_sensor_dpc_on_counts": dict(sorted(dpc_counts.items())),
        "photo_hot_pixel_map_record_count": hotmap_photo_records,
        "photo_dead_pixel_map_record_count": deadmap_photo_records,
        "packages": package_rows,
        "package_photo_payload_matches": package_photo_matches,
        "photo_calibration_payload_counts": {
            f"{signature}|{role}|{digest}": count
            for (signature, role, digest), count in sorted(payload_counts.items())
        },
        "photo_calibration_payload_firmware_counts": {
            f"{signature}|{firmware}|{role}|{digest}": count
            for (signature, firmware, role, digest), count
            in sorted(payload_firmware_counts.items())
        },
        "zoom_calibrations": zoom_rows(args.new_root, package_rows),
        "hot_pixel_schema": hotpixel_schema(),
        "photographs": photographs,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print("new_lri_calibration_packages=OK labels_reversed=true packages=2")
    print(f"new_lri_photographs=OK complete={len(photographs)} incomplete={len(incomplete)}")
    print(f"new_lri_photo_units=OK counts={dict(sorted(photo_counts.items()))}")
    print("new_lri_package_photo_payloads=OK roles=5 units=2")
    print(
        "new_lri_sensor_characterization=OK "
        f"semantic_variants={len(sensor_semantic_counts)} black=42 white=1023 cliff=2 rows=28"
    )
    print(
        "new_lri_hotpixel_boundary=OK "
        f"package_records=32 photo_records={hotmap_photo_records} sensor_dpc={dict(dpc_counts)}"
    )


if __name__ == "__main__":
    main()
