#!/usr/bin/env python3
"""Verify and replay the installed 0x145980 undistort-envelope builder."""

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
DISTORTION_VERIFIER = ROOT / "tools/lldb_probes/distortion_table/verify_distortion_table.py"
REFERENCE_VERIFIER = (
    ROOT / "tools/lldb_probes/reference_undistorted_planes/verify_reference_validation_artifacts.py"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

UNIT1_REPORTS = {
    "28mm": ROOT / "runs/state_448_later_box_formula/box_formula_28mm.json",
    "35mm": ROOT / "runs/state_448_later_box_formula/box_formula_35mm.json",
    "70mm": ROOT / "runs/state_448_later_box_formula/box_formula_70mm.json",
    "150mm": ROOT / "runs/state_448_later_box_formula/box_formula_150mm.json",
}
UNIT1_LRIS = {
    "28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "35mm": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
    "70mm": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
    "150mm": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
}
UNIT2_REPORT = ROOT / "runs/g38_undistort_envelope/unit2_70mm_box.json"
UNIT2_LRI = Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DIST = load_module("g38_distortion", DISTORTION_VERIFIER)
REFERENCE = load_module("g38_reference", REFERENCE_VERIFIER)

f32 = DIST.f32
add = DIST.add
sub = DIST.sub
mul = DIST.mul
div = DIST.div


def bytes_at(data, address, size):
    # This installed dylib maps __TEXT at VA/file offset zero.
    return data[address : address + size]


def instruction(data, address):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    item = next(decoder.disasm(bytes_at(data, address, 16), address))
    return item.mnemonic, item.op_str


def verify_static():
    data = LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == LIBCP_SHA256, "installed libcp digest")
    windows = {
        (0x145980, 0x14624D): "1ff1fb1ee335178428a8f412e490f40535bf35361be15b9f6010f3b85123850e",
        (0x145A1F, 0x146141): "93a6d49fc8676dbb1949e762aaf8ae1d72af94fc8fc559323611108dac516b32",
        (0x146380, 0x146501): "24f543dd29eecdfdcdb38a87b12870febfa1a0d2936ce2464e2ab5c82711a19e",
    }
    for (start, end), expected in windows.items():
        digest = hashlib.sha256(bytes_at(data, start, end - start)).hexdigest()
        require(digest == expected, f"0x{start:x}..0x{end:x} digest")

    expected = {
        0x145A45: ("divss", "xmm1, xmm0"),
        0x145A8C: ("mulss", "xmm0, xmm2"),
        0x145A9C: ("mulss", "xmm1, xmm2"),
        0x145AAC: ("subss", "xmm0, xmm1"),
        0x145B17: ("mulss", "xmm0, dword ptr [rip + 0x47fce5]"),
        0x145C41: ("cvttss2si", "eax, xmm1"),
        0x145C45: ("cmp", "eax, edx"),
        0x145C4C: ("cmovle", "eax, ebx"),
        0x145D3A: ("divss", "xmm9, xmm3"),
        0x145D46: ("mulss", "xmm9, xmm11"),
        0x145D59: ("subss", "xmm1, xmm9"),
        0x145D85: ("maxss", "xmm13, xmm1"),
        0x145DF4: ("divss", "xmm4, xmm5"),
        0x145E05: ("minss", "xmm1, xmm4"),
        0x145E0B: ("cmp", "edi, 0x5b"),
        0x145E2D: ("mulss", "xmm6, dword ptr [rip + 0x47f9d3]"),
        0x146058: ("maxss", "xmm0, xmm1"),
        0x1460DB: ("minss", "xmm1, xmm4"),
        0x1460F1: ("cmp", "eax, 0x79"),
        0x146102: ("cvttss2si", "eax, xmm1"),
        0x146106: ("cvttss2si", "ecx, xmm0"),
        0x14611D: ("cvttss2si", "edx, xmm11"),
        0x14612A: ("cvttss2si", "esi, xmm4"),
        0x146498: ("mov", "rcx, qword ptr [r15]"),
        0x1464E8: ("divss", "xmm0, xmm1"),
    }
    for address, wanted in expected.items():
        observed = instruction(data, address)
        require(observed == wanted, f"0x{address:x}: {observed} != {wanted}")

    require(struct.unpack("<f", bytes_at(data, 0x5C5804, 4))[0] == f32(1.0 / 90.0), "1/90")
    require(struct.unpack("<f", bytes_at(data, 0x5C5808, 4))[0] == f32(1.0 / 120.0), "1/120")
    require(struct.unpack("<d", bytes_at(data, 0x5A8130, 8))[0] == 1.0 / 3.0, "1/3")
    require(struct.unpack("<d", bytes_at(data, 0x5A8138, 8))[0] == 1.0 / 6.0, "1/6")
    return "g38_static=OK body=0x145980 samples=91x121"


def sample_vectors(state, pixel_size):
    inverse_scale = div(1.0, pixel_size)
    distorted_pixels = []
    radial_delta_pixels = []
    for index in range(30):
        radius = mul(f32(index), f32(0.1))
        sample_x = add(mul(radius, inverse_scale), state["center_x"])
        output_x, _output_y = DIST.brown_conrady(state, sample_x, state["center_y"])
        distorted_radius = mul(sub(output_x, state["center_x"]), pixel_size)
        distorted_pixel_radius = mul(distorted_radius, inverse_scale)
        uniform_pixel_radius = mul(radius, inverse_scale)
        distorted_pixels.append(distorted_pixel_radius)
        radial_delta_pixels.append(sub(uniform_pixel_radius, distorted_pixel_radius))
    return distorted_pixels, radial_delta_pixels


