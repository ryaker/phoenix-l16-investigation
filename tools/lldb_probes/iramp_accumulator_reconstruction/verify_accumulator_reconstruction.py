#!/usr/bin/env python3
"""Verify IRAMP scale normalization and inverse 9/7 accumulator reconstruction."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
RUN_ROOT = ROOT / "runs/iramp_accumulator_reconstruction"
REPLAY = RUN_ROOT / "replay_36e530"
ANALYZER = (
    ROOT
    / "tools/lldb_probes/iramp_accumulator_reconstruction"
    / "analyze_transform_basis.py"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("iramp_reconstruction_static_helpers", STATIC_PATH)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def trailing_zeros(value: int) -> int:
    return 4 if value == 0 else (value & -value).bit_length() - 1


def expected_selector() -> bytes:
    return bytes(
        min(trailing_zeros(x), trailing_zeros(y), 4)
        for y in range(16)
        for x in range(16)
    )


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    body = STATIC.bytes_at(data, mapping, 0x36E530, 0x36F7F4 - 0x36E530)
    require(
        hashlib.sha256(body).hexdigest()
        == "ceb0993f9f371e9bc3e19309feb107c8b9c7a1eec5365ee9daf1f30e07b92ccc",
        "0x36e530 body changed",
    )

    constants = {
        0x5CBFD0: 1.58613431,
        0x5CBFE0: 3.17226863,
        0x5CBFF0: -0.0529801175,
        0x5CC000: -0.105960235,
        0x5CC010: -0.882911086,
        0x5CC020: -1.76582217,
        0x5CC030: 1.14960444,
        0x5CC040: 0.869864404,
        0x5FDC90: 1.01971495,
        0x5FDCA0: 0.509857476,
    }
    for va, expected in constants.items():
        actual = struct.unpack("<4f", STATIC.bytes_at(data, mapping, va, 16))
        require(
            all(f32_bits(value) == f32_bits(expected) for value in actual),
            f"lifting constant at 0x{va:x} changed",
        )

    guards = {
        0x36E530: "0f538780250000",
        0x36E568: "0f5387c0250000",
        0x36E5A0: "0fb650ff48c1e204",
        0x36E5A8: "0f28841780250000",
        0x36E5B0: "0f5941f0",
        0x36E5EF: "55",
        0x36ED01: "488d8780150000",
        0x36F3F0: "4881c100010000",
        0x36F623: "4883c110",
        0x36F7F3: "c3",
    }
    for va, expected_hex in guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")
    return digest


def verify_capture(name: str, expected_normalizers: tuple[float, ...]) -> None:
    directory = RUN_ROOT / name
    capture = json.loads((directory / "capture.json").read_text())
    before = (directory / "before.bin").read_bytes()
    after = (directory / "after.bin").read_bytes()
    require(len(before) == len(after) == 0x2800, f"{name}: scratch size")
    require(capture["return_offset"] == 0x1580, f"{name}: return offset")
    require(capture["first_changed_offset"] == 0x1580, f"{name}: first change")
    require(capture["last_changed_offset"] == 0x25CF, f"{name}: last change")
    require(before[0x25D0:0x26D0] == expected_selector(), f"{name}: selectors")

    normalizers = struct.unpack_from("<20f", before, 0x2580)
    require(
        all(
            f32_bits(normalizers[scale * 4 + lane])
            == f32_bits(expected_normalizers[scale])
            for scale in range(5)
            for lane in range(4)
        ),
        f"{name}: normalizer vectors",
    )

    env = os.environ.copy()
    framework = (
        "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
    )
    env["DYLD_FRAMEWORK_PATH"] = framework
    env["DYLD_LIBRARY_PATH"] = framework
    result = subprocess.run(
        [
            "arch",
            "-x86_64",
            str(REPLAY),
            str(directory / "before.bin"),
            str(directory / "after.bin"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    require("mismatched_bytes=0" in result.stdout, f"{name}: replay mismatch")
    print(
        f"{name}: OK normalizers="
        + ",".join(f"{value:.9g}" for value in expected_normalizers)
    )


def verify_basis() -> None:
    path = RUN_ROOT / "transform_basis.bin"
    require(path.exists(), "missing transform basis output")
    result = subprocess.run(
        ["python3", str(ANALYZER), str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    require(
        "basis_exact_float_bits=65536/65536" in result.stdout,
        "basis float-bit coverage",
    )
    require("basis_max_abs_error=0" in result.stdout, "basis formula mismatch")
    print("inverse97_basis=OK exact_float_bits=65536/65536")


def main() -> None:
    digest = verify_static()
    verify_capture("unit1_35mm", (0.2, 0.2, 0.2, 0.2, 0.2))
    verify_capture(
        "unit1_35mm_nonbaseline",
        (1.06253981590271, 0.9859229922294617, 0.6156874895095825, 0.2, 0.2),
    )
    verify_basis()
    print(f"iramp_accumulator_reconstruction_static=OK libcp={digest}")
    print("selector=min(v2(x),v2(y),4)")
    print("inverse97=strides_8_4_2_1_horizontal_then_vertical_symmetric")
    print("iramp_accumulator_reconstruction=OK")


if __name__ == "__main__":
    main()
