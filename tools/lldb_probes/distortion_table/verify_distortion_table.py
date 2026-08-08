#!/usr/bin/env python3
"""Replay libcp's 4096-entry distortion table from public LRI calibration."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/"
    "Frameworks/libcp.dylib"
)
PUBLIC_PARSER = (
    ROOT
    / "tools/lldb_probes/state_448_later_box_formula"
    / "verify_distortion_public_origin.py"
)
EXPECTED_LIBCP_SHA256 = (
    "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
)
CASES = {
    "unit1_28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "unit2_70mm": Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
}
PUBLIC_CASES = {
    "unit1_28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "unit1_35mm": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
    "unit1_70mm": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
    "unit1_150mm": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
    "unit2_28mm": Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
    "unit2_35mm": Path("/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"),
    "unit2_70mm": Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
    "unit2_150mm": Path("/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri"),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_public_parser():
    spec = importlib.util.spec_from_file_location(
        "distortion_public_origin_for_table", PUBLIC_PARSER
    )
    require(spec is not None and spec.loader is not None, "cannot load parser")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def add(a, b):
    return f32(f32(a) + f32(b))


def sub(a, b):
    return f32(f32(a) - f32(b))


def mul(a, b):
    return f32(f32(a) * f32(b))


def div(a, b):
    return f32(f32(a) / f32(b))


def word_float(word):
    return struct.unpack("<f", struct.pack("<I", word))[0]


def public_records(parser, schema, path):
    polynomial, geometry_sha = parser.public_polynomials(schema, path)
    pixel_sizes = {}
    cra_present = set()
    for _block_index, payload in schema.walk_lri_payloads(path):
        top = schema.fields_by_number(payload)
        for wire_type, raw_calibration in top.get(13, []):
            if wire_type != 2:
                continue
            calibration = schema.fields_by_number(raw_calibration)
            if 3 not in calibration:
                continue
            camera = int(parser.one_raw(calibration, 1, 0))
            geometry = schema.fields_by_number(
                parser.one_raw(calibration, 3, 2)
            )
            distortion = schema.fields_by_number(
                parser.one_raw(geometry, 3, 2)
            )
            cra = schema.fields_by_number(parser.one_raw(distortion, 2, 2))
            pixel_sizes[camera] = word_float(
                struct.unpack("<I", parser.one_raw(cra, 4, 5))[0]
            )
            cra_present.add(camera)
    require(sorted(polynomial) == list(range(16)), f"{path}: polynomial set")
    require(sorted(cra_present) == list(range(16)), f"{path}: CRA set")
    for camera, record in polynomial.items():
        require(
            len(record["coeff_words"]) == 5,
            f"{path}: camera {camera} coefficient count",
        )
        require(
            record["coeff_words"][2:4] == [0, 0],
            f"{path}: camera {camera} nonzero tangential coefficients",
        )
    return polynomial, pixel_sizes, geometry_sha


def state_from_public(record):
    center_x, center_y, norm_x, norm_y = [
        word_float(word) for word in record["center_normalization_words"]
    ]
    coeff = [word_float(word) for word in record["coeff_words"]]
    return {
        "norm_x": norm_x,
        "norm_y": norm_y,
        "center_x": center_x,
        "center_y": center_y,
        "k1": coeff[0],
        "k2": coeff[1],
        "k3": coeff[4],
        "p1": coeff[2],
        "p2": coeff[3],
        "inverse": (
            div(1.0, norm_x),
            0.0,
            -div(center_x, norm_x),
            0.0,
            div(1.0, norm_y),
            -div(center_y, norm_y),
            0.0,
            0.0,
            1.0,
        ),
    }


def brown_conrady(state, x, y):
    matrix = state["inverse"]
    nx_num = add(add(mul(matrix[0], x), mul(matrix[1], y)), matrix[2])
    ny_num = add(add(mul(matrix[3], x), mul(matrix[4], y)), matrix[5])
    denominator = add(
        add(mul(matrix[6], x), mul(matrix[7], y)), matrix[8]
    )
    reciprocal = div(1.0, denominator)
    nx = mul(nx_num, reciprocal)
    ny = mul(ny_num, reciprocal)

    x2 = mul(nx, nx)
    y2 = mul(ny, ny)
    radius2 = add(x2, y2)
    twice_xy = mul(add(nx, nx), ny)
    radial = add(mul(state["k3"], radius2), state["k2"])
    radial = add(mul(radial, radius2), state["k1"])
    radial = add(mul(radial, radius2), 1.0)

    xd = mul(nx, radial)
    xd = add(mul(twice_xy, state["p1"]), mul(add(add(x2, x2), radius2), state["p2"]))
    xd = add(xd, mul(nx, radial))

    yd = mul(ny, radial)
    yd = add(
        mul(add(add(y2, y2), radius2), state["p1"]),
        mul(twice_xy, state["p2"]),
    )
    yd = add(yd, mul(ny, radial))
    return (
        add(mul(xd, state["norm_x"]), state["center_x"]),
        add(mul(yd, state["norm_y"]), state["center_y"]),
    )


def correction_samples(state, pixel_size):
    inverse_scale = div(1.0, pixel_size)
    radii = []
    corrections = []
    for index in range(30):
        radius = mul(f32(index), f32(0.1))
        x = add(mul(radius, inverse_scale), state["center_x"])
        output_x, _output_y = brown_conrady(state, x, state["center_y"])
        distorted_radius = mul(
            sub(output_x, state["center_x"]), pixel_size
        )
        radii.append(radius)
        corrections.append(sub(distorted_radius, radius))
    return radii, corrections


def lagrange_table(radii, corrections, pixel_size):
    step = div(sub(radii[-1], radii[0]), f32(len(radii) - 1))
    table = [f32(1.0)]
    for output_index in range(1, 4096):
        radius = min(mul(f32(output_index), pixel_size), radii[-1])
        position = div(sub(radius, radii[0]), step)
        index = int(position)
        index = min(index, len(radii) - 3)
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

        value = add(
            mul(w0, corrections[index]),
            mul(w1, corrections[index + 1]),
        )
        value = mul(value, shared)
        value = add(value, mul(wm1, corrections[index - 1]))
        value = add(value, mul(w2, corrections[index + 2]))
        table.append(add(div(value, radius), 1.0))
    return table


def packed_floats(values):
    return b"".join(struct.pack("<f", value) for value in values)


def verify_static():
    blob = LIBCP.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    require(digest == EXPECTED_LIBCP_SHA256, "installed libcp SHA-256")
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    windows = (
        (0x131720, 0x131D90),
        (0x133CB0, 0x133DE9),
        (0xE810, 0xEA84),
        (0xEA90, 0xF0EA),
        (0x145590, 0x1457BB),
        (0x144A70, 0x144DE3),
        (0x3E42E0, 0x3E4400),
    )
    signatures = set()
    for start, end in windows:
        signatures.update(
            (ins.address, ins.mnemonic, ins.op_str)
            for ins in md.disasm(blob[start:end], start)
        )
    required = {
        (0x1317E8, "mov", "ecx, dword ptr [r14 + 0x58]"),
        (0x131A66, "call", "0x133a20"),
        (0x133D47, "mov", "edx, dword ptr [r14 + 0x10]"),
        (0x133D4B, "mov", "dword ptr [rbx + 0x10], edx"),
        (0xE9FD, "mulss", "xmm6, xmm7"),
        (0xEA0A, "addss", "xmm6, dword ptr [rsi + 0x14]"),
        (0xEA21, "movss", "xmm9, dword ptr [rsi + 0x24]"),
        (0xF0AB, "mov", "rax, qword ptr [r14]"),
        (0xF0B0, "mov", "dword ptr [r13 + 0x14], ecx"),
        (0xF0CF, "movss", "xmm0, dword ptr [rax + 0x10]"),
        (0xF0D4, "movss", "dword ptr [r13 + 0x1c], xmm0"),
        (0x145758, "mulss", "xmm0, dword ptr [rip + 0x4800a0]"),
        (0x1457B5, "cmp", "r15, 0x1e"),
        (0x144D39, "cvttss2si", "esi, xmm5"),
        (0x144DCE, "movss", "dword ptr [rcx + rdx*4], xmm6"),
        (0x144DD6, "cmp", "rdx, 0x1000"),
    }
    missing = required - signatures
    require(not missing, f"missing static signatures: {sorted(missing)!r}")
    polynomial_conversion = list(
        md.disasm(blob[0x131B62:0x131D96], 0x131B62)
    )
    require(
        any(
            ins.address == 0x131B99
            and ins.mnemonic == "test"
            and ins.op_str == "byte ptr [r13 + 0x10], 8"
            for ins in polynomial_conversion
        ),
        "fit_cost presence-bit conversion anchor",
    )
    require(
        not any("[r13 + 0x50]" in ins.op_str for ins in polynomial_conversion),
        "valid_roi unexpectedly consumed by polynomial conversion",
    )
    return {"binary_sha256": digest, "static_signature_count": len(signatures)}


def verify_case(label, path, parser, schema):
    public, pixel_sizes, geometry_sha = public_records(parser, schema, path)
    runtime_path = ROOT / "runs/distortion_table" / f"{label}.json"
    runtime = json.loads(runtime_path.read_text())
    require(not runtime["errors"], f"{label}: runtime errors")
    key = runtime["pre"]["camera_key_object_0x60"]
    pixel_size = pixel_sizes[key]
    require(
        struct.pack("<f", pixel_size)
        == struct.pack("<f", runtime["pre"]["table_scalar_rbp_minus_b4"]),
        f"{label}: public CRA.pixel_size mismatch",
    )
    require(
        struct.pack("<f", pixel_size)
        == struct.pack("<f", runtime["sample_scale"]["forward_scale_rbp_minus_13c"]),
        f"{label}: sample forward scale mismatch",
    )
    require(
        struct.pack("<f", div(1.0, pixel_size))
        == struct.pack("<f", runtime["sample_scale"]["inverse_scale_rbp_minus_140"]),
        f"{label}: sample inverse scale mismatch",
    )

    state = state_from_public(public[key])
    radii, corrections = correction_samples(state, pixel_size)
    runtime_radii = runtime["pre"]["uniform_radius_samples_rbp_minus_58"]["values"]
    runtime_corrections = runtime["pre"]["distorted_radius_samples_rbp_minus_70"]["values"]
    require(
        packed_floats(radii) == packed_floats(runtime_radii),
        f"{label}: 30 uniform radii mismatch",
    )
    require(
        packed_floats(corrections) == packed_floats(runtime_corrections),
        f"{label}: 30 Brown-Conrady corrections mismatch",
    )

    table = lagrange_table(radii, corrections, pixel_size)
    runtime_table = runtime["post"]["table"]
    table_bytes = packed_floats(table)
    require(
        table_bytes == bytes.fromhex(runtime_table["raw_hex"]),
        f"{label}: 4096-entry table mismatch",
    )
    require(
        hashlib.sha256(table_bytes).hexdigest() == runtime_table["sha256"],
        f"{label}: table SHA-256 mismatch",
    )
    return {
        "camera_key": key,
        "geometry_sha256": geometry_sha,
        "pixel_size": pixel_size,
        "coefficient_order": ["k1", "k2", "p1", "p2", "k3"],
        "table_sha256": runtime_table["sha256"],
        "table_min": min(table),
        "table_max": max(table),
    }


def main():
    parser = load_public_parser()
    schema = parser.load_schema_module()
    result = {
        "status": "PASS",
        "static": verify_static(),
        "public_corpus": {},
        "cases": {},
    }
    for label, path in PUBLIC_CASES.items():
        records, pixel_sizes, geometry_sha = public_records(
            parser, schema, path
        )
        result["public_corpus"][label] = {
            "geometry_sha256": geometry_sha,
            "camera_count": len(records),
            "coefficient_counts": sorted(
                {len(record["coeff_words"]) for record in records.values()}
            ),
            "pixel_sizes": sorted(set(pixel_sizes.values())),
            "all_tangential_zero": all(
                record["coeff_words"][2:4] == [0, 0]
                for record in records.values()
            ),
        }
    for label, path in CASES.items():
        result["cases"][label] = verify_case(
            label, path, parser, schema
        )
    report = ROOT / "runs/distortion_table/verification.json"
    report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
