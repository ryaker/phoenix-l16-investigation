#!/usr/bin/env python3
"""Verify installed IRAMP src1/src2/direct-contributor operand-role custody."""

from __future__ import annotations

import hashlib
import importlib.util
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
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


STATIC = load_module("iramp_operand_roles_static", STATIC_PATH)


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    windows = {
        (0x366553, 0x3666FF): "a788b52e5991230376b90cc7f2fb97b98ea8fee795e175ec7bdd72c41a63ee46",
        (0x366900, 0x366A05): "48ddbc7b7a2da58f05906a77e4a22f711040aa6aaeae9df81462b2c4cfd05870",
        (0x366A50, 0x366B38): "7ac124a340cc7d0077d3b330d45a2aa6b8a794d991a228a0751e14ad89f3f701",
        (0x366B66, 0x366D5D): "1eed7a5aeee2a99608c53aaadcf5fed111df4b5f16d346f853481e08f384e836",
        (0x366E5D, 0x366F21): "cc5b8f2d8adaff2586fa8adc8c95bb826536cb5be4405e5e5d2c63bfd3029064",
        (0x368833, 0x368BA3): "23679da17a350db4bb43a388619992afcd77fd98b455caed912f3bb70ee54f41",
        (0x369167, 0x3692CB): "496a1c80dd6f58039bba63c223c3d772b0bb15ea2dced4cfc96b2940251d98b4",
        (0x3692DC, 0x369320): "16d09eaed1153bc538280f84be64edb7b5ad13524b237c42e829297216bf35b9",
        (0x369E31, 0x369F39): "d7189c83497c763c237819004eec0155a3aa59d6f14a094edb1f5113af743d8f",
        (0x36A7C0, 0x36AA5B): "e5fe9712aa8660c89736de6e32f6cb651a12c689cd8d0188ea1ad5e1c8dab1e5",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")

    byte_guards = {
        0x36656B: "498b7708",                    # closure+8 src1
        0x366915: "498b7710",                    # closure+0x10 src2
        0x366A50: "498b4f18",                    # closure+0x18 direct vector
        0x366B18: "4d8b6f08",                    # src1 dimensions for warp-grid bounds
        0x366B1C: "498b4f20",                    # closure+0x20 warp vector
        0x366E5D: "488b8d78bcffff488b4118488b4928488b00488b9598bcffff488b3410",
                                                    # direct-vector item selection
        0x3691B2: "48638588e8ffff",              # src1-derived byte-guide stride
        0x3691C3: "48039590e8ffff",              # src1-derived byte-guide data
        0x3692B1: "488dbdc0bdffff",              # reference scratch destination
        0x3692B8: "488db530e8ffff",              # src2 vec4 image descriptor
        0x369E31: "488dbdc0bdffff",              # reference patch argument
        0x369E38: "488db560eeffff",              # warped direct candidate patch
        0x36A7D8: "f30f10448b08",                # tuple score load
        0x36A84B: "0f289d00bdffff",              # tuple score -> multiplier
        0x36A8C0: "0f280c39",                    # candidate vec4 load
        0x36A8C4: "0f59c8",                      # candidate * score multiplier
        0x36A8C7: "0f580c3a",                    # add destination
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    expected_calls = {
        0x3665D5: 0x374AC0,  # render src1
        0x3666BA: 0x374870,  # derive src1 guide transform
        0x366826: 0x36FBA0,  # materialize src1 byte guide
        0x36695A: 0x374AC0,  # render src2
        0x366F1C: 0x374AC0,  # render direct contributor i
        0x3692C6: 0x36B920,  # src2 reference patch -> scratch
        0x369E3F: 0x36CDE0,  # reference/candidate patch score
        0x369F34: 0x36E530,  # normalized selector/reduction preparation
        0x36A838: 0x372A00,  # tuple-adjusted candidate resample
        0x36A974: 0x19E7D0,  # normalize accumulated candidate patch
    }
    for call_va, target in expected_calls.items():
        require(call_target(data, mapping, call_va) == target, f"call target at 0x{call_va:x}")

    return digest


def main() -> None:
    digest = verify()
    print(f"iramp_operand_roles_static=OK libcp={digest}")
    print("src1=coarse_registration_guide")
    print("src2=vec4_reference_patch")
    print("srcs[i]+warps[i]=warped_direct_candidate_patch")
    print("comparison=reference_candidate_patch_score")
    print("score_consequence=tuple_multiplier_normalized_weighted_add")
    print("iramp_operand_roles=OK")


if __name__ == "__main__":
    main()
