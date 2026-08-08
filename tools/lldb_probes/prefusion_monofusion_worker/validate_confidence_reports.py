#!/usr/bin/env python3
"""Validate MonoFusion's secondary confidence callback runtime packets."""

from __future__ import annotations

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs/prefusion_monofusion_worker"
REPORTS = (
    RUNS / "confidence_unit1_35mm.json",
    RUNS / "confidence_unit2_28mm.json",
)
EXPECTED_TYPE = (
    "NSt3__110__function6__funcIZN2lt10MonoFusion10initializeEPKbE3$_0"
    "NS_9allocatorIS6_EEFfffEEE"
)
R = 2.3183400630950928
N = 1.0
C = 4.0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> bytes:
    return struct.pack("<f", value)


def expected_parameters() -> tuple[float, float, float, float]:
    denominator = f32(f32(N * R) + C)
    alpha = f32(C / denominator)
    one_minus_alpha = f32(1.0 - alpha)
    inverse_n = f32(1.0 / N)
    confidence_scale = f32(one_minus_alpha * one_minus_alpha)
    confidence_scale = f32(confidence_scale * C)
    confidence_denominator = f32(N * N)
    confidence_denominator = f32(confidence_denominator * R)
    confidence_scale = f32(confidence_scale / confidence_denominator)
    return alpha, one_minus_alpha, inverse_n, confidence_scale


def callback(parameters: list[float], x: float, y: float) -> float:
    p0, p1, p2, p3 = parameters
    term = f32(p1 * x)
    term = f32(term * p2)
    term = f32(term + p0)
    term = f32(term * term)
    confidence_term = f32(p3 * y)
    return f32(term + confidence_term)


def main() -> None:
    expected = expected_parameters()
    for path in REPORTS:
        report = json.loads(path.read_text())
        calls = report["confidence_callback_calls"]
        require(calls, f"{path}: no confidence callback calls")
        for index, call in enumerate(calls):
            require(call["callback_va"] == 0x1B33A0, f"{path}:{index}: callback changed")
            require(call["type_name"] == EXPECTED_TYPE, f"{path}:{index}: RTTI changed")
            parameters = call["parameters"]
            require(parameters is not None, f"{path}:{index}: missing parameters")
            require(
                all(f32_bits(a) == f32_bits(b) for a, b in zip(parameters, expected)),
                f"{path}:{index}: parameter formula mismatch {parameters} != {expected}",
            )
            reproduced = callback(
                parameters,
                call["sum_one_minus_confidence"],
                call["sum_confidence_squared"],
            )
            require(
                f32_bits(reproduced) == f32_bits(call["result"]),
                f"{path}:{index}: callback mismatch {reproduced} != {call['result']}",
            )
        print(
            f"{path.stem}: calls={len(calls)} callback=0x1b33a0 "
            f"parameters={list(expected)} exact_float32=OK"
        )
    print("prefusion_monofusion_confidence_callback=OK")


if __name__ == "__main__":
    main()
