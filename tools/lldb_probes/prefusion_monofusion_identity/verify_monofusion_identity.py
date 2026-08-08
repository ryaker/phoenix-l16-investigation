#!/usr/bin/env python3
"""Verify the installed-bundle identity and custody of FusionCacheBayer+0x20."""

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


def load_static():
    spec = importlib.util.spec_from_file_location("monofusion_static", STATIC_PATH)
    require(spec is not None and spec.loader is not None, f"cannot import {STATIC_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_static()


def u64(raw: bytes) -> int:
    return struct.unpack("<Q", raw)[0]


def cstring(data: bytes, mapping, va: int) -> str:
    offset = STATIC.file_offset(mapping, va)
    end = data.index(b"\0", offset)
    return data[offset:end].decode("ascii")


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def rtti_name(data: bytes, mapping, address_point: int) -> str:
    typeinfo = u64(STATIC.bytes_at(data, mapping, address_point - 8, 8))
    name_pointer = u64(STATIC.bytes_at(data, mapping, typeinfo + 8, 8))
    return cstring(data, mapping, name_pointer)


def main() -> None:
    digest = STATIC.verify_static()
    require(
        digest == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        f"unexpected libcp digest {digest}",
    )
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    windows = {
        (0x4066FC, 0x4067C0): "b29d12765ac8836c67040ffe24887bd5321a3eb278719fc84976fc4f7e9d967e",
        (0x406970, 0x4069C6): "49d7235e6496eeb37b7bca27d2966960e7ca3832d63ce752cafc50a7d5e7c60c",
        (0x406B9F, 0x406C30): "67fe031a30ca6225c70556a997f9da966fa5792b9927514377b2addcea09db89",
        (0x1B17C0, 0x1B1830): "1ffa43f0a5e9023b51d30fe8820e275595123a1ca741d4626a3d532e5e3f1440",
        (0x1B26F1, 0x1B2730): "e06dca3165e69327018b530a462453175873e5f9e959d297bb0206512d4af97f",
        (0x1B3530, 0x1B35A0): "c9461483d110a3b58c59a9ff07dff81811080d0d771ebec2d94fffc33ddfa040",
        (0x657BD0, 0x657D28): "a5c411256a6b68d6e52eaa1f85a2ee7f3a94b893ddabce117b212681ce9c3972",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed: {actual}")

    require(
        cstring(data, mapping, 0x631B73) == "Called MonoFusion::initialize() twice!",
        "MonoFusion initialize guard string changed",
    )

    expected_rtti = {
        0x657BE0: (
            "NSt3__110__function6__funcIZN2lt10MonoFusion10initializeEPKbE3$_0"
            "NS_9allocatorIS6_EEFfffEEE"
        ),
        0x657C68: (
            "NSt3__110__function6__funcIZN2lt10MonoFusion10initializeEPKbE3$_2"
            "NS_9allocatorIS6_EEFbfRKNS2_4Vec2IfEEEEE"
        ),
    }
    for address_point, expected in expected_rtti.items():
        actual = rtti_name(data, mapping, address_point)
        require(actual == expected, f"RTTI at 0x{address_point:x} changed: {actual}")

    expected_slots = {
        0x657BE0: (
            0x1B3310,
            0x1B3320,
            0x1B3330,
            0x1B3360,
            0x1B3380,
            0x1B3390,
            0x1B33A0,
            0x1B33D0,
            0x1B33F0,
        ),
        0x657C68: (
            0x1B3400,
            0x1B3410,
            0x1B3420,
            0x1B3450,
            0x1B3470,
            0x1B3480,
            0x1B3490,
            0x1B3500,
            0x1B3520,
        ),
    }
    for address_point, expected in expected_slots.items():
        actual = tuple(
            u64(STATIC.bytes_at(data, mapping, address_point + 8 * index, 8))
            for index in range(len(expected))
        )
        require(actual == expected, f"vtable slots changed at 0x{address_point:x}")

    require(call_target(data, mapping, 0x40670C) == 0x556398, "MonoFusion allocation")
    require(call_target(data, mapping, 0x40676B) == 0x1B17B0, "MonoFusion constructor")
    require(call_target(data, mapping, 0x40699E) == 0x1AB2D0, "ColorFusionBayer initialize")
    require(call_target(data, mapping, 0x406C2A) == 0x1B3530, "MonoFusion process")
    require(call_target(data, mapping, 0x1B3599) == 0x1B37A0, "MonoFusion process worker")

    byte_guards = {
        0x406707: "bf50020000",          # allocate 0x250-byte optional object
        0x40675D: "4c89e7",              # constructed object is r12
        0x406774: "4d896520",            # FusionCacheBayer+0x20 = r12
        0x4069A3: "807b180074",          # gate on FusionCacheBayer+0x18
        0x4069A9: "488b7b20",            # load FusionCacheBayer+0x20
        0x4069B8: "e903aedaff",          # tail-call 0x1b17c0 initialize
        0x406C0A: "498b7f20",            # load FusionCacheBayer+0x20 for process
        0x1B17E8: "4180be4002000000",    # reject repeated initialize
        0x1B2722: "41c6864002000001",    # MonoFusion+0x240 initialized = 1
        0x1B2A33: "488d3539f14700",      # unique MonoFusion guard string xref
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    print(f"static_monofusion_identity=OK libcp={digest}")
    print("FusionCacheBayer+0x20=lt::MonoFusion")
    print("wide_construct=0x406707->0x1b17b0->0x406774")
    print("initialize=0x4069a9->0x1b17c0 callbacks=0x657be0,0x657c68")
    print("process=0x406c0a->0x1b3530->0x1b37a0")


if __name__ == "__main__":
    main()
