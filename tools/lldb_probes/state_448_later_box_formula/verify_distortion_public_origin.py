#!/usr/bin/env python3
"""Verify public Distortion.polynomial custody into the state+0x448 box path."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
SCHEMA_VERIFIER = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
RUN_ROOT = ROOT / "runs/state_448_distortion_public_origin"
CASES = {
    "unit1_28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "unit2_70mm": Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
}
EXPECTED_LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

STATIC_ANCHORS = {
    0xE353F: ("mov", "eax, dword ptr [rbx + 0x10]"),
    0xE3542: ("test", "al, 1"),
    0xE3546: ("lea", "rdi, [r14 + 0x30]"),
    0xE354A: ("mov", "rsi, qword ptr [rbx + 0x30]"),
    0xE3559: ("call", "0x1302e0"),
    0x131720: ("mov", "rax, qword ptr [rbp - 0x750]"),
    0x131727: ("mov", "r15, qword ptr [rax + 0x30]"),
    0x131736: ("test", "byte ptr [r15 + 0x10], 3"),
    0x131B5A: ("test", "al, 1"),
    0x131B62: ("mov", "r13, qword ptr [r15 + 0x18]"),
    0x131B71: ("mov", "rax, qword ptr [r13 + 0x30]"),
    0x131B75: ("mov", "rcx, qword ptr [r13 + 0x38]"),
    0x131BC0: ("mov", "eax, dword ptr [r13 + 0x18]"),
    0x131C0E: ("mov", "rsi, qword ptr [r13 + 0x20]"),
    0x131D4B: ("mov", "dword ptr [rsi + 0x60], ebx"),
    0x131D4E: ("mov", "dword ptr [rsi + 0x64], r14d"),
    0x131D52: ("mov", "dword ptr [rsi + 0x68], ecx"),
    0x131D55: ("mov", "dword ptr [rsi + 0x6c], r13d"),
    0x131D67: ("mov", "qword ptr [rax], r8"),
    0x131D6A: ("movups", "xmmword ptr [rsi + 0x78], xmm1"),
    0x131D78: ("mov", "byte ptr [rsi + 0x8c], 0"),
    0xF336C: ("mov", "rdi, qword ptr [rax + 0xa0]"),
    0xF3378: ("mov", "esi, dword ptr [rax + 0x60]"),
    0xF337B: ("call", "0xe7220"),
    0xE7224: ("mov", "rdx, qword ptr [rdi + 0x2a8]"),
    0xE7240: ("cmp", "dword ptr [rax + 0x20], esi"),
    0xE727C: ("add", "rax, 0x30"),
    0x1455CD: ("call", "0xf3360"),
    0x1455D2: ("mov", "rbx, rax"),
    0x1455D5: ("cmp", "byte ptr [rbx + 0x90], 0"),
    0x14568C: ("mov", "eax, dword ptr [rbx + 0x68]"),
    0x14568F: ("mov", "ecx, dword ptr [rbx + 0x6c]"),
    0x145692: ("mov", "edx, dword ptr [rbx + 0x60]"),
    0x145695: ("mov", "esi, dword ptr [rbx + 0x64]"),
    0x1456CD: ("mov", "rsi, rbx"),
    0x1456D0: ("add", "rsi, 0x70"),
    0x1456E2: ("call", "0xe730"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_schema_module():
    spec = importlib.util.spec_from_file_location("embedded_schema", SCHEMA_VERIFIER)
    require(spec is not None and spec.loader is not None, "cannot load schema verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_descriptors(module, data: bytes) -> dict[str, str]:
    names = ("distortion.proto", "geometric_calibration.proto", "lightheader.proto")
    descriptors = [
        module.decode_file_descriptor(data, module.locate_descriptor(data, name))
        for name in names
    ]
    fields = module.field_map(descriptors)
    module.require_field(fields, ".ltpb.LightHeader", 13, "module_calibration", "message")
    module.require_field(fields, ".ltpb.FactoryModuleCalibration", 3, "geometry", "message")
    module.require_field(fields, ".ltpb.GeometricCalibration", 3, "distortion", "message")
    module.require_field(fields, ".ltpb.Distortion", 1, "polynomial", "message")
    module.require_field(fields, ".ltpb.Distortion.Polynomial", 1, "distortion_center", "message")
    module.require_field(fields, ".ltpb.Distortion.Polynomial", 2, "normalization", "message")
    module.require_field(fields, ".ltpb.Distortion.Polynomial", 3, "coeffs", "float")
    module.require_field(fields, ".ltpb.Distortion.Polynomial", 4, "fit_cost", "float")
    module.require_field(fields, ".ltpb.Distortion.Polynomial", 5, "valid_roi", "message")
    return {descriptor["name"]: descriptor["serialized_sha256"] for descriptor in descriptors}


def verify_static_anchors(data: bytes) -> str:
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = {}
    for start, end in (
        (0xE3360, 0xE3565),
        (0xE7220, 0xE7282),
        (0xF3360, 0xF3380),
        (0x1302E0, 0x1325C1),
        (0x145590, 0x1456E7),
    ):
        instructions.update({ins.address: ins for ins in md.disasm(data[start:end], start)})
    for address, expected in STATIC_ANCHORS.items():
        instruction = instructions.get(address)
        require(instruction is not None, f"missing instruction at 0x{address:x}")
        observed = (instruction.mnemonic, instruction.op_str)
        require(observed == expected, f"0x{address:x}: {observed} != {expected}")
    window = data[0xE3360:0xE3565] + data[0xE7220:0xE7282] + data[0xF3360:0xF3380]
    window += data[0x1302E0:0x1325C1] + data[0x145590:0x1456E7]
    return hashlib.sha256(window).hexdigest()


def one_raw(fields: dict[int, list[tuple[int, object]]], number: int, wire_type: int):
    values = fields.get(number, [])
    require(len(values) == 1 and values[0][0] == wire_type, f"field {number}: {values}")
    return values[0][1]


def point_words(module, raw: bytes) -> list[int]:
    fields = module.fields_by_number(raw)
    x = one_raw(fields, 1, 5)
    y = one_raw(fields, 2, 5)
    return [struct.unpack("<I", x)[0], struct.unpack("<I", y)[0]]


def packed_float_words(fields: dict[int, list[tuple[int, object]]], number: int) -> list[int]:
    words: list[int] = []
    for wire_type, value in fields.get(number, []):
        if wire_type == 5:
            require(isinstance(value, bytes) and len(value) == 4, f"field {number}: bad fixed32")
            words.append(struct.unpack("<I", value)[0])
        elif wire_type == 2:
            require(isinstance(value, bytes) and len(value) % 4 == 0, f"field {number}: bad packed float")
            words.extend(struct.unpack("<" + "I" * (len(value) // 4), value))
        else:
            raise AssertionError(f"field {number}: unexpected wire type {wire_type}")
    return words


def public_polynomials(module, path: Path) -> tuple[dict[int, dict], str]:
    records: dict[int, dict] = {}
    geometry_payload = None
    for _block_index, payload in module.walk_lri_payloads(path):
        top = module.fields_by_number(payload)
        block_records = 0
        for wire_type, raw_calibration in top.get(13, []):
            if wire_type != 2:
                continue
            calibration = module.fields_by_number(raw_calibration)
            if 3 not in calibration:
                continue
            camera_id = one_raw(calibration, 1, 0)
            geometry = module.fields_by_number(one_raw(calibration, 3, 2))
            distortion = module.fields_by_number(one_raw(geometry, 3, 2))
            polynomial = module.fields_by_number(one_raw(distortion, 1, 2))
            center = point_words(module, one_raw(polynomial, 1, 2))
            normalization = point_words(module, one_raw(polynomial, 2, 2))
            fit_values = polynomial.get(4, [])
            fit_word = None
            if fit_values:
                require(len(fit_values) == 1 and fit_values[0][0] == 5, "bad fit_cost")
                fit_word = struct.unpack("<I", fit_values[0][1])[0]
            records[int(camera_id)] = {
                "center_normalization_words": center + normalization,
                "coeff_words": packed_float_words(polynomial, 3),
                "fit_cost_word": fit_word,
            }
            block_records += 1
        if block_records:
            geometry_payload = payload
    require(sorted(records) == list(range(16)), f"{path}: polynomial cameras {sorted(records)}")
    require(geometry_payload is not None, f"{path}: no geometry payload")
    return records, hashlib.sha256(geometry_payload).hexdigest()


def verify_runtime_case(module, label: str, path: Path) -> str:
    report_path = RUN_ROOT / f"{label}.json"
    report = json.loads(report_path.read_text())
    process = report["process"]
    require(process["state"] == "exited", f"{label}: process state {process}")
    require(process["exit_status"] == 0, f"{label}: nonzero exit")
    require(not report.get("errors"), f"{label}: errors {report.get('errors')}")
    require(not report.get("drive_hit_step_cap"), f"{label}: step cap")
    require(report.get("events"), f"{label}: no events")
    require(report.get("site_va") == 0x1455D5, f"{label}: site drift")

    public, geometry_sha = public_polynomials(module, path)
    keys = set()
    for event in report["events"]:
        key = event["camera_key"]
        require(key in public, f"{label}: runtime key {key} absent from public geometry")
        expected = public[key]
        require(event["site_va"] == 0x1455D5, f"{label} key {key}: event site")
        require(event["polynomial_present"] & 0xFF == 1, f"{label} key {key}: polynomial absent")
        require(
            event["center_normalization_words"] == expected["center_normalization_words"],
            f"{label} key {key}: center/normalization mismatch",
        )
        require(event["coeff_words"] == expected["coeff_words"], f"{label} key {key}: coeff mismatch")
        require(event["coeff_count"] == len(expected["coeff_words"]), f"{label} key {key}: coeff count")
        if expected["fit_cost_word"] is None:
            require(event["fit_cost_present"] & 0xFF == 0, f"{label} key {key}: unexpected fit_cost")
        else:
            require(event["fit_cost_present"] & 0xFF == 1, f"{label} key {key}: fit_cost absent")
            require(event["fit_cost_word"] == expected["fit_cost_word"], f"{label} key {key}: fit_cost")
        keys.add(key)

    require(len(keys) >= 5, f"{label}: insufficient distinct runtime keys {sorted(keys)}")
    jpg = RUN_ROOT / f"{label}.jpg"
    require(jpg.read_bytes()[:2] == b"\xff\xd8", f"{label}: output is not JPEG")
    return (
        f"{label}: keys={','.join(str(key) for key in sorted(keys))} "
        f"events={len(report['events'])} geometry_sha256={geometry_sha[:16]}"
    )


def main() -> None:
    data = LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == EXPECTED_LIBCP_SHA256, "libcp SHA-256 drift")
    module = load_schema_module()
    descriptor_hashes = verify_descriptors(module, data)
    static_hash = verify_static_anchors(data)
    print(
        "static_public_distortion_origin=OK "
        f"window_sha256={static_hash} "
        + " ".join(f"{name}={digest[:16]}" for name, digest in sorted(descriptor_hashes.items()))
    )
    for label, path in CASES.items():
        print(verify_runtime_case(module, label, path))


if __name__ == "__main__":
    main()
