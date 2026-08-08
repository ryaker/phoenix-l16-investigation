#!/usr/bin/env python3
"""Verify the installed Lab-L unsharp formula and four-focal live packets."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/unsharp_formula"
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
TIERS = ("unit1_28mm", "unit1_35mm", "unit1_70mm", "unit1_150mm")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("unsharp_static_helper", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def verify_static():
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == static.LIBCP_SHA256, f"libcp digest changed: {digest}")
    hashes = {
        (0x35F5C0, 0x35F8A2): "fef1ef2f88650ef66d1c0b2bfd1c6a80fc100be2538867c2e386f85238b105cb",
        (0x35F8F0, 0x35FA4F): "ddafdff2914856a03c19aec4419d27c21d09cd8a7b786992bbc4daa7e151f7bd",
        (0x3607A0, 0x3609F3): "a3e05ec5751ee4563a02da29e5032a0cfb0a47ca0f271651d7c65fdb27e5736e",
        (0x3608B0, 0x3608DB): "7115d69f7332ad6049f540bd9b1d2c4b5dcfec1a14913dafdc02f4066af23b96",
        (0x361E20, 0x3625F0): "162e751cf276234f9d993d23d3118a7155f20e783bb3aacfb522c0bcbf11e0ab",
        (0x341040, 0x341090): "bef7113566b338728c6dc7a148c310b95c08798bdd599cec5cf2c9a6cca1d16f",
        (0x319436, 0x31945E): "68736013d6d1b773247d8d91c69fc6ee8d0dce6361e39d75c9859ee01563c259",
        (0x33EB60, 0x33EB80): "9daddfad050427ef68c405e516c9616793dc5b629342730a3efc2729447c6219",
    }
    for (start, end), expected in hashes.items():
        actual = hashlib.sha256(static.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed: {actual}")
    constants = {
        0x5FC0A0: (-20.0,) * 4,
        0x5FC0B0: (20.0,) * 4,
        0x5FC0C0: (116.0,) * 4,
        0x5FC0D0: (-16.0,) * 4,
        0x5FC0E0: (500.0,) * 4,
        0x5FC0F0: (200.0,) * 4,
    }
    for va, expected in constants.items():
        actual = struct.unpack("<4f", static.bytes_at(data, mapping, va, 16))
        require(actual == expected, f"constant 0x{va:x} changed: {actual}")
    require(
        static.bytes_at(data, mapping, 0x5FD0B0, 37) == b"N2lt8Internal18SharpenLineFactoryIfEE",
        "SharpenLineFactory RTTI changed",
    )
    require(
        static.bytes_at(data, mapping, 0x5FD600, 57) == b"N2lt8Internal14LabLineFactoryINS_5ImageINS_8vec4x32fEEEEE",
        "LabLineFactory RTTI changed",
    )
    vtable = struct.unpack("<5Q", static.bytes_at(data, mapping, 0x669108, 40))
    require(vtable == (0x35F480, 0x35F4E0, 0x35F550, 0x35F560, 0x35E930), f"sharpen vtable changed: {vtable}")
    core = static.bytes_at(data, mapping, 0x3608B0, 0x2B)
    for opcode in (b"\x0f\x5c", b"\x0f\x59", b"\x0f\x5f", b"\x0f\x5d", b"\x0f\x58"):
        require(opcode in core, f"missing unsharp core opcode {opcode.hex()}")
    print(f"static_unsharp_formula=OK libcp={digest} domain=Lab_L clamp=-20,+20")


def decode_configs(report):
    configs = []
    for raw_hex in report["constructor_config_counts"]:
        raw = bytes.fromhex(raw_hex)
        require(len(raw) == 20, f"bad constructor packet: {raw_hex}")
        configs.append(struct.unpack("<5f", raw))
    return configs


def verify_runtime():
    for tier in TIERS:
        report = json.loads((RUN / f"{tier}.json").read_text())
        require(report["process"]["exit_status"] == 0, f"{tier}: render did not exit 0")
        require(not report["errors"], f"{tier}: probe errors {report['errors']}")
        require(report["counts"]["constructor"] > 1000, f"{tier}: sparse constructor census")
        combine = report["combine"]
        require(combine is not None, f"{tier}: missing combine packet")
        require(combine["base_source_rtti"]["name"] == "N2lt8Internal14LabLineFactoryINS_5ImageINS_8vec4x32fEEEEE", f"{tier}: base RTTI")
        require(combine["dog_positive_rtti"]["name"] == "N2lt8Internal15ConvLineFactoryIfLi3EEE", f"{tier}: positive RTTI")
        require(combine["dog_negative_rtti"]["name"] == "N2lt8Internal15ConvLineFactoryIfLi7EEE", f"{tier}: negative RTTI")
        expected = []
        for base, difference in zip(combine["base_xmm2"], combine["difference_xmm3"]):
            boost = f32(f32(combine["amount_0x68"]) * f32(difference))
            boost = max(-20.0, min(20.0, boost))
            expected.append(f32(f32(base) + f32(boost)))
        require(expected == combine["output_xmm4"], f"{tier}: combine mismatch {expected} != {combine['output_xmm4']}")
        configs = decode_configs(report)
        amounts = {item[3] for item in configs}
        require(amounts == {0.5, 1.0}, f"{tier}: configured amount set changed: {amounts}")
        require(combine["amount_0x68"] == 1.0, f"{tier}: first live amount changed")
        print(f"runtime_unsharp_formula={tier}=OK constructors={report['counts']['constructor']} configs={len(configs)} amount={combine['amount_0x68']}")


def verify_kernel_census():
    report = json.loads((RUN / "unit1_28mm.json").read_text())
    kernels = report["generated_kernels"]
    require(report["counts"]["gaussian5_return"] == 0, "unexpected 5-tap sharpen kernel")
    require(len(kernels) == 14, f"unexpected unique generated-kernel count: {len(kernels)}")
    by_config = {}
    for item in kernels:
        config = struct.unpack("<5f", bytes.fromhex(item["config_hex_0x00_0x10"]))
        by_config.setdefault(config, {})[item["role"]] = (item["taps"], tuple(item["coefficients"]))
    require(len(by_config) == 7, f"unexpected config/kernel groups: {len(by_config)}")
    main = by_config[(1.0, f32(0.9), 0.5, 1.0, 1.0)]
    require(main["positive"] == (3, (0.2740686237812042, 0.45186275243759155, 0.2740686237812042)), "main positive kernel")
    require(main["negative"][0] == 7, "main negative tap count")
    neutral = by_config[(1.0, 0.0, 0.0, 1.0, 0.5)]
    require(neutral["positive"] == (3, (0.10650697350502014, 0.7869859933853149, 0.10650697350502014)), "neutral positive kernel")
    require(neutral["negative"] == (3, (0.24370792508125305, 0.5125841498374939, 0.24370792508125305)), "neutral negative kernel")
    dynamic = [roles for config, roles in by_config.items() if config[0] == 1.5]
    require(len(dynamic) == 5, f"dynamic config count changed: {len(dynamic)}")
    require(len({roles["positive"] for roles in dynamic}) == 1, "dynamic positive kernels differ")
    require(len({roles["negative"] for roles in dynamic}) == 1, "dynamic negative kernels differ")
    require(all(roles["positive"][0] == 3 and roles["negative"][0] == 7 for roles in dynamic), "dynamic tap family")
    properties = {(item["address"], item["name"]) for item in report["properties"]}
    require((0x319436, "sharpening") in properties, "public sharpening property not observed")
    require((0x319459, "sharpening_scale") in properties, "public sharpening_scale property not observed")
    print("runtime_unsharp_kernel_census=OK configs=7 generated=3/7tap public=sharpening,sharpening_scale")


def main():
    verify_static()
    verify_runtime()
    verify_kernel_census()
    print("unsharp_formula_verification=OK")


if __name__ == "__main__":
    main()
