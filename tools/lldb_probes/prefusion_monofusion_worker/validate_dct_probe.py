#!/usr/bin/env python3
"""Fingerprint the installed 16x16 MonoFusion transform pair."""

from __future__ import annotations

import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "runs/prefusion_monofusion_worker/dct_probe.txt"
SIDE = 16


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse() -> dict[str, object]:
    result: dict[str, object] = {}
    for line in REPORT.read_text().splitlines():
        key, value = line.split("=", 1)
        if "," in value:
            result[key] = [float(item) for item in value.split(",")]
        else:
            result[key] = float(value)
    return result


def candidate_impulse(x: int, y: int) -> list[float]:
    values = []
    for v in range(SIDE):
        cv = math.sqrt(1.0 / SIDE) if v == 0 else math.sqrt(2.0 / SIDE)
        for u in range(SIDE):
            cu = math.sqrt(1.0 / SIDE) if u == 0 else math.sqrt(2.0 / SIDE)
            values.append(
                cu
                * cv
                * math.cos(math.pi * (2 * x + 1) * u / (2 * SIDE))
                * math.cos(math.pi * (2 * y + 1) * v / (2 * SIDE))
            )
    return values


def maximum_error(actual: list[float], expected: list[float]) -> float:
    return max(abs(a - b) for a, b in zip(actual, expected))


report = parse()
constant = report["constant_forward"]
impulse00 = report["impulse00_forward"]
impulse01 = report["impulse01_forward"]
require(isinstance(constant, list) and len(constant) == SIDE * SIDE, "constant matrix")
require(isinstance(impulse00, list) and len(impulse00) == SIDE * SIDE, "impulse00 matrix")
require(isinstance(impulse01, list) and len(impulse01) == SIDE * SIDE, "impulse01 matrix")

expected_constant = [0.0] * (SIDE * SIDE)
expected_constant[0] = float(SIDE)
constant_error = maximum_error(constant, expected_constant)
impulse00_error = maximum_error(impulse00, candidate_impulse(0, 0))
impulse01_error = maximum_error(impulse01, candidate_impulse(1, 0))

require(constant_error < 2e-5, f"constant DCT mismatch {constant_error}")
require(impulse00_error > 0.5, "plain row-major orthonormal DCT-II was not refuted")
require(impulse01_error > 0.5, "plain row-major orthonormal DCT-II was not refuted")
fingerprint = {
    "impulse00[0]": (impulse00[0], 0.191406429),
    "impulse00[1]": (impulse00[1], -0.375),
    "impulse00[2]": (impulse00[2], -0.5),
    "impulse00[16]": (impulse00[16], -0.37499997),
    "impulse01[0]": (impulse01[0], 0.273437619),
    "impulse01[1]": (impulse01[1], 0.75),
    "impulse01[4]": (impulse01[4], -0.3125),
}
for label, (actual, expected) in fingerprint.items():
    require(abs(actual - expected) < 2e-6, f"{label} fingerprint changed")
for key in (
    "constant_roundtrip_max_error",
    "impulse00_roundtrip_max_error",
    "impulse01_roundtrip_max_error",
):
    require(float(report[key]) < 2e-6, f"{key} too large: {report[key]}")

print(
    "prefusion_monofusion_transform=OK "
    f"constant_error={constant_error:.3g} "
    f"plain_dct_impulse00_error={impulse00_error:.3g} "
    f"plain_dct_impulse01_error={impulse01_error:.3g}"
)
print("transform=installed_factorized_16x16_forward_inverse_pair")
print("plain_row_major_orthonormal_DCT_II=REFUTED")
