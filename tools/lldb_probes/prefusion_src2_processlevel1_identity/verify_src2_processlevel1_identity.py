#!/usr/bin/env python3
"""Verify the exact installed identity of the visible src2 processing path."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE_VERIFIER = (
    ROOT
    / "tools/lldb_probes/prefusion_cache_rtti_identity"
    / "verify_prefusion_cache_rtti_identity.py"
)
RUNTIME_LOGS = {
    "28mm": ROOT / "runs/src2_executor_target/src2_executor_target_28mm.log",
    "35mm": ROOT / "runs/src2_executor_target/src2_executor_target_35mm_hwcomplete.log",
    "70mm": ROOT / "runs/src2_executor_target/src2_executor_target_70mm_hwcomplete.log",
    "150mm": ROOT / "runs/src2_executor_target/src2_executor_target_150mm_hwcomplete.log",
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


BASE = load_module("prefusion_src2_rtti_base", BASE_VERIFIER)
STATIC = BASE.STATIC


def u64(raw: bytes) -> int:
    return struct.unpack("<Q", raw)[0]


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def rip_lea_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 7)
    require(raw[:3] == bytes.fromhex("488d0d"), f"0x{va:x} is not lea disp32(%rip),%rcx")
    return va + 7 + struct.unpack_from("<i", raw, 3)[0]


def verify_static() -> str:
    digest, _ = BASE.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    windows = {
        (0x65F6D8, 0x65F850): "12432bd4344eb37d39bf865ec93c3b2c735aa8a352bf2446b3173ad7cde83cca",
        (0x3ECD80, 0x3ECE10): "e4a2cb418ef9de0e8e66859eaa1193e814851174d0a15a34debf7558d5fef2bc",
        (0x3EC3F5, 0x3EC467): "ddeed1c8ac2e987c9f6a6b54405f3c978b1f034906f258c9fe411978fe2216a6",
        (0x3ED2E0, 0x3ED330): "23cbd9b2d66aa861322d929416f6df1710f95da8980b3b67cd2f085b24387c63",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")

    expected_names = {
        0x65F6E8: (
            "NSt3__110__function6__funcIZN2lt13PipelineCache10initResAmpEPbE3$_2"
            "NS_9allocatorIS5_EEFbRNS2_5ImageINS2_8vec4x32fEEERKNS2_9RectangleIiEEEEE"
        ),
        0x65F768: (
            "NSt3__110__function6__funcIZN2lt13PipelineCache10initResAmpEPbE3$_3"
            "NS_9allocatorIS5_EEFbRNS2_5ImageINS2_8vec4x32fEEERKNS2_9RectangleIiEEEEE"
        ),
        0x65F7E8: (
            "NSt3__110__function6__funcIZN2lt8Internal16ImageWarpClamped"
            "ILNS2_15ResamplerFilterE2ENS2_8vec4x32fERZNS2_13PipelineCache"
            "13processLevel1ERNS2_5ImageIS6_EERKNS2_9RectangleIiEEE3$_4"
            "NS3_15ExprConstScalarIS6_EEEEvRNS8_IT0_EERKSK_OT1_RKT2_EUlSE_iE_"
            "NS_9allocatorIST_EEFvSE_iEEE"
        ),
    }
    for address_point, expected in expected_names.items():
        actual = BASE.rtti_name(data, mapping, address_point)
        require(actual == expected, f"RTTI changed at 0x{address_point:x}: {actual}")

    expected_slots = {
        0x65F6E8: (0x3ECCF0, 0x3ECD00, 0x3ECD10, 0x3ECD40, 0x3ECD60, 0x3ECD70, 0x3ECD80),
        0x65F768: (0x3ECE40, 0x3ECE50, 0x3ECE60, 0x3ECE90, 0x3ECEB0, 0x3ECEC0, 0x3ECED0),
        0x65F7E8: (0x3ED230, 0x3ED240, 0x3ED250, 0x3ED290, 0x3ED2C0, 0x3ED2D0, 0x3ED2E0),
    }
    for address_point, expected in expected_slots.items():
        actual = tuple(
            u64(STATIC.bytes_at(data, mapping, address_point + 8 * index, 8))
            for index in range(len(expected))
        )
        require(actual == expected, f"vtable slots changed at 0x{address_point:x}")

    require(call_target(data, mapping, 0x3ECDA8) == 0x3EBB80, "src2 wrapper call")
    require(call_target(data, mapping, 0x3ECDC7) == 0x3EDB80, "src2 normalize call")
    require(rip_lea_target(data, mapping, 0x3EC410) == 0x65F7E8, "processLevel1 callback install")
    return digest


def parse_runtime_log(path: Path) -> tuple[dict, dict]:
    summary_prefix = "L16_SRC2_EXECUTOR_TARGET_SUMMARY "
    summary = None
    packet = None
    for line in path.read_text().splitlines():
        if line.startswith(summary_prefix):
            summary = json.loads(line[len(summary_prefix) :])
        elif line.startswith('{"accepted_gates":'):
            packet = json.loads(line)
    require(summary is not None, f"missing runtime summary in {path}")
    require(packet is not None, f"missing runtime packet in {path}")
    return summary, packet


def verify_runtime() -> None:
    for zoom, path in RUNTIME_LOGS.items():
        summary, packet = parse_runtime_log(path)
        require(summary["accepted_gate_count"] >= 1, f"{zoom}: no accepted gate")
        require(summary["accepted_dispatch_count"] >= 1, f"{zoom}: no accepted dispatch")
        require(summary["worker_entry_count"] >= 1, f"{zoom}: no worker entry")
        require(summary["slot30_vas"] == [0x3ED2E0], f"{zoom}: slot target changed")
        require(summary["worker_entry_vas"] == [0x3ED2E0], f"{zoom}: worker changed")
        require(packet["errors"] == [], f"{zoom}: runtime errors")
        accepted = packet["accepted_gates"][0]["callback"]
        require(accepted["vptr_va"] == 0x65F7E8, f"{zoom}: callback RTTI table changed")


def main() -> None:
    digest = verify_static()
    verify_runtime()
    print(f"static_src2_processlevel1_identity=OK libcp={digest}")
    print("visible_src2_wrapper=PipelineCache::initResAmp::$_2")
    print("visible_src2_method=PipelineCache::processLevel1")
    print("worker=ImageWarpClamped<ResamplerFilter=2,vec4x32f> callback +0x30=0x3ed2e0")
    print("direct_contributor_wrapper=PipelineCache::initResAmp::$_3")
    print("runtime_scope=28mm,35mm,70mm,150mm")
    print("src2_processlevel1_identity=OK")


if __name__ == "__main__":
    main()
