#!/usr/bin/env python3
"""Verify libcp+0x190da0's float32 quadratic subpixel fit."""

import argparse
import hashlib
import json
import struct
from pathlib import Path


EXPECTED_LIBCP_SHA256 = (
    "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def add(left, right):
    return f32(f32(left) + f32(right))


def sub(left, right):
    return f32(f32(left) - f32(right))


def mul(left, right):
    return f32(f32(left) * f32(right))


def div(left, right):
    return f32(f32(left) / f32(right))


def bits(value):
    return struct.pack("<f", f32(value)).hex()


def quadratic_fit(samples):
    a0, a1, a2, a3, a4, a5, a6, a7, a8 = map(f32, samples)

    # Preserve the scalar SSE operation order at libcp+0x190ddb..0x190e8c.
    hyy = mul(a0, 4.0)
    hyy = sub(hyy, mul(a1, 8.0))
    hyy = add(mul(a2, 4.0), hyy)
    hyy = add(hyy, mul(a3, 8.0))
    hyy = add(hyy, mul(a4, -16.0))
    hyy = add(hyy, mul(a5, 8.0))
    hyy = add(hyy, mul(a6, 4.0))
    hyy = sub(hyy, mul(a7, 8.0))
    hyy = add(hyy, mul(a8, 4.0))
    hyy = max(f32(0.0), hyy)

    hxx = mul(add(a7, a1), 8.0)
    hxx_work = mul(add(a2, a0), 4.0)
    hxx_work = sub(hxx_work, mul(a3, 8.0))
    hxx_work = sub(hxx_work, mul(a5, 8.0))
    hxx_work = add(hxx_work, mul(a6, 4.0))
    hxx_work = add(hxx_work, mul(a8, 4.0))
    hxx_work = add(hxx_work, mul(a4, -16.0))
    hxx = add(hxx_work, hxx)
    hxx = max(f32(0.0), hxx)

    hxy = mul(add(sub(sub(a0, a2), a6), a8), 4.0)
    determinant = sub(mul(hxx, hyy), mul(hxy, hxy))
    if not f32(0.0) < determinant:
        hxy = f32(0.0)
    determinant = sub(mul(hxx, hyy), mul(hxy, hxy))
    if determinant == f32(0.0):
        return [f32(0.0), f32(0.0)]

    gy = mul(a0, -2.0)
    a2_twice = add(a2, a2)
    gy = add(gy, a2_twice)
    gy = sub(gy, mul(a3, 4.0))
    gy = add(gy, mul(a5, 4.0))
    a6_twice = add(a6, a6)
    gy = sub(gy, a6_twice)
    a8_twice = add(a8, a8)
    gy = add(gy, a8_twice)

    gx = sub(mul(a0, -2.0), a2_twice)
    gx = add(gx, a6_twice)
    gx = add(gx, a8_twice)
    gx = sub(gx, mul(a1, 4.0))
    gx = add(gx, mul(a7, 4.0))

    inverse_determinant = div(1.0, determinant)
    dx = mul(sub(mul(hxy, gx), mul(hxx, gy)), inverse_determinant)
    if abs(dx) >= f32(1.0):
        return [f32(0.0), f32(0.0)]
    dy = mul(sub(mul(hxy, gy), mul(hyy, gx)), inverse_determinant)
    if abs(dy) >= f32(1.0):
        return [f32(0.0), f32(0.0)]
    return [dx, dy]


def verify_constants(binary):
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert digest == EXPECTED_LIBCP_SHA256, digest
    expected = {
        0x5A8128: 1.0,
        0x5A81F0: 0x7FFFFFFF,
        0x5A8870: 4.0,
        0x5A8874: -2.0,
        0x5A8878: -4.0,
        0x5A9B0C: 8.0,
        0x5AAE78: -16.0,
    }
    with binary.open("rb") as handle:
        for offset, value in expected.items():
            handle.seek(offset)
            raw = handle.read(4)
            if isinstance(value, int):
                observed = struct.unpack("<I", raw)[0]
            else:
                observed = struct.unpack("<f", raw)[0]
            assert observed == value, (hex(offset), observed, value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("binary", type=Path)
    args = parser.parse_args()

    verify_constants(args.binary)
    report = json.loads(args.report.read_text(encoding="ascii"))
    fits = report["quadratic_fits"]
    assert len(fits) == 32
    for index, item in enumerate(fits):
        replay = quadratic_fit(item["input"])
        observed = item["result"]
        assert [bits(value) for value in replay] == [bits(value) for value in observed], (
            index,
            item["input"],
            replay,
            observed,
        )
    print(
        "verified",
        len(fits),
        "quadratic fits bit-exact against libcp+0x190da0;",
        "constants and abs mask match installed libcp SHA-256",
        EXPECTED_LIBCP_SHA256,
    )


if __name__ == "__main__":
    main()
