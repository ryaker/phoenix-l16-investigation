#!/usr/bin/env python3
"""Verify MonoFusion's exact response-basis scalar replacement wrapper."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs/prefusion_monofusion_color_wrapper"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_static():
    spec = importlib.util.spec_from_file_location("monofusion_wrapper_static", STATIC_PATH)
    require(spec is not None and spec.loader is not None, f"cannot import {STATIC_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_static()
F = np.float32


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def same_bits(actual, expected, message: str) -> None:
    require(bits(actual) == bits(expected), f"{message}: {actual!r} != {expected!r}")


def response_basis(values: list[float]) -> list[np.float32]:
    a, b, c = map(F, values)
    neg_b = F(-b)
    ac = F(c + a)

    n0 = F(math.sqrt(float(F(F(c * c) + F(F(a * a) + F(b * b))))))
    two_b2 = F(F(b * b) + F(b * b))
    n1 = F(math.sqrt(float(F(two_b2 + F(ac * ac)))))

    u = F(F(b * neg_b) - F(ac * c))
    v = F(F(c - a) * neg_b)
    w = F(F(ac * a) - F(b * neg_b))
    n2 = F(math.sqrt(float(F(F(w * w) + F(F(v * v) + F(u * u))))))
    inv_n2 = F(F(1.0) / n2)

    # 0xab830 initially normalizes row 0 by n0. Constructor 0x1b14cb then
    # deliberately restores the three unnormalized response coefficients.
    return [
        a,
        b,
        c,
        F(neg_b / n1),
        F(ac / n1),
        F(neg_b / n1),
        F(u * inv_n2),
        F(v * inv_n2),
        F(w * inv_n2),
    ]


def inverse3(m: list[float]) -> list[np.float32]:
    a, b, c, d, e, f, g, h, i = map(F, m)
    c00 = F(F(i * e) - F(f * h))
    c01n = F(F(b * i) - F(c * h))
    c02 = F(F(b * f) - F(c * e))
    c10n = F(F(d * i) - F(g * f))
    c11 = F(F(a * i) - F(c * g))
    c12n = F(F(a * f) - F(c * d))
    c20 = F(F(d * h) - F(g * e))
    c21n = F(F(a * h) - F(g * b))
    c22 = F(F(a * e) - F(b * d))
    determinant = F(F(c20 * c) + F(F(c00 * a) - F(c10n * b)))
    inv_det = F(F(1.0) / determinant)
    return [
        F(c00 * inv_det), F(-F(c01n * inv_det)), F(c02 * inv_det),
        F(-F(c10n * inv_det)), F(c11 * inv_det), F(-F(c12n * inv_det)),
        F(c20 * inv_det), F(-F(c21n * inv_det)), F(c22 * inv_det),
    ]


def replay_pixel(p, mono, black, span, forward, inverse):
    p = list(map(F, p))
    mono = F(mono)
    m = list(map(F, forward))
    n = list(map(F, inverse))
    q = []
    for row in range(3):
        q.append(F(F(p[2] * m[3 * row + 2]) + F(F(p[1] * m[3 * row + 1]) + F(p[0] * m[3 * row]))))
    scale = F(F(1.0) / F(span))
    s = F(F(mono - F(black)) * scale)
    out = []
    for row in range(3):
        out.append(F(F(F(q[2] * n[3 * row + 2]) + F(q[1] * n[3 * row + 1])) + F(s * n[3 * row])))
    return out + [p[3]]


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    windows = {
        (0x1B1360, 0x1B1528): "607207b5e26b0c3f3f6f8bb7ce86db5bbb2b2f2cc4883f867421fef46ebb2360",
        (0x1B3530, 0x1B375C): "61dfd8999ea456a4e92e97635de2357d729f5e7c40177577822c242a13bbef13",
        (0x09D7E0, 0x09D96A): "09dc1b8297117595002c0e07aa93915064b049d013e82e1dd5d7f74843acab2a",
        (0x0AB830, 0x0AB93B): "193603b136bb189fef0a7aa96cd9e95fbc5bdbb032555ae2fe621663d9ee047d",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")
        print(f"sha256_0x{start:x}_0x{end:x}={actual}")
    return digest


def verify_report(name: str) -> None:
    path = RUNS / f"{name}.json"
    require(path.is_file(), f"missing {path}")
    report = json.loads(path.read_text())
    require(not report["errors"], f"{name}: probe errors {report['errors']}")
    entry = report["entry"]
    require(entry is not None, f"{name}: missing entry")
    payload = entry["normalization_payload"]
    require(
        payload
        == {
            "sensor_type": 2,
            "black_level": 42.0,
            "white_level": 1023.0,
            "cliff_slope": 2.0,
        },
        f"{name}: normalization payload {payload}",
    )
    require(entry["normalization_span_0xf8"] == 981.0, f"{name}: span")
    response = entry["response_0x100"]
    expected_response = [
        0.2155500054359436,
        0.43230700492858887,
        0.35214298963546753,
        0.0,
    ]
    for index, expected in enumerate(expected_response):
        same_bits(response[index], expected, f"{name}: response[{index}]")

    expected_forward = response_basis(response[:3])
    forward = entry["forward_matrix_0x114"]
    inverse = entry["inverse_matrix_0x138"]
    expected_inverse = inverse3(forward)
    for index in range(9):
        same_bits(forward[index], expected_forward[index], f"{name}: forward[{index}]")
        same_bits(inverse[index], expected_inverse[index], f"{name}: inverse[{index}]")

    tile = report["tile"]
    require(tile is not None and len(tile["samples"]) == 3, f"{name}: samples")
    for sample_index, sample in enumerate(tile["samples"]):
        expected = replay_pixel(
            sample["pre_rgba"],
            sample["fused_scalar"],
            payload["black_level"],
            entry["normalization_span_0xf8"],
            forward,
            inverse,
        )
        for channel in range(4):
            same_bits(
                sample["post_rgba"][channel],
                expected[channel],
                f"{name}: sample {sample_index} channel {channel}",
            )
    print(f"{name}=OK matrix_words=18/18 pixel_words=12/12")


def main() -> None:
    digest = verify_static()
    for name in ("unit1_28mm", "unit2_28mm"):
        verify_report(name)
    print(f"monofusion_color_wrapper=OK libcp={digest}")
    print("scope=exact-28mm Unit-1+Unit-2; wide-only wrapper; tele route absent")


if __name__ == "__main__":
    main()
