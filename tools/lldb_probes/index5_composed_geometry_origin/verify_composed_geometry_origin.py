#!/usr/bin/env python3
"""Verify public origins and field meaning of index-5 composed geometry records."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/index5_composed_geometry_origin"
AUDIT_PATH = ROOT / "tools/lane_b_index5_public_meaning_audit.py"
DISTORTION_PATH = (
    ROOT
    / "tools/lldb_probes/state_448_later_box_formula"
    / "verify_distortion_public_origin.py"
)
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)

CASES = {
    "28mm": {
        "path": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        "keys": [0, 4, 1, 2, 3],
        "constructed_keys": [0, 4, 6, 8, 9, 1, 2, 3, 5, 7],
        "anchor": 0,
        "unit": "722a6e721636c9c4",
    },
    "35mm": {
        "path": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
        "keys": [0, 4, 1, 2, 3],
        "constructed_keys": [0, 4, 6, 8, 9, 1, 2, 3, 5, 7],
        "anchor": 0,
        "unit": "722a6e721636c9c4",
    },
    "70mm": {
        "path": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
        "keys": [8, 6, 9, 5, 7],
        "constructed_keys": [6, 8, 9, 14, 5, 7, 11, 10, 12, 13, 15],
        "anchor": 8,
        "unit": "722a6e721636c9c4",
    },
    "150mm": {
        "path": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
        "keys": [8, 6, 9, 5, 7],
        "constructed_keys": [6, 8, 9, 14, 5, 7, 11, 10, 12, 13, 15],
        "anchor": 8,
        "unit": "722a6e721636c9c4",
    },
    "unit2_28mm": {
        "path": Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
        "keys": [0, 4, 1, 2, 3],
        "constructed_keys": [0, 4, 6, 8, 9, 1, 2, 3, 5, 7],
        "anchor": 0,
        "unit": "223961c6bce6153e",
    },
}

CAMERA_NAMES = {
    0: "A1",
    1: "A2",
    2: "A3",
    3: "A4",
    4: "A5",
    5: "B1",
    6: "B2",
    7: "B3",
    8: "B4",
    9: "B5",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_module("lane_b_audit_composed_geometry", AUDIT_PATH)
DISTORTION = load_module("distortion_origin_composed_geometry", DISTORTION_PATH)
STATIC = load_module("index5_static_composed_geometry", STATIC_PATH)
SCHEMA = DISTORTION.load_schema_module()


def raw_words(values: list[float]) -> list[int]:
    return [struct.unpack("<I", struct.pack("<f", float(value)))[0] for value in values]


def f32_from_word(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def public_modules(path: Path) -> dict[int, dict[int, int]]:
    modules: dict[int, dict[int, int]] = {}
    for block in AUDIT.scan_lri_blocks(str(path)):
        for module in AUDIT.field_values(block["payload"], 12, wire_type=2):
            camera_id = AUDIT.first_field(module, 2, wire_type=0)
            if not isinstance(camera_id, int) or not 0 <= camera_id <= 15:
                continue
            modules[camera_id] = {
                field_no: value
                for field_no, wire_type, value in AUDIT.parse_fields(module)
                if wire_type == 0 and isinstance(value, int)
            }
    return modules


def public_intrinsics(path: Path) -> tuple[dict[int, dict], str]:
    blocks = AUDIT.scan_lri_blocks(str(path))
    candidates = [
        block
        for block in blocks
        if len(AUDIT.field_values(block["payload"], 13, wire_type=2)) == 16
    ]
    require(candidates, f"{path}: no 16-record calibration block")
    block = min(candidates, key=lambda item: item["payload_size"])
    records: dict[int, dict] = {}
    for entry in AUDIT.field_values(block["payload"], 13, wire_type=2):
        camera_id = AUDIT.first_field(entry, 1, wire_type=0)
        body = AUDIT.first_field(entry, 3, wire_type=2)
        if not isinstance(camera_id, int) or not isinstance(body, bytes):
            continue
        try:
            bundles = AUDIT.field_values(body, 2, wire_type=2)
            pose = AUDIT._message_field(AUDIT._message_field(bundles[2], 3), 1)
            rotation = AUDIT._message_field(pose, 1)
            translation = AUDIT._message_field(pose, 2)
        except (AssertionError, IndexError):
            continue
        records[camera_id] = {
            "rotation": AUDIT._fixed32_values(rotation),
            "translation": AUDIT._fixed32_values(translation),
        }
    return records, hashlib.sha256(block["payload"]).hexdigest()[:16]


def verify_static() -> str:
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == STATIC.LIBCP_SHA256, f"libcp digest changed: {digest}")
    expected = {
        (0x264270, 0x2643C7): "acde803cf7789e4ccf0c61450feb6e83d827f7c95d2a4312724b0f35e22b2cda",
        (0x23FAF0, 0x2404CA): "7667ca96cf808086b007d521d7f06230b8d769e1692440023eea75a067a01cb7",
        (0x3FF050, 0x3FF46E): "8612d894a6acfd01573cf917f9ae756abe1075f6f7298ba5d44bb5d232bd9807",
        (0x28F5A0, 0x28F827): "c072ca497f377dcd393fd21ca41e4e645ec3d18cb4bbb890cdae3b7a8624b372",
    }
    for (start, end), wanted in expected.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == wanted, f"static range 0x{start:x}..0x{end:x} changed")
    constant = struct.unpack("<4f", STATIC.bytes_at(data, mapping, 0x5C51E0, 16))
    require(constant == (0.0, 0.0, 1.0, 1.0), "base adjustment tuple changed")
    require(
        STATIC.instruction(data, mapping, 0xE5970).op_str == "edi, 0x230",
        "CapturedImage shared allocation size changed",
    )
    require(
        STATIC.rip_target(STATIC.instruction(data, mapping, 0xE5985)) == 0x665EB8,
        "CapturedImage shared control-block vtable changed",
    )
    require(
        STATIC.instruction(data, mapping, 0xE5993).op_str == "rbx, 0x20",
        "CapturedImage object offset changed",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0xE59A4))
        == 0xF2770,
        "CapturedImage constructor call changed",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0xE59C5))
        == 0xE3240,
        "CapturedImage owner insertion call changed",
    )
    require(
        STATIC.instruction(data, mapping, 0xF27B0).op_str
        == "al, byte ptr [r14 + 0x60]",
        "CameraModule.is_enabled source copy changed",
    )
    require(
        STATIC.instruction(data, mapping, 0xF27B4).op_str
        == "byte ptr [rdx + 0x30], al",
        "CapturedImage.is_enabled destination copy changed",
    )
    require(
        STATIC.u64(STATIC.bytes_at(data, mapping, 0x665EB0, 8)) == 0x665EE0,
        "CapturedImage control-block typeinfo pointer changed",
    )
    require(
        STATIC.u64(STATIC.bytes_at(data, mapping, 0x665EE8, 8)) == 0x5AE680,
        "CapturedImage typeinfo-name pointer changed",
    )
    require(
        STATIC.cstring(data, mapping, 0x5AE680).decode("ascii")
        == "NSt3__120__shared_ptr_emplaceIN2lt13CapturedImageENS_9allocatorIS2_EEEE",
        "CapturedImage shared control-block RTTI changed",
    )
    return digest


def finite(values: list[float]) -> bool:
    return all(math.isfinite(value) for value in values)


def is_intrinsics_matrix(values: list[float]) -> bool:
    return (
        len(values) == 9
        and finite(values)
        and values[0] > 0
        and values[4] > 0
        and abs(values[1]) < 1e-6
        and abs(values[3]) < 1e-6
        and abs(values[6]) < 1e-6
        and abs(values[7]) < 1e-6
        and abs(values[8] - 1.0) < 1e-6
    )


def is_rotation(values: list[float], tolerance: float = 0.003) -> bool:
    if len(values) != 9 or not finite(values):
        return False
    rows = [values[index : index + 3] for index in (0, 3, 6)]
    for left in range(3):
        for right in range(3):
            dot = sum(rows[left][axis] * rows[right][axis] for axis in range(3))
            expected = 1.0 if left == right else 0.0
            if abs(dot - expected) > tolerance:
                return False
    return True


def source_point(record: dict) -> tuple[float, float, float]:
    translation = record["translation_0x24"]
    rotation = record["rotation_0x30"]
    rt = [
        sum(rotation[row * 3 + column] * translation[row] for row in range(3))
        for column in range(3)
    ]
    return rt[2], rt[1], rt[0]


def record_numeric_bytes(raw: bytes) -> bytes:
    return raw[0:0x64] + raw[0x80:0xA4]


def verify_case(label: str, config: dict) -> dict:
    report = json.loads((RUN_ROOT / f"composed_geometry_{label}.json").read_text())
    process = report["process"]
    require(process["state"] == "exited" and process["exit_status"] == 0, f"{label}: process")
    require(not report["errors"], f"{label}: errors {report['errors']}")
    require(not report["drive_hit_step_cap"], f"{label}: step cap")
    expected_counts = {
        "0xe59a9": len(config["constructed_keys"]),
        "0x3ff1bc": 5,
        "0x3ff1d6": 5,
        "0x3ff43c": 1,
    }
    require(report["counts"] == expected_counts, f"{label}: counts")
    require(report["breakpoint_hit_counts"] == expected_counts, f"{label}: breakpoint counts")
    hdr = RUN_ROOT / f"composed_geometry_{label}.hdr"
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{label}: output is not HDR")

    pre = [event["packet"] for event in report["events"] if event["site_name"] == "after_state_e0_record"]
    post = [event["packet"] for event in report["events"] if event["site_name"] == "after_23faf0_compose"]
    final = [event["packet"] for event in report["events"] if event["site_name"] == "before_stereolayer_install"]
    constructed = [
        event["packet"]
        for event in report["events"]
        if event["site_name"] == "after_capturedimage_construct"
    ]
    require(len(pre) == len(post) == 5 and len(final) == 1, f"{label}: event grouping")
    require(
        [packet["camera_id_0x60"] for packet in constructed]
        == config["constructed_keys"],
        f"{label}: CapturedImage construction keys",
    )
    require(
        all(
            packet["control_block_vtable_libcp_va"] == 0x665EB8
            for packet in constructed
        ),
        f"{label}: CapturedImage control-block RTTI",
    )
    constructed_objects = {
        packet["capturedimage_object"] for packet in constructed
    }
    require(
        constructed_objects == set(report["capturedimage_objects"]),
        f"{label}: CapturedImage object list",
    )
    require([packet["camera_key"] for packet in pre] == config["keys"], f"{label}: pre keys")
    require([packet["camera_key"] for packet in post] == config["keys"], f"{label}: post keys")

    public_pose, unit_signature = public_intrinsics(config["path"])
    require(unit_signature == config["unit"], f"{label}: unit signature {unit_signature}")
    public_poly, polynomial_signature = DISTORTION.public_polynomials(SCHEMA, config["path"])
    modules = public_modules(config["path"])
    anchor = public_pose[config["anchor"]]

    final_record_vector = final[0]["composed_geometry_vector"]
    require(final[0]["images_vector"]["byte_size"] == 5 * 0x10, f"{label}: Images bytes")
    require(final_record_vector["byte_size"] == 5 * 0xA8, f"{label}: record bytes")
    require(final[0]["image_flags_vector"]["byte_size"] == 5 * 4, f"{label}: flags bytes")
    final_raw = bytes.fromhex(final_record_vector["raw_hex"])

    points = []
    public_translation_matches = 0
    for index, (before, after) in enumerate(zip(pre, post)):
        key = config["keys"][index]
        require(before["camera_key"] == after["camera_key"] == key, f"{label}: key pair {index}")
        require(before["state_e0_object"] == after["state_e0_object"], f"{label}: object pair {key}")
        require(
            before["state_e0_object"] in constructed_objects,
            f"{label}: state+0xe0 object is not a constructed CapturedImage {key}",
        )
        require(
            before["state_448_node_record"]["raw_0x00_0xa4"]
            == after["state_448_node_record"]["raw_0x00_0xa4"],
            f"{label}: state+0x448 input changed for {key}",
        )
        require(
            before["state_e0_calibstage_record"]["raw_0x00_0xa4"]
            == after["state_e0_calibstage_record"]["raw_0x00_0xa4"],
            f"{label}: state+0xe0 input changed for {key}",
        )

        fields = after["state_e0_object_fields"]
        require(fields["active_0x30"] == 1, f"{label}: inactive camera {key}")
        require(fields["camera_id_0x60"] == key, f"{label}: object camera id {key}")
        require(fields["calib_stage_0x64"] == 0, f"{label}: object lookup stage {key}")
        require(fields["sensor_size_0x114"] == [4160, 3120], f"{label}: sensor size {key}")
        require(fields["lens_position_0x54"] == modules[key][5], f"{label}: lens position {key}")

        node = after["state_448_node_record"]
        require(raw_words(node["primary_matrix_0x00"]) == anchor["rotation"], f"{label}: anchor R {key}")
        require(raw_words(node["translation_0x24"]) == anchor["translation"], f"{label}: anchor t {key}")

        source = after["state_e0_calibstage_record"]
        require(is_intrinsics_matrix(source["primary_matrix_0x00"]), f"{label}: source K {key}")
        require(is_rotation(source["rotation_0x30"]), f"{label}: source R {key}")
        coeffs = source["distortion_coeffs_0x68"]
        require(coeffs["read_ok"], f"{label}: coefficient vector unreadable {key}")
        require(
            list(struct.unpack("<" + "I" * (coeffs["byte_size"] // 4), bytes.fromhex(coeffs["raw_hex"])))
            == public_poly[key]["coeff_words"],
            f"{label}: public distortion coeffs {key}",
        )
        center_norm = public_poly[key]["center_normalization_words"]
        center_x, center_y, norm_x, norm_y = map(f32_from_word, center_norm)
        expected_secondary = [norm_x, 0.0, center_x, 0.0, norm_y, center_y, 0.0, 0.0, 1.0]
        require(
            raw_words(source["secondary_matrix_0x80"]) == raw_words(expected_secondary),
            f"{label}: public distortion center/normalization matrix {key}",
        )

        output = after["compose_output_after"]
        require(is_intrinsics_matrix(output["primary_matrix_0x00"]), f"{label}: output K {key}")
        require(is_rotation(output["rotation_0x30"]), f"{label}: output R {key}")
        require(finite(output["adjustment_0x54"]), f"{label}: output adjustment {key}")
        require(output["adjustment_0x54"][2] > 0 and output["adjustment_0x54"][3] > 0, f"{label}: output scale {key}")
        output_coeffs = output["distortion_coeffs_0x68"]
        require(
            output_coeffs["raw_hex"] == coeffs["raw_hex"],
            f"{label}: composed distortion coefficients {key}",
        )

        appended = final_raw[index * 0xA8 : (index + 1) * 0xA8]
        output_raw = bytes.fromhex(output["raw_0x00_0xa4"])
        require(
            record_numeric_bytes(appended) == record_numeric_bytes(output_raw),
            f"{label}: composed output to +0x258 item {key}",
        )

        public_for_key = public_pose.get(key)
        if public_for_key and raw_words(output["translation_0x24"]) == public_for_key["translation"]:
            public_translation_matches += 1
        points.append(source_point(output))

    first_translation = post[0]["compose_output_after"]["translation_0x24"]
    require(max(abs(value) for value in first_translation) < 2e-5, f"{label}: anchor not zero")
    first = points[0]
    distances = [
        math.sqrt(sum((point[axis] - first[axis]) ** 2 for axis in range(3)))
        for point in points
    ]
    max_distance = max(distances)
    require(max_distance > 20.0, f"{label}: degenerate camera spread")
    if config["anchor"] == 0:
        require(public_translation_matches == 5, f"{label}: wide public translation matches")

    return {
        "keys": ",".join(CAMERA_NAMES[key] for key in config["keys"]),
        "anchor": CAMERA_NAMES[config["anchor"]],
        "capturedimage_count": len(constructed),
        "max_distance": max_distance,
        "unit_signature": unit_signature,
        "polynomial_signature": polynomial_signature[:16],
        "record_sha256": hashlib.sha256(final_raw).hexdigest(),
    }


def main() -> None:
    digest = verify_static()
    print(f"static_composed_geometry_origin=OK libcp={digest}")
    summaries = {}
    for label, config in CASES.items():
        summary = verify_case(label, config)
        summaries[label] = summary
        print(
            f"{label}: OK keys={summary['keys']} anchor={summary['anchor']} "
            f"state_e0_objects=lt::CapturedImage({summary['capturedimage_count']}) "
            f"max_camera_center_separation={summary['max_distance']:.6f} "
            f"unit={summary['unit_signature']} polynomial={summary['polynomial_signature']}"
        )
    require(
        summaries["28mm"]["record_sha256"] != summaries["unit2_28mm"]["record_sha256"],
        "Unit-1 and Unit-2 composed records unexpectedly identical",
    )
    require(
        summaries["28mm"]["unit_signature"] != summaries["unit2_28mm"]["unit_signature"],
        "Unit-1 and Unit-2 calibration signatures unexpectedly identical",
    )
    print("cross_body_28mm=OK distinct_calibration_and_composed_record_bytes")


if __name__ == "__main__":
    main()
