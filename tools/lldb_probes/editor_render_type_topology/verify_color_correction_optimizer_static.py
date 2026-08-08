#!/usr/bin/env python3
"""Verify installed-bundle anchors for the editor HSV-map optimizer."""

from __future__ import annotations

import json
import hashlib
import struct
from pathlib import Path


LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCERES = LIBCP.with_name("libceres.dylib")


def read(data: bytes, va: int, size: int) -> bytes:
    # This image maps __TEXT and file-backed __DATA with file offset == VM address.
    return data[va : va + size]


def require_bytes(data: bytes, va: int, expected: bytes, label: str) -> None:
    actual = read(data, va, len(expected))
    if actual != expected:
        raise AssertionError(
            f"{label}: 0x{va:x}: expected {expected.hex()}, got {actual.hex()}"
        )


def require_f32(data: bytes, va: int, expected: float, label: str) -> None:
    actual = struct.unpack_from("<f", data, va)[0]
    if actual != expected:
        raise AssertionError(f"{label}: 0x{va:x}: expected {expected}, got {actual}")


def require_f64(data: bytes, va: int, expected: float, label: str) -> None:
    actual = struct.unpack_from("<d", data, va)[0]
    if actual != expected:
        raise AssertionError(f"{label}: 0x{va:x}: expected {expected}, got {actual}")


def require_cstring(data: bytes, va: int, expected: bytes, label: str) -> None:
    actual = read(data, va, len(expected) + 1)
    if actual != expected + b"\0":
        raise AssertionError(f"{label}: 0x{va:x}: cstring mismatch")


