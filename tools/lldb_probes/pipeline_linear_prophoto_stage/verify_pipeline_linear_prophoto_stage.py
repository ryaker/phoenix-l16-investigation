#!/usr/bin/env python3
"""Verify slot-15's fixed linear-ProPhoto color-space materialization."""

from __future__ import annotations

import hashlib
import importlib.util
import re
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
RUNNER = ROOT / "tools/lldb_probes/pipeline_linear_prophoto_stage/run_dump.sh"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("pipeline_color_static_helper", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


HASHES = {
    (0x2D6CD0, 0x2D6D7C): "1e6e3d944be4d85b25546a4fbd4d92972f38585f08635a1cfa0be40730c43fa9",
    (0xA9910, 0xA992B): "37543438b5d5baa51decfdfd2d0ded8d84d04a28651b9e9c28399aaf3a26542f",
    (0xA9340, 0xA990F): "24a66ed994b2850383b7cfcbdaf12e139e7c69725a8fd06353fa55e6ee30f7ae",
    (0xA9930, 0xA9E02): "b45482c022289664f99ef45776a44b7f12e74401f35f19f53fe7c6d7134e0d52",
    (0xA9EA0, 0xA9F12): "260ad79becbeac5446d050fe654c9bbc59cb03c8ae16317878c6522531d12c60",
    (0xA9F20, 0xAA10D): "79f9edbd79dda2b207b6c355f0f52c0043efe21956bd7ff89598fa6505d2520e",
    (0xAA110, 0xAA1EE): "8e7ed6c872fe7b2cfd1e26122ba1bbebdc086f41342eafe5f56d1219a57e40f5",
    (0xAB940, 0xABF1E): "ac9ea23c5b3eb235b808775188626baf93f0fce8e1305ebaa79fdfb7253b6698",
    (0x34A610, 0x34A6D7): "73ab2dfd7195441f39246835e010afaae3886e2405be2a82a272411ef37ffebe",
    (0x34A780, 0x34A847): "88511a8e6046e96a7aa52bff1fd8d8d02ec6b1605f0c7c0ddca43ee3badc5dd6",
    (0x34A8F0, 0x34A9B7): "4871a7188d7e3f7d6493ecb78b97df2761e2d758324267715cf344efa39b1219",
}

EXPECTED_COLOR = "8dfbb03ed08cb73e05000000"
EXPECTED_CONFIG = (
    "6c344c3fb16f0a3e6c6c003d017a933e623d363fd6b9b338"
    "0000000000000000f640533f8dfbb03ed08cb73e0500000005000000"
)
EXPECTED_IDENTITY = (
    "0000803f0000000000000000000000000000803f00000000"
    "00000000000000000000803f"
)
EXPECTED_PIXELS = (
    "000080be000000000000a03f0000003f"
    "00008040000000c00000003e0000803f"
)


def verify_static() -> str:
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == static.LIBCP_SHA256, f"libcp digest changed: {digest}")

    for (start, end), expected in HASHES.items():
        actual = hashlib.sha256(static.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed")

    require(static.cstring(data, mapping, 0x633860).decode("ascii") == "linear_prophoto_rgb",
            "public color-space label changed")
    require(static.instruction(data, mapping, 0x32851D).op_str == "dword ptr [rbp - 0x258], 5",
            "linear_prophoto_rgb selector changed")

    rtti = static.cstring(data, mapping, 0x5AB2E0).decode("ascii")
    require("ImageConvertColorSpace" in rtti and "ChromaticAdaptation" in rtti,
            f"worker RTTI changed: {rtti}")
    require(static.u64(static.bytes_at(data, mapping, 0x6527C0 + 0x30, 8)) == 0xBF4A0,
            "ImageConvertColorSpace worker vtable changed")

    for call_va, target in ((0x2D6D41, 0xA9910), (0x2D6D57, 0xA9EA0)):
        require(static.direct_call_target(static.instruction(data, mapping, call_va)) == target,
                f"singleton constructor call changed at 0x{call_va:x}")
    for va, expected in ((0x2D6D3C, "esi, 5"), (0x2D6D4A, "esi, 5"),
                         (0x2D6D4F, "ecx, 1")):
        require(static.instruction(data, mapping, va).op_str == expected,
                f"singleton constructor argument changed at 0x{va:x}")

    # All three payload wrappers tail-call the same in-place color converter
    # only after their exact 52-byte config comparisons differ.
    for va in (0x34A6D6, 0x34A846, 0x34A9B6):
        item = static.instruction(data, mapping, va)
        require(item.mnemonic == "jmp" and item.op_str == "0xa9f20",
                f"payload converter edge changed at 0x{va:x}")
    return digest


def parse_dump() -> dict[str, str]:
    completed = subprocess.run(
        [str(RUNNER)], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    result = {}
    for line in completed.stdout.splitlines():
        match = re.fullmatch(r"([a-z0-9_]+)=(.*)", line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


def verify_runtime_constructor() -> tuple[float, ...]:
    result = parse_dump()
    require(result["color_space"] == EXPECTED_COLOR, "ColorSpace(5) packet changed")
    require(result["constructed_config"] == EXPECTED_CONFIG, "constructed config changed")
    require(result["singleton_config"] == EXPECTED_CONFIG, "singleton config changed")
    require(result["match"] == "1", "constructed and singleton configs differ")
    require(result["converter_5_5"] == "0xab940", "selected 5->5 converter changed")
    require(result["adaptation"] == EXPECTED_IDENTITY, "equal-whitepoint adaptation changed")
    require(result["source"] == EXPECTED_PIXELS, "fixture source changed")
    require(result["destination"] == EXPECTED_PIXELS, "5->5 conversion is not a bit copy")
    require(result["pixel_match"] == "1", "5->5 fixture mismatch")
    return struct.unpack("<9f2f2I", bytes.fromhex(EXPECTED_CONFIG))


def main() -> None:
    digest = verify_static()
    packet = verify_runtime_constructor()
    matrix = packet[:9]
    print(f"libcp_sha256={digest}")
    print("slot15_target=linear_prophoto_rgb selector=5 adaptation=1")
    print("matrix=" + ",".join(f"{value:.17g}" for value in matrix))
    print(f"white_xy={packet[9]:.17g},{packet[10]:.17g}")
    print(f"source_enum={packet[11]} target_enum={packet[12]}")
    print("converter_5_5=0xab940 equal_whitepoint_matrix=identity fixture=bit_exact_copy")
    print("payload_wrappers=0x34a610,0x34a780,0x34a8f0 conditional_in_place_conversion=1")


if __name__ == "__main__":
    main()
