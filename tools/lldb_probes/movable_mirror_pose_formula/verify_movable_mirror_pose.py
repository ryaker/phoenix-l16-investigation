#!/usr/bin/env python3
"""Verify public movable-mirror calibration through Lumen's exact pose packet."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
SCHEMA = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
RUN_ROOT = ROOT / "runs/movable_mirror_pose_formula"
CASES = {
    "unit1_70mm": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
    "unit1_150mm": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
    "unit2_70mm": Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
}
RETAINED_CASES = {
    "unit1_28mm_retained": (
        Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        ROOT / "runs/codex_1f0ce0_k_source_trace/k_source_trace_28mm.json",
    ),
    "unit1_35mm_retained": (
        Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
        ROOT / "runs/codex_1f0ce0_k_source_trace/k_source_trace_35mm.json",
    ),
}
MOVABLE_KEYS = {5, 6, 7, 9, 10, 11, 12, 13}
EXPECTED_LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def instruction_at(data: bytes, address: int) -> tuple[str, str]:
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    item = next(decoder.disasm(data[address : address + 16], address), None)
    require(item is not None, f"cannot decode 0x{address:x}")
    return item.mnemonic, item.op_str


def verify_static_formula(data: bytes) -> None:
    expected = {
        # Constructor dispatch and public live-value handoff.
        0x1F1047: ("cmp", "dword ptr [rbx], 2"),
        0x1F1072: ("call", "0x1f0a00"),
        0x1F1095: ("cvtsi2sd", "xmm0, eax"),
        0x1F109C: ("call", "0x1c1860"),
        0x1F10B2: ("call", "0x1c79e0"),
        0x1C1865: ("jmp", "0x1ed4d0"),
        # Six coefficients become A(x), B(x), C(x), then the quadratic solver
        # returns the two roots in adjacent doubles.
        0x1ED608: ("cmp", "rax, 0x30"),
        0x1ED638: ("movsd", "xmm0, qword ptr [rax]"),
        0x1ED63C: ("mulsd", "xmm0, xmm2"),
        0x1ED640: ("addsd", "xmm0, qword ptr [rax + 0x18]"),
        0x1ED645: ("movsd", "xmm1, qword ptr [rax + 8]"),
        0x1ED64A: ("mulsd", "xmm1, xmm2"),
        0x1ED64E: ("addsd", "xmm1, qword ptr [rax + 0x20]"),
        0x1ED653: ("mulsd", "xmm2, qword ptr [rax + 0x10]"),
        0x1ED658: ("addsd", "xmm2, qword ptr [rax + 0x28]"),
        0x1ED666: ("call", "0x1c07e0"),
        0x1C07F0: ("mulsd", "xmm4, xmm4"),
        0x1C087D: ("sqrtsd", "xmm2, xmm4"),
        0x1C08CC: ("subpd", "xmm1, xmm2"),
        0x1C08D5: ("divpd", "xmm1, xmm0"),
        # Public left/right flags choose root slot 0 or slot 1.
        0x1ED507: ("ucomisd", "xmm0, qword ptr [rbx + 0x20]"),
        0x1ED50E: ("cmp", "byte ptr [rbx + 0x18], 0"),
        0x1ED51B: ("cmp", "byte ptr [rbx + 0x19], 0"),
        0x1ED521: ("mov", "rax, r12"),
        0x1ED526: ("lea", "rax, [r12 + 8]"),
        # Axis normalization, degree conversion, image-axis sign selection,
        # reflected center, transpose, and t = -R*C.
        0x1C75D3: ("sqrtsd", "xmm2, xmm2"),
        0x1C75DF: ("divsd", "xmm3, xmm2"),
        0x1C75FE: ("mulsd", "xmm0, qword ptr [rip + 0x40c4c2]"),
        0x1C7606: ("call", "0x555ed0"),
        0x1C78B8: ("cmp", "byte ptr [rbx + 0xb0], 0"),
        0x1C7955: ("mulsd", "xmm2, xmm7"),
        0x1C796F: ("addsd", "xmm2, qword ptr [rbx + 0x60]"),
        0x1C79AD: ("addsd", "xmm0, xmm0"),
        0x1C79ED: ("call", "0x1c7580"),
        0x1C7A81: ("movapd", "xmm1, xmmword ptr [rip + 0x3e0637]"),
        0x1C7A89: ("xorpd", "xmm3, xmm1"),
        0x1C7A8D: ("xorpd", "xmm0, xmm1"),
    }
    for address, wanted in expected.items():
        actual = instruction_at(data, address)
        require(actual == wanted, f"0x{address:x}: expected {wanted}, got {actual}")


def schema_module():
    spec = importlib.util.spec_from_file_location("embedded_schema", SCHEMA)
    require(spec is not None and spec.loader is not None, "cannot load schema verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def one(module, fields, number, wire_type):
    return module.one_field(fields, number, wire_type)


def f32(raw: bytes) -> float:
    return struct.unpack("<f", raw)[0]


def packed_f32(fields, number: int) -> list[float]:
    out: list[float] = []
    for wire_type, value in fields.get(number, []):
        if wire_type == 5:
            out.append(f32(value))
        elif wire_type == 2:
            require(len(value) % 4 == 0, f"field {number}: bad packed-float size")
            out.extend(struct.unpack("<" + "f" * (len(value) // 4), value))
        else:
            raise AssertionError(f"field {number}: wire type {wire_type}")
    return out


def point(module, raw: bytes) -> list[float]:
    fields = module.fields_by_number(raw)
    return [f32(one(module, fields, field, 5)) for field in (1, 2, 3)]


def matrix(module, raw: bytes) -> list[float]:
    fields = module.fields_by_number(raw)
    return [f32(one(module, fields, field, 5)) for field in range(1, 10)]


def decode_public(
    module, path: Path, required_live_keys: set[int] = MOVABLE_KEYS
) -> tuple[dict[int, int], dict[int, dict]]:
    mirror_positions: dict[int, int] = {}
    calibrations: dict[int, dict] = {}
    for _block, payload in module.walk_lri_payloads(path):
        top = module.fields_by_number(payload)
        for wire_type, raw_module in top.get(12, []):
            if wire_type != 2:
                continue
            fields = module.fields_by_number(raw_module)
            key = int(one(module, fields, 2, 0))
            mirror_positions[key] = int(one(module, fields, 4, 0)) if 4 in fields else 0
        for wire_type, raw_calibration in top.get(13, []):
            if wire_type != 2:
                continue
            calibration = module.fields_by_number(raw_calibration)
            key = int(one(module, calibration, 1, 0))
            if 3 not in calibration:
                continue
            geometry = module.fields_by_number(one(module, calibration, 3, 2))
            movable = []
            for bundle_wire, raw_bundle in geometry.get(2, []):
                require(bundle_wire == 2, f"{path}: bad focus-bundle wire")
                bundle = module.fields_by_number(raw_bundle)
                if 3 not in bundle:
                    continue
                extrinsics = module.fields_by_number(one(module, bundle, 3, 2))
                if 2 in extrinsics:
                    movable.append(module.fields_by_number(one(module, extrinsics, 2, 2)))
            if not movable:
                continue
            require(len(movable) == 1, f"{path} key {key}: movable bundle count {len(movable)}")
            raw = movable[0]
            system = module.fields_by_number(one(module, raw, 1, 2))
            mapping = module.fields_by_number(one(module, raw, 2, 2))
            quadratic = module.fields_by_number(one(module, mapping, 7, 2))
            calibrations[key] = {
                "system": {
                    "location": point(module, one(module, system, 1, 2)),
                    "orientation": matrix(module, one(module, system, 2, 2)),
                    "axis": point(module, one(module, system, 3, 2)),
                    "point": point(module, one(module, system, 4, 2)),
                    "distance": f32(one(module, system, 5, 5)),
                    "normal0": point(module, one(module, system, 6, 2)),
                    "flip_x": bool(one(module, system, 7, 0)),
                },
                "mapping": {
                    "type": int(one(module, mapping, 1, 0)),
                    "length_offset": f32(one(module, mapping, 2, 5)),
                    "length_scale": f32(one(module, mapping, 3, 5)),
                    "angle_offset": f32(one(module, mapping, 4, 5)),
                    "angle_scale": f32(one(module, mapping, 5, 5)),
                    "use_plus_left": bool(one(module, quadratic, 1, 0)),
                    "use_plus_right": bool(one(module, quadratic, 2, 0)),
                    "inflection": f32(one(module, quadratic, 3, 5)),
                    "coeffs": packed_f32(quadratic, 4),
                },
            }
    require(set(calibrations) == MOVABLE_KEYS, f"{path}: movable keys {sorted(calibrations)}")
    require(required_live_keys <= set(mirror_positions), f"{path}: missing live mirror positions")
    return mirror_positions, calibrations


def angle_from_mapping(hall: float, mapping: dict) -> float:
    require(mapping["type"] == 0, f"unobserved transform type {mapping['type']}")
    coeffs = mapping["coeffs"]
    require(len(coeffs) == 6, f"quadratic coefficient count {len(coeffs)}")
    x = (hall - mapping["length_offset"]) / mapping["length_scale"]
    a = coeffs[0] * x + coeffs[3]
    b = coeffs[1] * x + coeffs[4]
    c = coeffs[2] * x + coeffs[5]
    discriminant = b * b - 4.0 * a * c
    require(discriminant >= 0.0, f"negative actuator discriminant {discriminant}")
    root_plus = (-b + math.sqrt(discriminant)) / (2.0 * a)
    root_minus = (-b - math.sqrt(discriminant)) / (2.0 * a)
    use_plus = (
        mapping["use_plus_left"]
        if hall < mapping["inflection"]
        else mapping["use_plus_right"]
    )
    root = root_plus if use_plus else root_minus
    return mapping["angle_offset"] + mapping["angle_scale"] * root


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)] for r in range(3)]


def transpose(a: list[list[float]]) -> list[list[float]]:
    return [[a[c][r] for c in range(3)] for r in range(3)]


def matvec(a: list[list[float]], v: list[float]) -> list[float]:
    return [sum(a[r][k] * v[k] for k in range(3)) for r in range(3)]


def pose(system: dict, angle_degrees: float) -> tuple[list[float], list[float]]:
    axis = system["axis"]
    axis_norm = math.sqrt(sum(value * value for value in axis))
    axis = [value / axis_norm for value in axis]
    n0 = system["normal0"]
    theta = angle_degrees * math.pi / 180.0
    cosine = math.cos(theta)
    sine = math.sin(theta)
    cross = [
        axis[1] * n0[2] - axis[2] * n0[1],
        axis[2] * n0[0] - axis[0] * n0[2],
        axis[0] * n0[1] - axis[1] * n0[0],
    ]
    dot = sum(axis[index] * n0[index] for index in range(3))
    normal = [
        n0[index] * cosine + cross[index] * sine + axis[index] * dot * (1.0 - cosine)
        for index in range(3)
    ]
    reflection = [
        [(1.0 if row == col else 0.0) - 2.0 * normal[row] * normal[col] for col in range(3)]
        for row in range(3)
    ]
    orientation = [system["orientation"][row * 3 : row * 3 + 3] for row in range(3)]
    row_sign = [-1.0, 1.0, 1.0] if not system["flip_x"] else [1.0, -1.0, 1.0]
    rotation = matmul(transpose(orientation), reflection)
    rotation = [[row_sign[row] * value for value in rotation[row]] for row in range(3)]
    plane_point = [
        system["point"][index] + system["distance"] * normal[index] for index in range(3)
    ]
    center_dot = sum(
        normal[index] * (plane_point[index] - system["location"][index]) for index in range(3)
    )
    center = [
        system["location"][index] + 2.0 * normal[index] * center_dot for index in range(3)
    ]
    translation = [-value for value in matvec(rotation, center)]
    return [value for row in rotation for value in row], translation


def group_events(report: dict) -> dict[int, dict[str, dict]]:
    grouped: dict[int, dict[str, dict]] = {}
    for event in report["events"]:
        packet = event["packet"]
        key = int(packet["object"]["camera_id_0x60"])
        grouped.setdefault(key, {})[event["site_name"]] = packet
    return grouped


def close_lists(actual, expected, tolerance: float, label: str) -> float:
    require(len(actual) == len(expected), f"{label}: length")
    error = max(abs(float(a) - float(b)) for a, b in zip(actual, expected))
    require(error <= tolerance, f"{label}: max error {error}")
    return error


def verify_case(module, label: str, path: Path) -> str:
    report = json.loads((RUN_ROOT / f"{label}.json").read_text())
    require(report["process"] == {"exit_status": 0, "state": "exited"}, f"{label}: process")
    require(not report["errors"], f"{label}: errors {report['errors']}")
    require(not report["drive_hit_step_cap"], f"{label}: step cap")
    for site in (0x1F109C, 0x1F10A1, 0x1F10B2, 0x1F10B7):
        require(report["counts"][f"0x{site:x}"] == 8, f"{label}: site 0x{site:x}")
    require(report["counts"]["0x1f1328"] == 10, f"{label}: factory-copy count")
    mirror_positions, calibrations = decode_public(module, path)
    grouped = group_events(report)
    require(MOVABLE_KEYS <= set(grouped), f"{label}: missing runtime movable keys")
    max_angle_error = max_pose_error = max_public_error = 0.0
    root_choices: set[str] = set()
    for key in sorted(MOVABLE_KEYS):
        events = grouped[key]
        required = {
            "before_actuator_mapping", "after_actuator_mapping", "before_mirror_pose",
            "after_mirror_pose", "before_factory_copy",
        }
        require(required <= set(events), f"{label} key {key}: sites {sorted(events)}")
        before = events["before_mirror_pose"]["mirror_system"]
        public = calibrations[key]
        mapping = public["mapping"]
        use_plus = (
            mapping["use_plus_left"]
            if mirror_positions[key] < mapping["inflection"]
            else mapping["use_plus_right"]
        )
        root_choices.add("plus" if use_plus else "minus")
        public_system = public["system"]
        runtime_point = before.get("point_on_rotation_axis_0x60", before.get("rotation_axis_0x60"))
        runtime_axis = before.get("rotation_axis_0x78", before.get("mirror_normal_zero_0x78"))
        runtime_normal0 = before.get("mirror_normal_zero_0x90", before.get("point_on_rotation_axis_0x90"))
        max_public_error = max(
            max_public_error,
            close_lists(before["real_camera_orientation_0x00"], public_system["orientation"], 0.0, "orientation"),
            close_lists(before["real_camera_location_0x48"], public_system["location"], 0.0, "location"),
            close_lists(runtime_point, public_system["point"], 0.0, "point"),
            close_lists(runtime_axis, public_system["axis"], 0.0, "axis"),
            close_lists(runtime_normal0, public_system["normal0"], 0.0, "normal0"),
            abs(before["distance_0xa8"] - public_system["distance"]),
        )
        require(bool(before["flip_img_around_x_0xb0"]) == public_system["flip_x"], "flip mismatch")
        hall = float(mirror_positions[key])
        mapping_event = events["before_actuator_mapping"]
        require(mapping_event["mapping_input_hall_f64"] == hall, f"{label} key {key}: hall")
        expected_angle = angle_from_mapping(hall, mapping)
        actual_angle = events["after_actuator_mapping"]["mapping_output_angle_degrees_f64"]
        max_angle_error = max(max_angle_error, abs(actual_angle - expected_angle))
        expected_rotation, expected_translation = pose(public_system, expected_angle)
        after = events["after_mirror_pose"]
        max_pose_error = max(
            max_pose_error,
            close_lists(after["rotation_output_f64x9"], expected_rotation, 5e-13, "rotation"),
            close_lists(after["translation_output_f64x3"], expected_translation, 5e-13, "translation"),
        )
        copied = events["before_factory_copy"]
        expected_rotation_f32 = [struct.unpack("<f", struct.pack("<f", value))[0] for value in expected_rotation]
        expected_translation_f32 = [struct.unpack("<f", struct.pack("<f", value))[0] for value in expected_translation]
        close_lists(copied["rotation_copy_f32x9"], expected_rotation_f32, 0.0, "f32 rotation copy")
        close_lists(copied["translation_copy_f32x3"], expected_translation_f32, 0.0, "f32 translation copy")
    require(max_angle_error <= 1e-12, f"{label}: angle error {max_angle_error}")
    require(root_choices == {"minus"}, f"{label}: unsupported root choices {root_choices}")
    hdr = RUN_ROOT / f"{label}.hdr"
    require(hdr.read_bytes()[:10] == b"#?RADIANCE", f"{label}: output")
    return (
        f"{label}: keys=5,6,7,9,10,11,12,13 type=0 root=minus "
        f"max_public_err={max_public_error:.3g} max_angle_err={max_angle_error:.3g} "
        f"max_pose_err={max_pose_error:.3g}"
    )


def verify_retained_case(module, label: str, path: Path, report_path: Path) -> str:
    report = json.loads(report_path.read_text())
    require(report["process"]["exit_status"] == 0, f"{label}: process")
    require(not report["errors"], f"{label}: errors {report['errors']}")
    require(not report["drive_hit_step_cap"], f"{label}: step cap")
    expected_keys = {5, 6, 7, 9}
    mirror_positions, calibrations = decode_public(module, path, expected_keys)
    packets = {
        int(event["trace"]["object"]["key_i32_0x60"]): event["trace"]
        for event in report["events"]
        if event["site_name"] == "selector0_f33d0_call"
    }
    keys = sorted(MOVABLE_KEYS & set(packets))
    require(keys == sorted(expected_keys), f"{label}: retained movable keys {keys}")
    max_pose_error = 0.0
    for key in keys:
        mapping = calibrations[key]["mapping"]
        require(mapping["type"] == 0, f"{label} key {key}: transform type")
        require(
            not mapping["use_plus_left"] and not mapping["use_plus_right"],
            f"{label} key {key}: unobserved root selector",
        )
        expected_rotation, expected_translation = pose(
            calibrations[key]["system"],
            angle_from_mapping(float(mirror_positions[key]), mapping),
        )
        expected_rotation_f32 = [
            struct.unpack("<f", struct.pack("<f", value))[0] for value in expected_rotation
        ]
        expected_translation_f32 = [
            struct.unpack("<f", struct.pack("<f", value))[0] for value in expected_translation
        ]
        packet = packets[key]
        max_pose_error = max(
            max_pose_error,
            close_lists(packet["pose_stack"]["f32x9"], expected_rotation_f32, 0.0, "retained R"),
            close_lists(
                packet["triple_stack"]["f32x3"],
                expected_translation_f32,
                0.0,
                "retained t",
            ),
        )
    return f"{label}: keys=5,6,7,9 type=0 root=minus f32_pose_err={max_pose_error:.3g}"


def main() -> None:
    data = LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == EXPECTED_LIBCP_SHA256, "libcp SHA-256 drift")
    verify_static_formula(data)
    module = schema_module()
    mirror_descriptor = module.decode_file_descriptor(
        data, module.locate_descriptor(data, "mirror_system.proto")
    )
    fields = module.field_map([mirror_descriptor])
    module.require_field(fields, ".ltpb.MirrorSystem", 7, "flip_img_around_x", "bool")
    module.require_field(fields, ".ltpb.MirrorActuatorMapping", 7, "quadratic_model", "message")
    module.require_field(
        fields, ".ltpb.MirrorActuatorMapping.QuadraticModel", 4, "model_coeffs", "float"
    )
    enum = next(
        value for value in mirror_descriptor["enums"]
        if value["full_name"] == ".ltpb.MirrorActuatorMapping.TransformationType"
    )
    require(enum["values"][0] == {"name": "MEAN_STD_NORMALIZE", "number": 0}, "enum drift")
    windows = data[0x1F08A0:0x1F09FA] + data[0x1ED4D0:0x1ED5F0]
    windows += data[0x1C7580:0x1C79DC] + data[0x1C79E0:0x1C7AA1]
    pi_over_180 = struct.unpack_from("<d", data, 0x5D3AC8)[0]
    require(pi_over_180 == math.pi / 180.0, "degrees-to-radians constant")
    print(
        "static_movable_mirror=OK "
        f"window_sha256={hashlib.sha256(windows).hexdigest()} "
        f"descriptor_sha256={mirror_descriptor['serialized_sha256']}"
    )
    for label, path in CASES.items():
        print(verify_case(module, label, path))
    for label, (path, report_path) in RETAINED_CASES.items():
        print(verify_retained_case(module, label, path, report_path))


if __name__ == "__main__":
    main()
