#!/usr/bin/env python3
"""Verify the installed and runtime origins of index-5 SGM tuning fields."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
CTOR_ROOT = ROOT / "runs/stereolayer_constructor_provenance"
TERM_ROOT = ROOT / "runs/codex_276860_xmm3_term_step"
XMM4_ROOT = ROOT / "runs/codex_276860_xmm4_origin"
TIERS = ("28mm", "35mm", "70mm", "150mm")
EXPECTED_SCALE_HEX = "8a25a43d4f38f63c4f38f63c00000000"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("index5_sgm_parameter_static", STATIC_PATH)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32s(raw: bytes) -> tuple[float, ...]:
    return struct.unpack("<" + "f" * (len(raw) // 4), raw)


def verify_static() -> tuple[str, tuple[float, ...]]:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    windows = {
        (0x27ABB0, 0x27AC72): "2fbc41a1606c133f6ef544b35f0b1a515f964a2c9aa24d47d5fd7f169347eaaf",
        (0x26B750, 0x26B7D6): "3016743611ab94915e9f6d70edaf5c8402f7010a52783f01316d2eba51427a12",
        (0x3F3AFA, 0x3F40EB): "9917c70707f8a918ba369787eeec2b35405b18d3cad3b399cbc50abdadb8335c",
        (0x27786B, 0x277A16): "e92f03110d46e23332d3f10b32f38006388dcdea5be756fc32dca462e50a7dc7",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")

    byte_guards = {
        0x277885: "0f595760",       # guide delta * object+0x60
        0x277903: "0fb75756",       # object+0x56
        0x27790E: "f30f595758",     # * object+0x58
        0x2779D7: "660fddc1",       # shifted candidate + P1
        0x2779DB: "660f383ac5",     # minimum with opposite neighbor
        0x2779E0: "660fddf1",       # other shifted candidate + P1
        0x2779E4: "660f383af0",     # neighbor minimum
        0x2779E9: "660f383af3",     # minimum with min-cost + adaptive P2
        0x2779F8: "660fd9c2",       # normalize by min cost
        0x27AC16: "668b453066894746",  # stack literal -> StereoParams+0x46
        0x27AC22: "f30f115f48",     # xmm3 -> StereoParams+0x48
    }
    for va, expected_hex in byte_guards.items():
        expected = bytes.fromhex(expected_hex)
        require(
            STATIC.bytes_at(data, mapping, va, len(expected)) == expected,
            f"opcode drift at 0x{va:x}",
        )

    constants = f32s(STATIC.bytes_at(data, mapping, 0x5DA920, 8))
    require(constants == (24.0, 500.0), f"unexpected 0x5da920 constants {constants}")
    numerator = f32s(STATIC.bytes_at(data, mapping, 0x5DB370, 4))[0]
    require(
        struct.pack("<f", numerator) == struct.pack("<f", f32(math.log2(math.e) / 3.0)),
        f"0x5db370 is not float32 log2(e)/3: {numerator}",
    )
    scales = tuple(f32(numerator / f32(value)) for value in (6.0, 16.0, 16.0))
    require(
        struct.pack("<4f", *scales, 0.0).hex() == EXPECTED_SCALE_HEX,
        f"derived guide scales changed: {scales}",
    )
    return digest, scales


def index5_constructor(report: dict) -> dict:
    samples = [
        sample
        for sample in report["samples"]
        if sample["site"] == "index_setter_26bbd0"
        and sample.get("incoming_index_esi") == 5
        and sample.get("matching_constructor_params")
    ]
    require(len(samples) == 1, f"{report['label']}: expected one index-5 constructor")
    return samples[0]["matching_constructor_params"]


def verify_constructor_capture(filename: str) -> None:
    path = CTOR_ROOT / filename
    require(path.exists(), f"missing constructor report {path}")
    report = json.loads(path.read_text())
    require(report["process"]["state"] == "exited", f"{filename}: process state")
    require(report["process"]["exit_status"] == 0, f"{filename}: process exit")
    require(not report["errors"], f"{filename}: errors {report['errors']}")
    params = index5_constructor(report)
    require(params["u16"][0x46 // 2] == 1, f"{filename}: StereoParams+0x46")
    require(params["f32"][0x48 // 4] == 500.0, f"{filename}: StereoParams+0x48")
    require(
        struct.pack("<4f", *params["f32"][0x50 // 4 : 0x60 // 4]).hex()
        == EXPECTED_SCALE_HEX,
        f"{filename}: StereoParams+0x50",
    )


def verify_live_tier(tier: str) -> str:
    term_path = TERM_ROOT / f"xmm3_term_step_{tier}.json"
    xmm4_path = XMM4_ROOT / f"xmm4_origin_{tier}.json"
    require(term_path.exists(), f"missing {term_path}")
    require(xmm4_path.exists(), f"missing {xmm4_path}")
    term = json.loads(term_path.read_text())
    xmm4 = json.loads(xmm4_path.read_text())
    for label, report in (("term", term), ("xmm4", xmm4)):
        require(report["capture_complete"], f"{tier}: {label} capture")
        require(not report["errors"], f"{tier}: {label} errors")
        require(report["target_index"] == 5, f"{tier}: {label} target")

    fields = term["packet"]["table"]["target_stack_context"]["object_fields"]
    require(fields["u16_0x56"] == 1, f"{tier}: live P1")
    require(fields["f32_0x58"] == 500.0, f"{tier}: live P2/P1 scale")
    require(fields["bytes_0x60_0x70_hex"] == EXPECTED_SCALE_HEX, f"{tier}: guide scales")

    inputs = xmm4["packet"]["table"]["xmm4_inputs"]
    require(inputs["object_plus_0x60_hex"] == EXPECTED_SCALE_HEX, f"{tier}: xmm4 scales")
    masks = xmm4["packet"]["table"]["xmm_hex"]
    require(
        masks["xmm10"] == "ffffff7fffffff7fffffff7f00000000",
        f"{tier}: absolute-value mask",
    )
    require(
        masks["xmm12"] == "00000080000000800000008000000080",
        f"{tier}: negative exponent sign mask",
    )
    return f"{tier}: OK P1=1 P2_over_P1=500 guide_decay={EXPECTED_SCALE_HEX}"


def main() -> None:
    digest, scales = verify_static()
    verify_constructor_capture("ctor_28mm_narrow.json")
    verify_constructor_capture("ctor_28mm_no_lris_narrow.json")
    print(
        f"static_index5_sgm_parameter_origin=OK libcp={digest} "
        f"guide_decay={','.join(f'{value:.9f}' for value in scales)}"
    )
    for tier in TIERS:
        print(verify_live_tier(tier))
    print("index5_sgm_parameter_origin=OK")


if __name__ == "__main__":
    main()
