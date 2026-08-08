#!/usr/bin/env python3
"""Verify four-focal denoise/CNR route-census reports plus Unit-2 control."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/denoise_route_census"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
TIERS = ("28mm", "35mm", "70mm", "150mm")
WIDE = {"28mm", "35mm"}
TELE = {"70mm", "150mm"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("denoise_static_helpers", STATIC_PATH)


def u64(raw: bytes) -> int:
    return struct.unpack("<Q", raw)[0]


def rtti_name(data: bytes, mapping, address_point: int) -> bytes:
    typeinfo = u64(STATIC.bytes_at(data, mapping, address_point - 8, 8))
    name = u64(STATIC.bytes_at(data, mapping, typeinfo + 8, 8))
    return STATIC.cstring(data, mapping, name)


def range_hash(data: bytes, mapping, start: int, end: int) -> str:
    return hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()


def verify_static() -> None:
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == STATIC.LIBCP_SHA256, f"libcp digest changed: {digest}")

    rtti = {
        0x65AC10: b"ColorNoiseReduction",
        0x65DE38: b"setColorNoiseReduction",
        0x65DEB8: b"setColorNoiseReduction",
        0x65DF28: b"setColorNoiseReduction",
    }
    for address_point, needle in rtti.items():
        name = rtti_name(data, mapping, address_point)
        require(needle in name, f"RTTI at 0x{address_point:x} changed: {name!r}")

    hashes = {
        (0x34B3F0, 0x34B808): "6f7ac1fc4faf18ccc4ef5c9b70dff4336a807ff53194efcb357ba25e467fbf0d",
        (0x34B8A0, 0x34B8AE): "3f0d36a7821c312ba21322f86d38fd3c7abd516b1623d140b83517be02faa8c0",
        (0x34B970, 0x34B97E): "da807245a672e5e59053caf759203375711558d3125ceadaf4891865891647a0",
        (0x307EE0, 0x308459): "dfbaee4a6921cbac9c4d6da49e2306c19bb4e18710ab1f805dbddd6d64dcf254",
        (0x308520, 0x308567): "e464875586d0a4f45738567d87dec65fabf39935a8d248fc885ba9a3a54b58c6",
        (0x3085A0, 0x308D00): "9dd68fec69d6f63e5346f938d1ea7516bdab909050ef0c8c2015c159f99367d7",
        (0x2F53D0, 0x2F5EF0): "14bf861649acec9c7e0375499a05a3b232104f74f1e496df853502fa96d61474",
        (0x2F6420, 0x2F68A0): "5f28dc1fdbd035a13e71867718f6865cc1b3c43ebfa70869526f090ae2b7cbb0",
        (0x2FB320, 0x2FC11F): "c6a6926cffdfa8f79b8f6c0caa4a65066ab0b7f42f7ce4e15dc95a1ed65b7861",
        (0x2FD070, 0x2FDCE0): "c4660f0f361c2a4e9886d125197181dab9f50b7757c5ce3032197c65f547860a",
        (0x3066D0, 0x306D40): "bfebe7619117a2db022e28894a2dbc2456fe8f2d255306939a508675d91b3da8",
        (0x3070E0, 0x307D90): "862f185f5d4cd3d365ebf5ff65091520b2697cdd9d83a1e8bf4c42a4b2a5ddbb",
        (0x307D90, 0x307EA7): "1415cf342baae4666c4a15d84d99acb004eff16de46a3c71dd042643de8d5cab",
    }
    for (start, end), expected in hashes.items():
        actual = range_hash(data, mapping, start, end)
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed")

    print(f"static_denoise_route=OK libcp={digest}")


def load_report(tier: str, suffix: str) -> dict:
    return load_sample_report(f"unit1_{tier}", suffix)


def load_sample_report(sample: str, suffix: str) -> dict:
    path = RUN_ROOT / f"{sample}_{suffix}.json"
    require(path.exists(), f"missing report {path}")
    report = json.loads(path.read_text())
    require(report["process"]["exit_status"] == 0, f"{path.name}: process exit")
    require(report["process"]["state"] == "exited", f"{path.name}: process state")
    require(not report["drive_hit_step_cap"], f"{path.name}: drive step cap")
    require(not report["errors"], f"{path.name}: errors {report['errors']}")
    return report


def count(report: dict, name: str) -> int:
    return int(report["counts"].get(name, 0))


def nonzero_names(report: dict) -> set[str]:
    return {name for name, value in report["counts"].items() if value}


def first_site(report: dict, names: set[str]) -> str:
    for event in report["events"]:
        if event["site"] in names:
            return event["site"]
    raise AssertionError(f"{report['label']}: no event in {names}")


def verify_cnr_report(tier: str, sample: str | None = None, low_endpoint: int = 42) -> None:
    sample = sample or f"unit1_{tier}"
    report = load_sample_report(sample, "cnr")
    expected = {
        "CNR_effective_0x34b3f0",
        "ColorNoiseReduction_body_0x307ee0",
        "ColorNoiseReduction_callback_0x308520",
        "ColorNoiseReduction_worker_0x3085a0",
        "setCNR_0x34b3b0",
        "setCNR_0x34b970" if tier in WIDE else "setCNR_0x34b8a0",
    }
    require(nonzero_names(report) == expected, f"{sample}: CNR nonzero set changed")
    require(
        first_site(report, {"setCNR_0x34b970", "setCNR_0x34b8a0"})
        == ("setCNR_0x34b970" if tier in WIDE else "setCNR_0x34b8a0"),
        f"{sample}: first CNR family changed",
    )
    for name in expected:
        require(count(report, name) > 0, f"{sample}: expected live CNR site {name}")

    body_samples = [
        sample["packet"]["cnr_body_entry"]
        for sample in report["samples"]
        if "cnr_body_entry" in sample["packet"]
    ]
    require(body_samples, f"{sample}: missing CNR body samples")
    for entry in body_samples:
        require(entry["xmm0_f32"] == 1.0, "CNR xmm0")
        require(entry["xmm1_f32"] == 1.0, "CNR xmm1")
        require(entry["r9d"] == low_endpoint, "CNR r9d")
        require(entry["stack_i32_arg0"] == 1023, "CNR stack arg")

    effective_samples = [
        sample["packet"]["cnr_effective_entry"]
        for sample in report["samples"]
        if "cnr_effective_entry" in sample["packet"]
    ]
    require(effective_samples, "missing CNR effective samples")
    for entry in effective_samples:
        require(entry["object_params"]["f32_0x15d8"] == 1.0, "object 0x15d8")
        require(entry["object_params"]["f32_0x1624"] == 1.0, "object 0x1624")
    print(
        f"{report['label']}: CNR route OK first="
        f"{'0x34b970' if tier in WIDE else '0x34b8a0'} "
        f"args=(1,1,{low_endpoint},1023)"
    )


def verify_denoise_algo_report(
    tier: str, sample: str | None = None, extra_expected: set[str] | None = None
) -> None:
    sample = sample or f"unit1_{tier}"
    report = load_sample_report(sample, "denoise_algo")
    expected = {
        "helper_chain_0x2f53d0",
        "callback_selector_0x2f6420",
        "bilateral_arm_0x2fb320",
        "ImageDenoiseNLM_positive_0x3066d0",
        "PatchNLM_adapter_0x3070a0",
        "PatchNLM_body_0x3070e0",
        "PatchNLM_normalize_0x307d90",
    }
    expected |= extra_expected or set()
    require(nonzero_names(report) == expected, f"{sample}: denoise algorithm set changed")
    require(
        first_site(report, {"helper_chain_0x2f53d0"}) == "helper_chain_0x2f53d0",
        f"{sample}: first helper changed",
    )
    for name in expected:
        require(count(report, name) > 0, f"{sample}: expected live denoise site {name}")
    if extra_expected:
        print(
            f"{report['label']}: denoise algorithms OK "
            f"selected=0x2fb320+PatchNLM extra={sorted(extra_expected)}"
        )
    else:
        print(f"{report['label']}: denoise algorithms OK selected=0x2fb320+PatchNLM")


def verify_setdenoise_report(tier: str, sample: str | None = None) -> None:
    sample = sample or f"unit1_{tier}"
    report = load_sample_report(sample, "setdenoise")
    expected = {
        "setDenoising_51_0x345920",
        "setDenoising_52_0x345a10",
        "setDenoising_55_0x345c80" if tier in WIDE else "setDenoising_53_0x345ae0",
    }
    require(nonzero_names(report) == expected, f"{sample}: setDenoising set changed")
    require(
        first_site(report, {"setDenoising_55_0x345c80", "setDenoising_53_0x345ae0"})
        == ("setDenoising_55_0x345c80" if tier in WIDE else "setDenoising_53_0x345ae0"),
        f"{sample}: first setDenoising family changed",
    )
    for name in expected:
        require(count(report, name) > 0, f"{sample}: expected setDenoising site {name}")
    print(
        f"{report['label']}: setDenoising OK first="
        f"{'0x345c80' if tier in WIDE else '0x345ae0'} shared=0x345920,0x345a10"
    )


def verify_unit2_control() -> None:
    verify_cnr_report("35mm", "unit2_35mm", low_endpoint=43)
    verify_denoise_algo_report(
        "35mm",
        "unit2_35mm",
        extra_expected={"bilateral_arm_0x2fd070"},
    )
    verify_setdenoise_report("35mm", "unit2_35mm")


def main() -> None:
    verify_static()
    for tier in TIERS:
        verify_cnr_report(tier)
        verify_denoise_algo_report(tier)
        verify_setdenoise_report(tier)
    verify_unit2_control()
    print("denoise_route_census=OK")


if __name__ == "__main__":
    main()