def main() -> None:
    data = LIBCP.read_bytes()
    binary_sha256 = hashlib.sha256(data).hexdigest()
    if binary_sha256 != "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9":
        raise AssertionError(f"installed libcp changed: {binary_sha256}")
    libceres_data = LIBCERES.read_bytes()
    libceres_sha256 = hashlib.sha256(libceres_data).hexdigest()
    if libceres_sha256 != "dad91f3f2b05af8705b48eaa42e04aea15a5f4640528a922d2ae843c8b85bec6":
        raise AssertionError(f"installed libceres changed: {libceres_sha256}")
    if b"ceres-solver-1.12.0" not in libceres_data:
        raise AssertionError("bundled Ceres 1.12.0 build path missing")

    range_hashes = {
        "wrapper_113230_113720": (0x113230, 0x113720, "dc574caa5e54067da98e59c652c647a6cf227b77ee3d2d8f4f058e410f5acd4a"),
        "optimizer_116ee0_11ac30": (0x116EE0, 0x11AC30, "296194837f77e02ee4c01f383c355b7ce000eacbb528da2ea48d6948aa173ed6"),
        "tps_evaluator_11c4c0_11c770": (0x11C4C0, 0x11C770, "6bae868d91a7a9d524f0ef3f52d0bed1e55b40ca3b849f819a571304d35512c7"),
        "ciede2000_1273c0_127870": (0x1273C0, 0x127870, "98127d1b7f765be58307f79717e5aace8604b4613461922b90a0e9569b4ecc7a"),
    }
    for label, (begin, end, expected) in range_hashes.items():
        actual = hashlib.sha256(read(data, begin, end - begin)).hexdigest()
        if actual != expected:
            raise AssertionError(f"{label}: expected {expected}, got {actual}")

    require_cstring(
        data,
        0x5C3930,
        b"NSt3__110__function6__funcIZN2lt12_GLOBAL__N_114OptimizeHSVLutERKNS_6vectorINS2_4Vec3IfEENS_9allocatorIS6_EEEESB_RKNS2_10IlluminantEPS9_E3$_0NS7_ISG_EEFS6_RKS6_EEE",
        "OptimizeHSVLut grid callback RTTI",
    )

    require_bytes(data, 0x113249, bytes.fromhex("492b4760483d20010000"), "public 24-Vec3f wrapper input")
    require_bytes(data, 0x113300, bytes.fromhex("488d3599ac5500488dbd80feffff41b8010000004c89f24c89e1e8e171f9ff"), "reference table color conversion")
    require_bytes(data, 0x1133B4, bytes.fromhex("498d7760488dbd40feffff488d9580feffff488d8d30feffff4c8d8510feffff4531c9e8043b0000"), "wrapper OptimizeHSVLut call")
    require_cstring(
        data,
        0x5C38B0,
        b"N5ceres20AutoDiffCostFunctionIN2lt12_GLOBAL__N_115LabCostFunctionELi25ELi9ELi0ELi0ELi0ELi0ELi0ELi0ELi0ELi0ELi0EEE",
        "25-residual/9-parameter LabCostFunction RTTI",
    )

    # The optimizer accepts exactly 24 Vec3f calibration samples.
    require_bytes(data, 0x116F1D, bytes.fromhex("483d20010000"), "24-patch byte check")
    # It verifies a 3x3 solve and a 24-patch-plus-constraint (25-column) matrix.
    require_bytes(data, 0x117468, bytes.fromhex("4883f809"), "3x3 matrix check")
    require_bytes(data, 0x117472, bytes.fromhex("4883bdf8f5ffff19"), "25-column check")
    require_bytes(
        data,
        0x117189,
        bytes.fromhex("48ba8dedb5a0f7c6b03e"),
        "1e-6 stabilizer row",
    )
    require_bytes(data, 0x1172A1, bytes.fromhex("4ac7043000000000"), "zero stabilizer weight")
    require_bytes(
        data,
        0x1174CB,
        bytes.fromhex(
            "f30f1000f30f104804f30f10254c0c49000f28d4f30f5ed10f28dc"
            "f30f5cd9f30f5cd8f30f59c2f30f59da0f28ccf30f5ec80f28c4"
            "f30f5ec3f30f114b18c7431c0000803ff30f114320"
        ),
        "D50 reciprocal-white float32 construction",
    )
    require_bytes(
        data,
        0x11758F,
        bytes.fromhex(
            "c7857cfaffff00000000c78520faffff01000000c78550f9ffff00000000"
            "c78554f9ffff03000000c78558f9ffff01000000c68580faffff00"
            "c785b8f9ffffd00700000f280577bf4a000f118508faffff"
            "c785c8f9ffff01000000"
        ),
        "Ceres line-search option writes",
    )
    require_f64(data, 0x5C3550, 1e-10, "Ceres function tolerance")
    require_f64(data, 0x5C3558, 1.0000000000000002e-14, "Ceres gradient tolerance")

    # The map descriptor is written as {hue=32, saturation=32, value=1}.
    require_bytes(
        data,
        0x118193,
        bytes.fromhex("48b82000000020000000"),
        "32x32 descriptor pair",
    )
    require_bytes(
        data,
        0x11819D,
        bytes.fromhex("48898530feffffc78538feffff01000000"),
        "descriptor write and value dimension",
    )
    require_bytes(data, 0x11974A, bytes.fromhex("e8414c0200"), "HSVMap constructor call")

    # Grid generation calls the optimizer lambda for every HSV lattice point.
    require_bytes(data, 0x13E1E0, bytes.fromhex("488b06488b4030"), "grid callback dispatch")
    require_f32(data, 0x5A8124, -1.0, "map lower clamp")
    require_f32(data, 0x5A8128, 1.0, "unity and hue-wrap offset")
    upper = struct.unpack_from("<4f", data, 0x5C51F0)
    if upper != (1.0, 2.0, 2.0, 0.0):
        raise AssertionError(f"map upper clamp: expected (1,2,2,0), got {upper}")

    # The callback evaluates three thin-plate splines. Each begins with affine
    # coefficients at N..N+2 and adds coefficient[i] * r^2 * log10(r).
    require_bytes(data, 0x11C533, bytes.fromhex("f2410f101404"), "affine constant load")
    require_bytes(data, 0x11C5F0, bytes.fromhex("f30f1043fcf30f1013"), "control point load")
    require_bytes(data, 0x11C602, bytes.fromhex("f30f59c0f30f59d2f30f58d0f30f51d2"), "distance formula")
    require_bytes(data, 0x11C63D, bytes.fromhex("e8ae994300"), "log10 import call")
    require_bytes(data, 0x11C65F, bytes.fromhex("f20f594588"), "r squared times log10(r)")
    require_f64(data, 0x5C38A0, 0.0001, "low-saturation guard")
    require_bytes(
        data,
        0x11CCD2,
        bytes.fromhex("41c746080000803f"),
        "low-saturation value-scale unity",
    )
    correspondence_clamps = struct.unpack_from("<6f", data, 0x5C3530)
    expected_clamps = (-1.0 / 36.0, 0.9, 0.975, 1.0 / 36.0, 1.1, 1.025)
    for actual, expected in zip(correspondence_clamps, expected_clamps):
        if abs(actual - expected) > 3e-8:
            raise AssertionError(
                f"HSV correspondence clamp: expected {expected}, got {actual}"
            )
    require_bytes(data, 0x11838B, bytes.fromhex("4883f912"), "18 chromatic patch cap")
    require_f64(data, 0x5A8138, 1.0 / 6.0, "boundary hue step")
    require_f64(data, 0x5C3700, 0.001500000013038516, "TPS smoothing multiplier")
    require_bytes(data, 0x35091B, bytes.fromhex("4889f34989fe488d7de84889d6e8b3a9d5fff30f1045e8f30f100bf30f105304488d7358488d537c4c89f7e8d5add5ff"), "matrix CCT and ab720 interpolation")
    require_bytes(data, 0x13E45C, bytes.fromhex("f30f101dc49c4600f30f5cd80fc6db00498b77100fc6c00048c1fa0431ff660f1f4400000f28090f59cb0f28160f59d00f58d10f291048ff"), "HSV-map SIMD interpolation order")
    require_bytes(data, 0xAB940, bytes.fromhex("554889e54157415641554154534881eca800000044898d34"), "linear matrix converter")
    require_bytes(data, 0x9D7E0, bytes.fromhex("554889e58b46208947200f10060f104e"), "3x3 inverse helper")

    report = {
        "binary": str(LIBCP),
        "binary_sha256": binary_sha256,
        "libceres_sha256": libceres_sha256,
        "ceres_version": "1.12.0",
        "range_hashes": {label: expected for label, (_begin, _end, expected) in range_hashes.items()},
        "optimizer": "0x116ee0",
        "public_input_count": 24,
        "chromatic_control_count": 18,
        "periodic_tps_control_count": 126,
        "stabilizer_row": [1e-6, 1e-6, 1e-6],
        "stabilizer_residual_weight": 0.0,
        "hsv_correspondence_clamps": list(correspondence_clamps),
        "lab_cost": {"residuals": 25, "parameters": 9},
        "ceres_options": {
            "minimizer_type": "LINE_SEARCH",
            "line_search_direction_type": "BFGS",
            "line_search_type": "WOLFE",
            "linear_solver_type": "DENSE_QR",
            "max_num_iterations": 2000,
            "function_tolerance": 1e-10,
            "gradient_tolerance": 1.0000000000000002e-14,
            "num_threads": 1,
        },
        "wrapper_endpoint_formula": "M * diag(inverse(M) * D50_XYZ)",
        "hsv_map_dimensions": [32, 32, 1],
        "padded_vec4_cells": 33 * 33,
        "tps_radial_basis": "r^2 * log10(r), phi(0)=0",
        "tps_smoothing": "0.001500000013038516 * mean_pair_distance^2",
        "tps_affine_tail": "a0 + a1*hue + a2*saturation",
        "low_saturation_guard": 0.0001,
        "map_upper_clamp": list(upper),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
