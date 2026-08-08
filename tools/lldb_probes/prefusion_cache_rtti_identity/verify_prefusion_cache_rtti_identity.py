#!/usr/bin/env python3
"""Verify exact RTTI identities for visible src1 and contributor cache objects."""

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


STATIC = load_module("prefusion_cache_rtti_static", STATIC_PATH)


def u64(raw: bytes) -> int:
    return struct.unpack("<Q", raw)[0]


def cstring(data: bytes, mapping, va: int) -> str:
    offset = STATIC.file_offset(mapping, va)
    end = data.find(b"\0", offset)
    require(end >= offset, f"unterminated string at 0x{va:x}")
    return data[offset:end].decode("ascii")


def rtti_name(data: bytes, mapping, address_point: int) -> str:
    typeinfo = u64(STATIC.bytes_at(data, mapping, address_point - 8, 8))
    name_pointer = u64(STATIC.bytes_at(data, mapping, typeinfo + 8, 8))
    return cstring(data, mapping, name_pointer)


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify_static() -> tuple[str, dict[str, str]]:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    windows = {
        (0x3B3069, 0x3B30E7): "5be4cfb019f30854cdca889277f81f1f6cec8ef101f808702d3edb011d717c0b",
        (0x3DFCC0, 0x3E006D): "15d8a52eaeea8df42d3580927c0bc6727554b717f14b325f225bcb4ebc990099",
        (0x65F130, 0x65F1A0): "78dd25e341b9804cf0e383186f5a69a0c91f78c349b7e64b333442faab3d7e28",
        (0x65F480, 0x65F4D0): "92c87c6017c38b0aa81f5d2dc6f0170e1381fb17eace0422d47e1e1a71a352e0",
        (0x66A100, 0x66A160): "cb07cb9c3596c48050fde588b2628c1aa0729478863c1aca2649ae666dc58387",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")

    expected_names = {
        "image_caches_control": (
            0x66A118,
            "NSt3__120__shared_ptr_emplaceIN2lt11ImageCachesENS_9allocatorIS2_EEEE",
        ),
        "reference_cache": (0x65F140, "N2lt19ReferenceImageCacheE"),
        "source_cache": (0x65F490, "N2lt16SourceImageCacheE"),
        "src1_lambda": (
            0x65F668,
            "NSt3__110__function6__funcIZN2lt13PipelineCache10initResAmpEPbE3$_1"
            "NS_9allocatorIS5_EEFbRNS2_5ImageINS2_8vec4x32fEEERKNS2_9RectangleIiEEEEE",
        ),
        "src2_lambda": (
            0x65F6E8,
            "NSt3__110__function6__funcIZN2lt13PipelineCache10initResAmpEPbE3$_2"
            "NS_9allocatorIS5_EEFbRNS2_5ImageINS2_8vec4x32fEEERKNS2_9RectangleIiEEEEE",
        ),
    }
    names: dict[str, str] = {}
    for label, (address_point, expected) in expected_names.items():
        actual = rtti_name(data, mapping, address_point)
        require(actual == expected, f"{label} RTTI changed: {actual}")
        names[label] = actual

    reference_callback = rtti_name(data, mapping, 0x65F388)
    for token in (
        "ReferenceImageCacheC1E",
        "RawImageFactory",
        "CapturedImage6Camera",
        "StereoAsyncAPI",
        "TileINS2_4Vec3INS2_7Float16",
    ):
        require(token in reference_callback, f"reference callback missing {token}")
    source_callback = rtti_name(data, mapping, 0x65F4D8)
    for token in (
        "SourceImageCacheC1E",
        "RawImageFactory",
        "CapturedImage6Camera",
        "LensUndistortCRA",
        "TileINS2_8vec4x16f",
    ):
        require(token in source_callback, f"source callback missing {token}")

    expected_slots = {
        0x65F140: (0x3E53A0, 0x3E54C0, 0x3E2DC0),
        0x65F490: (0x3E81F0, 0x3E8260, 0x3E77E0),
        0x65F668: (0x3ECB80, 0x3ECB90, 0x3ECBA0, 0x3ECBD0, 0x3ECBF0, 0x3ECC00, 0x3ECC10),
        0x65F6E8: (0x3ECCF0, 0x3ECD00, 0x3ECD10, 0x3ECD40, 0x3ECD60, 0x3ECD70, 0x3ECD80),
        0x66A118: (0x3C1FB0, 0x3C1FE0, 0x3C2020, 0, 0x3C2030),
    }
    for address_point, expected in expected_slots.items():
        actual = tuple(
            u64(STATIC.bytes_at(data, mapping, address_point + 8 * index, 8))
            for index in range(len(expected))
        )
        require(actual == expected, f"vtable slots changed at 0x{address_point:x}: {actual}")

    byte_guards = {
        0x3B3069: "bf80000000",          # 0x80-byte shared control/object allocation
        0x3B30A8: "488d0569702b00",      # ImageCaches control-block address point
        0x3B30B3: "4d89ef",              # inner object starts at control +0x18
        0x3B30C8: "4c89bb" "a8060000",    # owner+0x6a8 = ImageCaches object
        0x3B30D6: "4c89ab" "b0060000",    # owner+0x6b0 = shared control
        0x3E0026: "bf90040000",          # ReferenceImageCache allocation size
        0x3E0066: "4c896b28",            # first-map node+0x28 payload store
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    require(call_target(data, mapping, 0x3B30C3) == 0x3E02D0, "ImageCaches constructor call")
    require(call_target(data, mapping, 0x3E005D) == 0x3E2DB0, "ReferenceImageCache constructor call")
    return digest, names


def main() -> None:
    digest, names = verify_static()
    print(f"static_prefusion_cache_rtti_identity=OK libcp={digest}")
    print("owner+0x6a8=lt::ImageCaches")
    print("src1_payload=lt::ReferenceImageCache vtable=0x65f140")
    print("direct_contributor_payload=lt::SourceImageCache vtable=0x65f490")
    print("visible_wrappers=PipelineCache::initResAmp::$_1/$_2")
    print(f"rtti_entries={len(names)}")
    print("prefusion_cache_rtti_identity=OK")


if __name__ == "__main__":
    main()