def interpolate_target_radius(radius, x_values, deltas):
    step = div(sub(x_values[-1], x_values[0]), f32(len(x_values) - 1))
    position = div(sub(radius, x_values[0]), step)
    index = int(position)
    index = min(index, len(x_values) - 3)
    index = max(index, 1)
    fraction = sub(position, f32(index))
    fraction2 = mul(fraction, fraction)

    w0 = sub(1.0, fraction2)
    w1 = add(fraction2, fraction)
    wm1 = sub(fraction2, fraction)
    w2 = mul(add(fraction2, -1.0), fraction)
    shared = add(mul(fraction, -0.5), 1.0)
    wm1 = div(mul(wm1, shared), 3.0)
    w2 = div(w2, 6.0)

    value = add(mul(w0, deltas[index]), mul(w1, deltas[index + 1]))
    value = mul(value, shared)
    value = add(value, mul(wm1, deltas[index - 1]))
    value = add(value, mul(w2, deltas[index + 2]))
    return add(radius, value)


def sqrtf(value):
    return f32(math.sqrt(f32(value)))


def build_box(state, pixel_size, width=4160, height=3120):
    x_values, deltas = sample_vectors(state, pixel_size)
    cx = state["center_x"]
    cy = state["center_y"]

    left = f32(0.0)
    right = f32(width - 1)
    y_step = mul(f32(height), f32(1.0 / 90.0))
    right_delta = sub(f32(width - 1), cx)
    for index in range(91):
        y_delta = sub(mul(f32(index), y_step), cy)
        left_radius = sqrtf(add(mul(y_delta, y_delta), mul(cx, cx)))
        target_radius = interpolate_target_radius(left_radius, x_values, deltas)
        left_x = sub(cx, div(mul(target_radius, cx), left_radius))
        left = max(left, left_x)

        right_radius = sqrtf(add(mul(y_delta, y_delta), mul(right_delta, right_delta)))
        target_radius = interpolate_target_radius(right_radius, x_values, deltas)
        right_x = add(cx, div(mul(target_radius, right_delta), right_radius))
        right = min(right, right_x)

    top = f32(0.0)
    bottom = f32(height - 1)
    x_step = mul(f32(width), f32(1.0 / 120.0))
    bottom_delta = sub(f32(height - 1), cy)
    for index in range(121):
        x_delta = sub(mul(f32(index), x_step), cx)
        top_radius = sqrtf(add(mul(x_delta, x_delta), mul(cy, cy)))
        target_radius = interpolate_target_radius(top_radius, x_values, deltas)
        top_y = sub(cy, div(mul(target_radius, cy), top_radius))
        top = max(top, top_y)

        bottom_radius = sqrtf(add(mul(x_delta, x_delta), mul(bottom_delta, bottom_delta)))
        target_radius = interpolate_target_radius(bottom_radius, x_values, deltas)
        bottom_y = add(cy, div(mul(target_radius, bottom_delta), bottom_radius))
        bottom = min(bottom, bottom_y)

    x0 = int(left)
    y0 = int(top)
    x1 = x0 + int(sub(add(right, 1.0), left))
    y1 = y0 + int(sub(add(bottom, 1.0), top))
    return [x0, y0, x1, y1]


def report_boxes(path):
    report = json.loads(path.read_text())
    process = report["process"]
    require(process["state"] == "exited" and process["exit_status"] == 0, f"{path}: process")
    require(not report.get("errors") and not report.get("drive_hit_step_cap"), f"{path}: probe")
    boxes = {}
    for event in report["events"]:
        if event["site_name"] == "post_145980_box":
            packet = event["packet"]
            boxes[int(packet["key"])] = packet["box_i32_xyxy"]
    require(len(boxes) == 5, f"{path}: box count {len(boxes)}")
    return boxes


def public_case(parser, schema, lri):
    records, pixel_sizes, geometry_sha = DIST.public_records(parser, schema, lri)
    return records, pixel_sizes, geometry_sha


def replay_report(label, report, lri, parser, schema):
    records, pixel_sizes, geometry_sha = public_case(parser, schema, lri)
    observed = report_boxes(report)
    for key, box in observed.items():
        expected = build_box(DIST.state_from_public(records[key]), pixel_sizes[key])
        require(expected == box, f"{label} key {key}: {expected} != {box}")
    return f"{label}: boxes={len(observed)} keys={','.join(str(key) for key in sorted(observed))} geometry={geometry_sha[:16]}"


def main():
    print(verify_static())
    # This rechecks the exact public Brown-Conrady samples and 4096-entry tables.
    DIST.verify_static()
    parser = DIST.load_public_parser()
    schema = parser.load_schema_module()
    for label, lri in DIST.CASES.items():
        result = DIST.verify_case(label, lri, parser, schema)
        print(f"{label}: table=OK camera={result['camera_key']} sha256={result['table_sha256'][:16]}")

    for tier, report in UNIT1_REPORTS.items():
        print(replay_report(f"Unit-1 {tier}", report, UNIT1_LRIS[tier], parser, schema))
    print(replay_report("Unit-2 70mm", UNIT2_REPORT, UNIT2_LRI, parser, schema))

    REFERENCE.verify_static()
    REFERENCE.verify_undistorted()
    print("undistorted_reference_planes=OK count=20 four_focal repeat_28mm=byte_identical")
    print("g38_undistort_envelope=OK")


if __name__ == "__main__":
    main()
