#!/usr/bin/env python3
"""Verify non-normal public orientation through final export placement."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
SCHEMA = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
RUNS = ROOT / "runs/output_orientation_policy"
CORPUS = ROOT / "runs/lri_consumed_block_roles/corpus_contract.json"
CASES = {
    "cw": {
        "path": Path("/Volumes/Base Photos/Light/2017-12-02/L16_00622.lri"),
        "unit_hash": "223961c6bce6153e",
        "orientation": 1,
        "aspect_matrix": [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.5, 3.5, 1.0],
        "scaled_matrix": [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 1040.0, 7280.0, 1.0],
        "final_matrix": [
            0.0,
            None,
            -0.0001220703125,
            None,
            0.0,
            6240.0,
            0.0,
            0.0,
            1.0,
        ],
        "report": RUNS / "unit2_35mm_cw.json",
        "log": RUNS / "unit2_35mm_cw.log",
    },
    "ccw": {
        "path": Path("/Volumes/Base Photos/Light/2018-01-24/L16_00202.lri"),
        "unit_hash": "722a6e721636c9c4",
        "orientation": 2,
        "aspect_matrix": [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 3.5, -0.5, 1.0],
        "scaled_matrix": [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 7280.0, -1040.0, 1.0],
        "final_matrix": [
            0.0,
            None,
            8320.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ],
        "report": RUNS / "unit1_35mm_ccw.json",
        "log": RUNS / "unit1_35mm_ccw.log",
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def fields(blob, number=None):
    result = list(parse_proto_fields(blob))
    if number is None:
        return result
    return [(wire, value) for field, wire, value in result if field == number]


def calibration_hash(path):
    for block in scan_lri_blocks(str(path)):
        count = sum(1 for number, _wire, _value in fields(block["payload"]) if number == 13)
        if count == 16:
            return hashlib.sha256(block["payload"]).hexdigest()[:16]
    raise AssertionError(f"{path}: no calibration block")


def installed_schema_orientation_enum(data):
    spec = importlib.util.spec_from_file_location("embedded_schema", SCHEMA)
    require(spec is not None and spec.loader is not None, "schema module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    descriptors = module.locate_all_descriptors(data)
    descriptor = next(item for item in descriptors if item["name"] == "view_preferences.proto")
    enum = next(
        item
        for item in descriptor["enums"]
        if item["full_name"] == ".ltpb.ViewPreferences.Orientation"
    )
    return [(item["name"], item["number"]) for item in enum["values"]]


def verify_static():
    data = LIBCP.read_bytes()
    require(
        hashlib.sha256(data).hexdigest()
        == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        "libcp hash drift",
    )
    require(
        installed_schema_orientation_enum(data)
        == [
            ("ORIENTATION_NORMAL", 0),
            ("ORIENTATION_ROT90_CW", 1),
            ("ORIENTATION_ROT90_CCW", 2),
            ("ORIENTATION_ROT90_CW_VFLIP", 3),
            ("ORIENTATION_ROT90_CCW_VFLIP", 4),
            ("ORIENTATION_VFLIP", 5),
            ("ORIENTATION_HFLIP", 6),
            ("ORIENTATION_ROT180", 7),
        ],
        "orientation enum drift",
    )

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.skipdata = True
    instructions = {}
    for start, end in (
        (0x13F180, 0x13F18A),
        (0x3B2B20, 0x3B2B74),
        (0x3C65A9, 0x3C6603),
        (0x39B630, 0x39B70B),
        (0x39B800, 0x39B80D),
        (0x401BF0, 0x401C84),
        (0x402830, 0x402A08),
        (0x419080, 0x419903),
    ):
        instructions.update(
            {item.address: (item.mnemonic, item.op_str) for item in md.disasm(data[start:end], start)}
        )

    expected = {
        0x13F184: ("lea", "rax, [rdi + 0x2c]"),
        0x3B2B33: ("mov", "qword ptr [rbx + 0xb0], r14"),
        0x3B2B60: ("mov", "esi, 2"),
        0x3B2B6F: ("call", "0x39b800"),
        0x3C65C0: ("call", "0x13f180"),
        0x3C65E8: ("call", "0x13f180"),
        0x3C65F9: ("cmp", "ebx, 8"),
        0x39B68A: ("movups", "xmm0, xmmword ptr [rbx + 0x10]"),
        0x39B808: ("jmp", "0x402830"),
        0x401C2B: ("call", "0x3abeb0"),
        0x402844: ("cmp", "esi, 7"),
        0x4190DF: ("call", "0x402a90"),
        0x41919D: ("call", "0x402c20"),
        0x4198ED: ("mov", "qword ptr [rbx + 0x40], rax"),
    }
    for address, value in expected.items():
        require(instructions.get(address) == value, f"{address:#x}: {instructions.get(address)}")

    table_base = 0x402A50
    offsets = struct.unpack_from("<8i", data, table_base)
    require(
        [table_base + value for value in offsets]
        == [0x402905, 0x40285D, 0x40285D, 0x402A08, 0x402A08, 0x40291A, 0x40293F, 0x402979],
        "orientation jump table drift",
    )
    require(data.startswith(b"?N2lt13TransformImplE\0", 0x60A3BF), "TransformImpl RTTI drift")


def verify_corpus():
    report = json.loads(CORPUS.read_text())
    require(report["status"] == "PASS", "corpus report not PASS")
    require(report["orientation_values"] == {"0": 8769, "1": 408, "2": 65}, "orientation census drift")
    require(
        report["orientation_focal_samples"]["1:35"] == str(CASES["cw"]["path"]),
        "CW sample drift",
    )
    require(
        report["orientation_focal_samples"]["2:35"] == str(CASES["ccw"]["path"]),
        "CCW sample drift",
    )


def verify_runtime(name, case):
    require(calibration_hash(case["path"]) == case["unit_hash"], f"{name}: unit drift")
    report = json.loads(case["report"].read_text())
    require(not report["errors"], f"{name}: {report['errors']}")
    counts = report["counts"]
    require(counts["orientation_accessor"] == 2, f"{name}: accessor count")
    require(counts["orientation_transform_ready"] == 1, f"{name}: transform count")
    require(counts["transform_copy_matrix_read"] == 9, f"{name}: copy count")
    require(counts["scaled_transform_matrix_ready"] == 2, f"{name}: scaled count")
    require(counts["export_transform_output_ready"] == 2, f"{name}: output count")
    require(counts["output_helper_entry"] == 1, f"{name}: helper count")
    require(counts["writer_virtual_call"] == 1, f"{name}: writer count")

    orientation = [item for item in report["events"] if item["site"] == "orientation_accessor"]
    require(
        all(item["present"] and item["orientation"] == case["orientation"] for item in orientation),
        f"{name}: public orientation mismatch",
    )

    transform = next(
        item for item in report["events"] if item["site"] == "orientation_transform_ready"
    )
    require(transform["dimensions"] == {"width": 4, "height": 3}, f"{name}: aspect dims")
    require(transform["matrix3x3"] == case["aspect_matrix"], f"{name}: aspect matrix")
    require(
        transform["crop_envelope"]
        == [0.125, -0.1666666865348816, 0.875, 1.1666667461395264],
        f"{name}: crop envelope",
    )

    copies = [item for item in report["events"] if item["site"] == "transform_copy_matrix_read"]
    require(copies[0]["source_transform"] == transform["transform"], f"{name}: first copy source")
    for current, following in zip(copies, copies[1:]):
        require(
            current["destination_transform"] == following["source_transform"],
            f"{name}: broken copy chain",
        )
    require(
        all(item["source_matrix3x3"] == case["aspect_matrix"] for item in copies),
        f"{name}: copied matrix changed",
    )
    require(
        any(
            any("CIAPI::Renderer::writeImage" in (frame["function"] or "") for frame in item["stack"])
            for item in copies
        ),
        f"{name}: no writeImage copy",
    )
    require(
        sum(
            any("4182a0" in (frame["function"] or "") for frame in item["stack"])
            for item in copies
        )
        == 3,
        f"{name}: final helper copy count",
    )

    scaled = [item for item in report["events"] if item["site"] == "scaled_transform_matrix_ready"]
    for item in scaled:
        require(item["level_dimensions"] == {"width": 8320, "height": 6240}, f"{name}: level dims")
        require(
            item["requested_dimensions"] == {"width": 10432, "height": 7824},
            f"{name}: requested dims",
        )
        require(item["scaled_matrix3x3"] == case["scaled_matrix"], f"{name}: scaled matrix")

    sx = f32(6240.0 / 10432.0)
    sy = f32(8320.0 / 7824.0)
    expected_final = list(case["final_matrix"])
    expected_final[1] = sy if name == "cw" else -sy
    expected_final[3] = -sx if name == "cw" else sx
    outputs = [item for item in report["events"] if item["site"] == "export_transform_output_ready"]
    for item in outputs:
        output = item["transform_output"]
        require(output["level_index"] == 0, f"{name}: level index")
        require(output["roi"] == [0, 0, 8320, 6240], f"{name}: ROI")
        require(output["scale"] == [sx, sy], f"{name}: scale")
        require(output["matrix3x3"] == expected_final, f"{name}: final matrix")

    writer = next(item for item in report["events"] if item["site"] == "writer_virtual_call")
    require(
        writer["writer_descriptor"]["width"] == 10432
        and writer["writer_descriptor"]["height"] == 7824
        and writer["writer_descriptor"]["row_bytes"] == 166912
        and writer["writer_descriptor"]["bytes_per_pixel"] == 16,
        f"{name}: writer descriptor",
    )
    log = case["log"].read_text(errors="replace")
    require("exited with status = 0" in log, f"{name}: incomplete process")
    require("Written:" in log and "(10432x7824)" in log, f"{name}: incomplete writer")
    print(
        f"{name}: OK unit={case['unit_hash'][:8]} orientation={case['orientation']} "
        f"sx={sx:.9g} sy={sy:.9g} roi=8320x6240 writer=10432x7824"
    )


def main():
    verify_static()
    verify_corpus()
    for name, case in CASES.items():
        verify_runtime(name, case)
    print("output_orientation_policy=PASS")


if __name__ == "__main__":
    main()
