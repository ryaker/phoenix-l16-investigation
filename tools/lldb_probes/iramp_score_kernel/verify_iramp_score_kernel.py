#!/usr/bin/env python3
"""Verify the installed IRAMP two-scale patch-score formula and captured replay."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
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
RUN_DIR = ROOT / "runs/iramp_score_kernel/unit1_35mm"
REPLAY = ROOT / "runs/iramp_score_kernel/replay_36cde0"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("iramp_score_static_helpers", STATIC_PATH)


def range_hash(data: bytes, mapping, start: int, end: int) -> str:
    raw = STATIC.bytes_at(data, mapping, start, end - start)
    return hashlib.sha256(raw).hexdigest()


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def near(actual: float, expected: float, tolerance: float = 2e-6) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    expected_hashes = {
        (0x36CDE0, 0x36E530): (
            "0034cf0f5ed368bfffab8720465ce588cfc60d98c490547618ce732cb0872188"
        ),
        (0x371ED0, 0x3720AC): (
            "9e6618ba9efc4adacf8b2c8aace89ce1ee5074f7cea0be18f27f3cc3bc2e6a4e"
        ),
    }
    for (start, end), expected in expected_hashes.items():
        require(
            range_hash(data, mapping, start, end) == expected,
            f"static range 0x{start:x}..0x{end:x} changed",
        )

    constants = {
        0x5CBFC0: (1.0 / 256.0,) * 4,
        0x5CBFD0: (1.58613431,) * 4,
        0x5CBFE0: (3.17226863,) * 4,
        0x5CBFF0: (-0.0529801175,) * 4,
        0x5CC000: (-0.105960235,) * 4,
        0x5CC010: (-0.882911086,) * 4,
        0x5CC020: (-1.76582217,) * 4,
        0x5CC030: (1.14960444,) * 4,
        0x5CC040: (0.869864404,) * 4,
        0x5FDC50: (0.01, 0.03, 0.03, 1.0),
        0x5FDC60: (-0.8, -0.8, -0.8, -0.0),
        0x5FDC70: (5.26315784, 5.26315784, 5.26315784, 1.0),
        0x5FDB10: (-1.0 / 192.0, -1.0 / 96.0, -1.0 / 48.0, -1.0 / 24.0),
    }
    for va, expected in constants.items():
        actual = struct.unpack("<4f", STATIC.bytes_at(data, mapping, va, 16))
        require(
            all(f32_bits(a) == f32_bits(e) for a, e in zip(actual, expected)),
            f"constant vector at 0x{va:x} changed: {actual}",
        )

    opcode_guards = {
        0x36CE06: "e8c5500000",      # candidate L1 normalization
        0x36CEA6: "0f282d13f12500",  # fine statistics / 256
        0x36CF24: "0f294d80",        # fine structural score
        0x36D080: "f3410f10842440150000",  # fine reference detail
        0x36D08A: "f30f590d7e0a2900",      # detail weight -1/192
        0x36D0E1: "0f594580",        # fine structure * detail
        0x36D28A: "0f2805ef092900",  # coarse statistics / 64
        0x36D31B: "0f294d90",        # coarse structural score
        0x36D79C: "f3410f108c2450150000",  # coarse reference detail
        0x36D7A6: "f30f590566032900",      # detail weight -1/96
        0x36D7FD: "0f598d70ffffff",  # coarse structure * detail
        0x36E3F9: "0f284590",        # min4 coarse
        0x36E41A: "0f284d80",        # min4 fine
        0x36E511: "f30f59c1f30f51c0",  # sqrt(coarse * fine)
        0x371FC9: "0fc6c900f30f53c9",  # candidate lane-0 L1 reciprocal
    }
    for va, expected_hex in opcode_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    return digest


def verify_capture() -> tuple[float, float, float]:
    capture_path = RUN_DIR / "capture.json"
    stages_path = RUN_DIR / "stages.json"
    scratch_path = RUN_DIR / "scratch.bin"
    candidate_path = RUN_DIR / "candidate.bin"
    for path in (capture_path, stages_path, scratch_path, candidate_path):
        require(path.exists(), f"missing captured artifact {path}")

    capture = json.loads(capture_path.read_text())
    stages = json.loads(stages_path.read_text())
    require(not stages["errors"], f"stage errors: {stages['errors']}")
    require(capture["scratch_size"] == 0x2800, "scratch capture size")
    require(capture["candidate_size"] == 0x1000, "candidate capture size")
    require(scratch_path.stat().st_size == 0x2800, "scratch blob size")
    require(candidate_path.stat().st_size == 0x1000, "candidate blob size")
    require(capture["live_score_bits"] == 0x3EFA37BD, "live score bits changed")

    by_label = {event["label"]: event for event in stages["events"]}
    expected_labels = {
        "fine_structure",
        "fine_detail_input",
        "fine_detail_factor",
        "fine_combined",
        "coarse_structure",
        "coarse_detail_input",
        "coarse_detail_factor",
        "coarse_combined",
        "final_geometric_mean_inputs",
    }
    require(set(by_label) == expected_labels, "stage label set changed")

    fine_structure = by_label["fine_structure"]["xmm1"]
    fine_detail_input = by_label["fine_detail_input"]
    fine_detail = by_label["fine_detail_factor"]["xmm0"]
    fine_combined = by_label["fine_combined"]["xmm0"]
    coarse_structure = by_label["coarse_structure"]["xmm1"]
    coarse_detail_input = by_label["coarse_detail_input"]
    coarse_detail = by_label["coarse_detail_factor"]["xmm1"]
    coarse_combined = by_label["coarse_combined"]["xmm1"]

    require(near(fine_structure[0], 0.8430248499), "fine structure packet")
    require(fine_detail == [1.0, 1.0, 1.0, 1.0], "fine detail packet")
    fine_formula = max(
        0.0,
        min(
            1.0,
            1.0
            - 8.0
            * (
                fine_detail_input["reference_detail_0"]
                - fine_detail_input["xmm1"][0] / 192.0
            )
            / (fine_detail_input["reference_detail_0"] + 0.05),
        ),
    )
    require(near(fine_detail[0], fine_formula, 1e-5), "fine detail formula")
    require(
        all(near(a * b, c) for a, b, c in zip(fine_structure, fine_detail, fine_combined)),
        "fine structure/detail multiplication",
    )
    require(near(coarse_structure[0], 0.3364120722), "coarse structure packet")
    require(near(coarse_detail[0], 0.8421399593), "coarse detail packet")
    coarse_formula = max(
        0.0,
        min(
            1.0,
            1.0
            - 8.0
            * (
                coarse_detail_input["reference_detail_1"]
                - coarse_detail_input["xmm0"][0] / 96.0
            )
            / (coarse_detail_input["reference_detail_1"] + 0.05),
        ),
    )
    require(near(coarse_detail[0], coarse_formula, 1e-5), "coarse detail formula")
    require(
        all(
            near(a * b, c)
            for a, b, c in zip(coarse_structure, coarse_detail, coarse_combined)
        ),
        "coarse structure/detail multiplication",
    )

    final_event = by_label["final_geometric_mean_inputs"]
    coarse_min = min(final_event["xmm0"])
    fine_min = min(final_event["xmm1"])
    require(near(coarse_min, coarse_combined[0]), "coarse min4")
    require(near(fine_min, fine_combined[0]), "fine min4")
    expected_score = math.sqrt(coarse_min * fine_min)
    require(near(expected_score, capture["live_score"]), "geometric-mean score")
    return fine_min, coarse_min, capture["live_score"]


def verify_replay(live_score: float) -> None:
    require(REPLAY.exists(), f"missing replay executable {REPLAY}")
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
            str(RUN_DIR / "scratch.bin"),
            str(RUN_DIR / "candidate.bin"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    first = result.stdout.splitlines()[0]
    require(first.endswith("bits=0x3efa37bd"), f"replay mismatch: {first}")
    replay_score = float(first.split()[0].split("=")[1])
    require(f32_bits(replay_score) == f32_bits(live_score), "replay/live score bits")


def main() -> None:
    digest = verify_static()
    fine, coarse, live = verify_capture()
    verify_replay(live)
    print(f"iramp_score_static=OK libcp={digest}")
    print(f"fine_min={fine:.9g} coarse_min={coarse:.9g}")
    print(f"score=sqrt(fine_min*coarse_min)={live:.9g} bits=0x{f32_bits(live):08x}")
    print("iramp_score_kernel=OK")


if __name__ == "__main__":
    main()
