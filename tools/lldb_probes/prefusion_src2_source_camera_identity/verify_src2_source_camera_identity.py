#!/usr/bin/env python3
"""Verify visible-src2 RawImageFactory source-camera identity on two bodies."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_cache_rtti_identity"
    / "verify_prefusion_cache_rtti_identity.py"
)
CASES = {
    "unit1_28mm": (0, 1),
    "unit1_70mm": (8, 0),
    "unit2_28mm": (0, 1),
    "unit2_70mm": (8, 0),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_module("src2_source_camera_base", BASE_PATH)
STATIC = BASE.STATIC


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def parse_packet(path: Path) -> dict:
    packets = [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.startswith('{"accepted":')
    ]
    require(len(packets) == 1, f"{path}: expected one packet")
    return packets[0]


def verify_static() -> str:
    digest, _ = BASE.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    raw = STATIC.bytes_at(data, mapping, 0x406B3F, 0x24)
    require(
        hashlib.sha256(raw).hexdigest()
        == "0cbe5226a739bc7e5c6b7b38d6527921a800ec01578d2ad72c74988e8a4314d6",
        "0x406b3f source-lookup window changed",
    )
    require(call_target(data, mapping, 0x406B43) == 0x1BEA00, "camera-key call changed")
    require(call_target(data, mapping, 0x406B59) == 0x1BE970, "CapturedImage lookup changed")
    expected_rtti = (
        "NSt3__120__shared_ptr_emplaceIN2lt13CapturedImageENS_9allocatorIS2_EEEE"
    )
    require(BASE.rtti_name(data, mapping, 0x665EB8) == expected_rtti, "CapturedImage RTTI")
    return digest


def verify_runtime() -> None:
    out = ROOT / "runs/prefusion_src2_source_camera_identity"
    for case_name, (expected_key, expected_flag) in CASES.items():
        packet = parse_packet(out / f"{case_name}.log")
        require(packet["errors"] == [], f"{case_name}: probe errors")
        require(packet["accepted"], f"{case_name}: no accepted lookup")
        for event in packet["accepted"]:
            require(event["key"] == expected_key, f"{case_name}: derived key")
            require(
                event["captured_camera_id_0x60"] == expected_key,
                f"{case_name}: CapturedImage camera id",
            )
            require(event["captured_active_0x30"] == 1, f"{case_name}: source inactive")
            require(event["flag_0x18"] == expected_flag, f"{case_name}: branch flag")
            require(event["control_vptr_va"] == 0x665EB8, f"{case_name}: source RTTI")


def main() -> None:
    digest = verify_static()
    verify_runtime()
    print(f"static_src2_source_camera_identity=OK libcp={digest}")
    print("wide_source=A1/key0 lt::CapturedImage")
    print("tele_source=B4/key8 lt::CapturedImage")
    print("runtime_scope=Unit-1_28mm,Unit-1_70mm,Unit-2_28mm,Unit-2_70mm")
    print("src2_source_camera_identity=OK")


if __name__ == "__main__":
    main()
