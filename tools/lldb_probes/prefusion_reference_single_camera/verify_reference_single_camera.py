#!/usr/bin/env python3
"""Verify ReferenceImageCache's one-Camera construction and lookup custody."""

from __future__ import annotations

import hashlib
import importlib.util
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CACHE_VERIFIER = (
    ROOT
    / "tools/lldb_probes/prefusion_cache_rtti_identity"
    / "verify_prefusion_cache_rtti_identity.py"
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


CACHE = load_module("reference_single_camera_cache", CACHE_VERIFIER)
STATIC = CACHE.STATIC


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify() -> str:
    digest, names = CACHE.verify_static()
    require(names["reference_cache"] == "N2lt19ReferenceImageCacheE", "cache RTTI")

    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    windows = {
        (0x3DDD50, 0x3DDE52): "1d64116e714e52304427d4a33f2887f7fe231f8b3de413456f4b13ace749bb29",
        (0x3DDF30, 0x3DDF6B): "fb1560f08defe8f2ec0e1a3bcee6a1f47b106f22456b2dbd557f2e19b60eaf4e",
        (0x3E27A0, 0x3E28CB): "68c14463dd9888d16deb8700c20d45afcbfa19952d757ca8a51e35c5db28e808",
        (0x65F178, 0x65F470): "1784b4018b1a12d4c7047d72be8de01a9ac87f555c806f9c1c93433a9a11e54a",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")

    constructor_prefix = (
        "NSt3__110__function6__funcIZN2lt19ReferenceImageCacheC1E"
        "RKNS_6vectorINS2_4Vec2IiEENS_9allocatorIS6_EEEERKS6_"
        "RKNS_10shared_ptrINS2_11TileStorageEEERKNSE_INS2_15RawImageFactoryEEE"
        "NS2_13CapturedImage6CameraERKNSE_INS2_14StereoAsyncAPIEEEE"
    )
    for index, address_point in enumerate((0x65F188, 0x65F208, 0x65F288, 0x65F308, 0x65F388)):
        name = CACHE.rtti_name(data, mapping, address_point)
        require(name.startswith(constructor_prefix), f"constructor RTTI {index} changed")
        require(
            name.count("CapturedImage6Camera") == 1,
            f"constructor RTTI {index} does not carry exactly one Camera enum",
        )
        require(f"3$_{index}" in name, f"constructor lambda index {index} changed")

    byte_guards = {
        0x3DDD5F: "4589ce",                         # incoming r9d Camera -> r14d
        0x3DDD7D: "4589b42490000000",               # Camera -> base object+0x90
        0x3DDDA6: "498bb42498000000458bb42490000000",  # reload factory and same key
        0x3DDE01: "498bb42498000000418b942490000000488d7dd0",
        0x3DDF39: "488bb7980000008b9790000000488d7de8",  # accessor uses +0x98/+0x90
        0x3E27B4: "4589cf4d89c44989fd",             # derived saves r9d and r8
        0x3E286B: "498b3424488dbd60ffffff4489fa",   # derived lookup uses saved key
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    expected_calls = {
        0x3DDDBD: 0x1BE970,
        0x3DDE15: 0x1BE970,
        0x3DDF4A: 0x1BE970,
        0x3E27CB: 0x3DDD50,
        0x3E2879: 0x1BE970,
    }
    for call_va, target in expected_calls.items():
        require(call_target(data, mapping, call_va) == target, f"call target at 0x{call_va:x}")

    return digest


def main() -> None:
    digest = verify()
    print(f"reference_single_camera_static=OK libcp={digest}")
    print("type=lt::ReferenceImageCache")
    print("constructor_camera_parameters=1 public_type=lt::CapturedImage::Camera")
    print("camera_storage=base+0x90 raw_image_factory=base+0x98/+0xa0")
    print("same_key_raw_image_lookups=base_ctor:2 derived_ctor:1 accessor:1")
    print("reference_single_camera=OK")


if __name__ == "__main__":
    main()
