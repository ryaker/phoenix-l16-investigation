#!/usr/bin/env python3
"""Bit-verify the installed G49 3x3 guarded sub-pixel quadratic fit."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = (
    ROOT / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
REPORTS = {
    tier: ROOT / f"runs/g49_subpixel_refinement/refinement_{tier}.json"
    for tier in ("28mm", "35mm", "70mm", "150mm")
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("g49_static", HELPER_PATH)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value):
    return struct.pack("<f", value).hex()


def i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def iadd(*values):
    total = 0
    for value in values:
        total = i32(total + value)
    return total


def imul(left, right):
    return i32(left * right)


def replay(costs):
    A, B, C, D, E, F, G, H, I = [i32(value) for value in costs]
    q = imul(4, iadd(A, C, G, I, imul(-4, E)))
    hxx = max(iadd(q, imul(8, iadd(D, F, -B, -H))), 0)
    hyy = max(iadd(q, imul(8, iadd(B, H, -D, -F))), 0)
    hxy0 = imul(4, iadd(A, I, -G, -C))

    product = f32(f32(hyy) * f32(hxx))
    determinant0 = f32(product - f32(f32(hxy0) * f32(hxy0)))
    hxy = f32(hxy0) if f32(0.0) < determinant0 else f32(0.0)
    denominator = f32(product - f32(hxy * hxy))

    if denominator == f32(0.0):
        return {
            "raw": None,
            "accepted": (f32(0.0), f32(0.0)),
            "hxx": hxx,
            "hyy": hyy,
            "hxy0": hxy0,
            "hxy": hxy,
            "determinant0": determinant0,
            "denominator": denominator,
        }

    gx = iadd(imul(4, iadd(F, -D)), imul(2, iadd(C, -G)), imul(2, iadd(I, -A)))
    gy = iadd(imul(2, iadd(I, -A, G, -C)), imul(4, iadd(H, -B)))
    numerator_x = f32(f32(hxy * f32(gy)) - f32(f32(hyy) * f32(gx)))
    numerator_y = f32(f32(hxy * f32(gx)) - f32(f32(hxx) * f32(gy)))
    reciprocal = f32(f32(1.0) / denominator)
    dx = f32(numerator_x * reciprocal)
    dy = f32(reciprocal * numerator_y)
    accepted = (dx, dy) if abs(dx) < f32(1.0) and abs(dy) < f32(1.0) else (f32(0.0), f32(0.0))
    return {
        "raw": (dx, dy),
        "accepted": accepted,
        "hxx": hxx,
        "hyy": hyy,
        "hxy0": hxy0,
        "hxy": hxy,
        "determinant0": determinant0,
        "denominator": denominator,
        "gx": gx,
        "gy": gy,
    }


def verify_static():
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    window = STATIC.bytes_at(data, mapping, 0x369B1F, 0x369CB0 - 0x369B1F)
    require(
        hashlib.sha256(window).hexdigest()
        == "9c32d42d9d21931bb56d266c5098f5d6f0024dcedbe1eb3d75661261a69515f9",
        "G49 arithmetic window changed",
    )
    expected = {
        0x369BEC: ("movaps", "xmm1, xmm2"),
        0x369BEF: ("mulss", "xmm1, xmm6"),
        0x369BF6: ("mulss", "xmm0, xmm0"),
        0x369BFD: ("subss", "xmm7, xmm0"),
        0x369C08: ("cmpltss", "xmm0, xmm7"),
        0x369C0D: ("andps", "xmm0, xmm5"),
        0x369C17: ("subss", "xmm1, xmm5"),
        0x369C1B: ("ucomiss", "xmm1, xmm4"),
        0x369C66: ("divss", "xmm5, xmm1"),
        0x369C6A: ("mulss", "xmm4, xmm5"),
        0x369C6E: ("mulss", "xmm5, xmm0"),
        0x369C7F: ("andps", "xmm0, xmm6"),
        0x369C85: ("andps", "xmm1, xmm6"),
        0x369C88: ("ucomiss", "xmm0, xmm2"),
        0x369C8E: ("ucomiss", "xmm1, xmm2"),
        0x369C94: ("and", "al, cl"),
    }
    for address, wanted in expected.items():
        item = STATIC.instruction(data, mapping, address)
        actual = (item.mnemonic, item.op_str)
        require(actual == wanted, f"0x{address:x}: {actual} != {wanted}")
    require(STATIC.bytes_at(data, mapping, 0x5A8128, 4) == struct.pack("<f", 1.0), "one constant")
    require(
        STATIC.bytes_at(data, mapping, 0x5A81F0, 16) == struct.pack("<4I", *([0x7FFFFFFF] * 4)),
        "abs mask",
    )
    return digest


def verify_report(tier, path):
    report = json.loads(path.read_text())
    require(report["libcp_sha256"] == STATIC.LIBCP_SHA256, f"{tier}: digest")
    require(report["done"] and not report["errors"], f"{tier}: probe completion")
    require(len(report["packets"]) == 24, f"{tier}: packet count")
    classes = {"zero_denominator": 0, "accepted": 0, "unit_guard_rejected": 0}
    for index, packet in enumerate(report["packets"]):
        result = replay(packet["costs_u32_row_major"])
        runtime_raw = (
            (packet["raw_offset_x"], packet["raw_offset_y"])
            if "raw_offset_x" in packet
            else None
        )
        if result["raw"] is None:
            classes["zero_denominator"] += 1
            require(runtime_raw is None, f"{tier}:{index}: zero-denominator branch")
        else:
            require(runtime_raw is not None, f"{tier}:{index}: missing raw offsets")
            for expected, actual in zip(result["raw"], runtime_raw):
                require(f32_bits(expected) == f32_bits(actual), f"{tier}:{index}: raw offset")
            require(
                f32_bits(result["denominator"]) == f32_bits(packet["denominator_after_div"]),
                f"{tier}:{index}: denominator",
            )
        runtime_accepted = (packet["accepted_offset_x"], packet["accepted_offset_y"])
        for expected, actual in zip(result["accepted"], runtime_accepted):
            require(f32_bits(expected) == f32_bits(actual), f"{tier}:{index}: accepted offset")
        if result["raw"] is not None and result["accepted"] == result["raw"]:
            classes["accepted"] += 1
        elif result["raw"] is not None:
            classes["unit_guard_rejected"] += 1
        require(all(math.isfinite(value) for value in runtime_accepted), f"{tier}:{index}: finite")
    return classes


def main():
    digest = verify_static()
    print(f"g49_static=OK libcp={digest} window=0x369b1f..0x369cb0")
    totals = {"zero_denominator": 0, "accepted": 0, "unit_guard_rejected": 0}
    for tier, path in REPORTS.items():
        classes = verify_report(tier, path)
        print(f"{tier}: {classes}")
        for key, value in classes.items():
            totals[key] += value
    require(all(value > 0 for value in totals.values()), f"missing branch class: {totals}")
    print(f"total: {totals}")
    print("g49_subpixel_refinement=OK")


if __name__ == "__main__":
    main()
