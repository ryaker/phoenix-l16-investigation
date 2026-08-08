#!/usr/bin/env python3
"""Verify public sharpen packet custody and the installed kernel-width formula."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/unsharp_formula"
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
TIERS = ("unit1_28mm", "unit1_35mm", "unit1_70mm", "unit1_150mm")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("unsharp_packet_static_helper", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def clamp01(value):
    return max(0.0, min(1.0, value))


def unsharp_sigmas(config):
    """Replay 0x35f5c0 in explicit float32 order.

    Config fields are (sensor_analog_gain, grain_power, grain_sigma,
    sharpening, sharpening_scale). Grain fields are carried by the shared
    packet but are not read by this constructor.
    """

    gain, _grain_power, _grain_sigma, amount, scale = config

    if gain >= f32(7.75):
        positive_base = f32(1.0)
        radial_a = f32(1.1)
        radial_b = f32(1.0)
        positive_alt = f32(0.5)
    elif gain >= f32(4.0):
        t = clamp01(f32(f32(gain + f32(-4.0)) * f32(0.2857142984867096)))
        positive_base = f32(f32(f32(-0.10000002384185791) * t) + f32(1.1))
        radial_a = f32(
            f32(f32(f32(-0.4000000059604645) * t) + f32(0.5))
            + positive_base
        )
        positive_alt = f32(
            f32(f32(-0.050000011920928955) * t) + f32(0.550000011920929)
        )
        radial_b = f32(f32(0.5) + positive_alt)
    elif gain >= f32(2.0):
        t = clamp01(f32(f32(gain + f32(-2.0)) * f32(0.5)))
        positive_base = f32(
            f32(1.0) + f32(f32(0.10000002384185791) * t)
        )
        radial_a = f32(
            f32(1.5) + f32(f32(0.10000002384185791) * t)
        )
        positive_alt = f32(
            f32(0.5) + f32(f32(0.050000011920928955) * t)
        )
        radial_b_lo = f32(
            f32(0.6000000238418579)
            + f32(f32(-0.10000002384185791) * t)
        )
        radial_b = f32(radial_b_lo + positive_alt)
    elif gain >= f32(1.0):
        t = clamp01(f32(gain + f32(-1.0)))
        positive_base = f32(1.0)
        radial_a = f32(
            f32(1.2999999523162842)
            + f32(f32(0.19999998807907104) * t)
        )
        positive_alt = f32(0.5)
        radial_b_lo = f32(
            f32(0.5) + f32(f32(0.10000002384185791) * t)
        )
        radial_b = f32(radial_b_lo + positive_alt)
    else:
        positive_base = f32(1.0)
        radial_a = f32(1.2999999523162842)
        radial_b = f32(1.0)
        positive_alt = f32(0.5)

    width_mix = clamp01(
        f32(f32(amount + f32(-4.0)) * f32(0.0833333358168602))
    )
    positive_delta = f32(positive_alt - positive_base)
    positive_unscaled = f32(f32(positive_delta * width_mix) + positive_base)
    radial_delta = f32(radial_b - radial_a)
    radial = f32(f32(radial_delta * width_mix) + radial_a)
    radial_sq = f32(radial * radial)
    positive_sq = f32(positive_unscaled * positive_unscaled)
    negative_unscaled = f32(math.sqrt(f32(positive_sq + radial_sq)))
    return f32(positive_unscaled * scale), f32(negative_unscaled * scale)


def verify_static():
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == static.LIBCP_SHA256, f"libcp digest changed: {digest}")

    hashes = {
        (0x31936E, 0x319472): "1e58750b4009c106885d14ad877893dfdb1d0b8bf1af747b729f8943d01b793e",
        (0x33EB40, 0x33EBA6): "0751cf22053bbc025f709bbc5e3fe2e7a308cc87cde468e068e1e7c73c733525",
        (0x341040, 0x341090): "bef7113566b338728c6dc7a148c310b95c08798bdd599cec5cf2c9a6cca1d16f",
        (0x3589C0, 0x358FCE): "e3d00ec17a3e4d782329c8a8880ef82dfdd264215cf65af1f9aeed27402ed192",
        (0x359E30, 0x35A13B): "7a872b98d2af4f6b4e91972f00a5fa35aa4f5e1e03439cc0c2fc0d3318a467fc",
        (0x35AC9A, 0x35AD04): "8b5c826c70336fa749053168944c16862c8e7319508e26742eb0f92a935100ca",
        (0x35B820, 0x35B875): "5d9f4ef49d43fb1f30fffc3b8531e582fc902a5348a8845df197d2c173e853ad",
        (0x35C498, 0x35C4F3): "3526c914c5b702e5e0468e6a2820640e048c4aff891df39ad0bc8b14920be773",
        (0x35D831, 0x35D893): "cadca79ef4f6ac5c0a1b30008765d75e8557a7fd3bb9cff040350a274caf0dbf",
        (0x35F5C0, 0x35F8A2): "fef1ef2f88650ef66d1c0b2bfd1c6a80fc100be2538867c2e386f85238b105cb",
        (0x35F8F0, 0x35FA4F): "ddafdff2914856a03c19aec4419d27c21d09cd8a7b786992bbc4daa7e151f7bd",
    }
    for (start, end), expected in hashes.items():
        actual = hashlib.sha256(static.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed: {actual}")

    closure_vtable = struct.unpack(
        "<8Q", static.bytes_at(data, mapping, 0x65E0B0, 64)
    )
    require(
        closure_vtable
        == (0x359D80, 0x359D90, 0x359DA0, 0x359DE0, 0x359E10, 0x359E20, 0x359E30, 0x35A190),
        f"sharpen closure vtable changed: {closure_vtable}",
    )

    constants = {
        0x5FBEB8: 116.0,
        0x5FBEBC: 0.9999989867210388,
        0x5FBEC0: 1.0000009536743164,
        0x5FBE8C: 0.2857142984867096,
        0x5FBE90: 7.75,
        0x5FBE94: -0.10000002384185791,
        0x5FBE98: -0.4000000059604645,
        0x5FBE9C: -0.050000011920928955,
        0x5FBEA0: 0.550000011920929,
        0x5FBEA4: 0.050000011920928955,
        0x5FBEA8: 0.19999998807907104,
        0x5FBEAC: 0.0833333358168602,
    }
    for address, expected in constants.items():
        actual = struct.unpack("<f", static.bytes_at(data, mapping, address, 4))[0]
        require(actual == expected, f"constant 0x{address:x} changed: {actual}")

    print(
        "static_unsharp_packet_origin=OK "
        "packet=sensor_analog_gain,grain_power,grain_sigma,sharpening,sharpening_scale "
        "route=saturation,vibrance"
    )


def verify_runtime_packets():
    property_union = set()
    for tier in TIERS:
        report = json.loads((RUN / f"{tier}.json").read_text())
        require(report["process"]["exit_status"] == 0, f"{tier}: render did not exit 0")
        require(not report["errors"], f"{tier}: probe errors {report['errors']}")
        property_union.update((item["address"], item["name"]) for item in report["properties"])
        for raw_hex in report["constructor_config_counts"]:
            config = struct.unpack("<5f", bytes.fromhex(raw_hex))
            positive_sigma, negative_sigma = unsharp_sigmas(config)
            require(positive_sigma > 0.0, f"{tier}: nonpositive positive sigma {config}")
            require(negative_sigma > positive_sigma, f"{tier}: unordered sigmas {config}")
        print(
            f"runtime_unsharp_packet={tier}=OK "
            f"unique={len(report['constructor_config_counts'])}"
        )

    expected_properties = {
        (0x31939B, "saturation"),
        (0x3193BE, "vibrance"),
        (0x3193E1, "grain_power"),
        (0x319400, "grain_sigma"),
        (0x319436, "sharpening"),
        (0x319459, "sharpening_scale"),
    }
    require(
        expected_properties <= property_union,
        f"missing public property observations: {expected_properties - property_union}",
    )

    report = json.loads((RUN / "unit1_28mm.json").read_text())
    expected_sigmas = {
        (1.0, f32(0.9), 0.5, 1.0, 1.0): (1.0, 1.6401219367980957),
        (1.0, 0.0, 0.0, 1.0, 0.5): (0.5, 0.8200609683990479),
    }
    for config, expected in expected_sigmas.items():
        require(unsharp_sigmas(config) == expected, f"sigma replay changed for {config}")
    dynamic = []
    for raw_hex in report["constructor_config_counts"]:
        config = struct.unpack("<5f", bytes.fromhex(raw_hex))
        if config[0] == 1.5:
            dynamic.append(unsharp_sigmas(config))
    require(
        len(dynamic) == 5 and set(dynamic) == {(1.0, 1.720465064048767)},
        f"dynamic sigma replay changed: {dynamic}",
    )
    print("runtime_unsharp_sigma_replay=OK unit1_28mm_families=7")


def main():
    verify_static()
    verify_runtime_packets()
    print("unsharp_packet_origin_verification=OK")


if __name__ == "__main__":
    main()
