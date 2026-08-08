#!/usr/bin/env python3
"""Verify that the state+0xe0 lookup context is lt::RawImageFactory."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
)
EXPECTED_LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
CAPTURE_STACK_RTTI = (
    "NSt3__120__shared_ptr_emplaceIN2lt12CaptureStackENS_9allocatorIS2_EEEE"
)
RAW_IMAGE_FACTORY_RTTI = (
    "NSt3__120__shared_ptr_pointerIPN2lt15RawImageFactoryE"
    "NS_14default_deleteIS2_EENS_9allocatorIS2_EEEE"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_static_module():
    spec = importlib.util.spec_from_file_location("index5_static", STATIC_PATH)
    require(spec is not None and spec.loader is not None, "cannot load static helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    static = load_static_module()
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    require(
        hashlib.sha256(data).hexdigest() == EXPECTED_LIBCP_SHA256,
        "installed libcp SHA-256 drift",
    )

    require(
        static.u64(static.bytes_at(data, mapping, 0x665DB8, 8)) == 0x665DF0,
        "CaptureStack control-block typeinfo pointer changed",
    )
    require(
        static.u64(static.bytes_at(data, mapping, 0x665DF8, 8)) == 0x5ADC00,
        "CaptureStack typeinfo-name pointer changed",
    )
    require(
        static.cstring(data, mapping, 0x5ADC00).decode("ascii") == CAPTURE_STACK_RTTI,
        "CaptureStack RTTI name changed",
    )
    require(
        static.u64(static.bytes_at(data, mapping, 0x66A490, 8)) == 0x66A4C0,
        "RawImageFactory shared control-block typeinfo pointer changed",
    )
    require(
        static.u64(static.bytes_at(data, mapping, 0x66A4C8, 8)) == 0x604350,
        "RawImageFactory typeinfo-name pointer changed",
    )
    require(
        static.cstring(data, mapping, 0x604350).decode("ascii")
        == RAW_IMAGE_FACTORY_RTTI,
        "RawImageFactory shared control-block RTTI name changed",
    )

    expected_ops = {
        0x3C9385: "edi, 0x2d0",
        0x3C93A9: "rbx, 0x18",
        0x3C93C0: "edi, 0x90",
        0x3C93F6: "qword ptr [rax + 0x18], r12",
        0x3C93FA: "qword ptr [r14 + 0xa0], r12",
        0x3C6AC4: "rax, [rdi + 0xa0]",
        0x3B3008: "rsi, rax",
        0x3F2C63: "r14, rsi",
        0x3F2CE0: "rax, qword ptr [r14]",
        0x3F2CE3: "qword ptr [r13 + 0xe0], rax",
        0x3F2CEA: "rdi, qword ptr [r14 + 8]",
        0x3F2CEE: "qword ptr [r13 + 0xe8], rdi",
        0x3FF13D: "rsi, qword ptr [r14 + 0xe0]",
        0x1BE980: "rcx, qword ptr [rsi]",
        0x1BE983: "edx, dword ptr [rsi + 0x10]",
        0x1BD2A0: "rax, qword ptr [rsi]",
        0x1BD2A3: "qword ptr [r15], rax",
        0x1BD2A6: "rdi, qword ptr [rsi + 8]",
        0x1BD2AA: "qword ptr [r15 + 8], rdi",
        0x1BD2B8: "dword ptr [r15 + 0x10], r14d",
    }
    for va, op_str in expected_ops.items():
        actual = static.instruction(data, mapping, va).op_str
        require(actual == op_str, f"0x{va:x}: {actual!r} != {op_str!r}")

    require(
        static.rip_target(static.instruction(data, mapping, 0x3C939B)) == 0x665DC0,
        "CaptureStack control-block address point changed",
    )
    require(
        static.rip_target(static.instruction(data, mapping, 0x3C93EC)) == 0x66A498,
        "RawImageFactory shared control-block address point changed",
    )
    expected_calls = {
        0x3C93B3: 0xE52C0,
        0x3C93D6: 0x1BDC70,
        0x3B2FEE: 0x3C6AC0,
        0x3B3011: 0x3F46D0,
        0x3F46E6: 0x3F2C40,
        0x3FF14A: 0x1BE970,
        0x1BE98B: 0xE6BA0,
    }
    for va, target in expected_calls.items():
        actual = static.direct_call_target(static.instruction(data, mapping, va))
        require(actual == target, f"0x{va:x}: call target 0x{actual:x} != 0x{target:x}")

    print(
        "state_e0_rawimagefactory_identity=OK "
        f"libcp={EXPECTED_LIBCP_SHA256} "
        "owner+0xa0=shared_ptr<lt::RawImageFactory> "
        "state+0xe0/+0xe8=retained_raw/control "
        "backing=shared_ptr<lt::CaptureStack>"
    )


if __name__ == "__main__":
    main()
