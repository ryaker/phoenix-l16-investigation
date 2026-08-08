#!/usr/bin/env python3
"""Verify the installed and four-focal final-stage constants."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
RUN_ROOT = ROOT / "runs/final_stage_constants"
TIERS = ("28mm", "35mm", "70mm", "150mm")
GAUSSIAN7_HEX = (
    "4fd6403d2838f43d1c44553e3b6a803e"
    "1c44553e2838f43d4fd6403d"
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


STATIC = load_module("final_stage_static_helpers", STATIC_PATH)


def u64(raw: bytes) -> int:
    return struct.unpack("<Q", raw)[0]


def rtti_name(data: bytes, mapping, address_point: int) -> bytes:
    typeinfo = u64(STATIC.bytes_at(data, mapping, address_point - 8, 8))
    name = u64(STATIC.bytes_at(data, mapping, typeinfo + 8, 8))
    return STATIC.cstring(data, mapping, name)


def range_hash(data: bytes, mapping, start: int, end: int) -> str:
    return hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()


def verify_static() -> tuple[tuple[float, ...], tuple[float, ...]]:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    wavelet_raw = STATIC.bytes_at(data, mapping, 0x5FDB10, 16)
    require(
        wavelet_raw.hex() == "abaaaabbabaa2abcabaaaabcabaa2abd",
        "wavelet detail table changed",
    )
    wavelet = struct.unpack("<4f", wavelet_raw)

    abs_mask = STATIC.bytes_at(data, mapping, 0x5A81F0, 16)
    require(abs_mask == struct.pack("<4I", *([0x7FFFFFFF] * 4)), "abs mask changed")

    expected_rtti = {
        0x6692E8: b"N2lt8Internal15ConvLineFactoryIfLi7EEE",
        0x669338: b"N2lt8Internal18WrappedLineFactoryINS0_11HConvBufferIfLi7EEEfEE",
        0x65A568: (
            b"NSt3__110__function6__funcIZN2lt8Internal12_GLOBAL__N_1"
            b"28ImageDenoiseBilateralGenericILi5ELb1EEEvRNS2_5ImageINS2_"
            b"8vec4x32fEEERKS8_SB_RKS7_RKNS2_9RectangleIiEEEUlSH_iE_"
            b"NS_9allocatorISI_EEFvSH_iEEE"
        ),
        0x668920: (
            b"NSt3__110__function6__funcIZN2lt8Internal20ImageDenoisePatchNLM"
            b"ILi4EEEvRNS2_5ImageINS2_8vec4x32fEEERKS7_SA_RKS6_iiEUlRKNS2_"
            b"9RectangleIiEEiE_NS_9allocatorISH_EEFvSG_iEEE"
        ),
        0x6689A8: (
            b"NSt3__110__function6__funcIZN2lt8Internal20ImageDenoisePatchNLM"
            b"ILi4EEEvRNS2_5ImageINS2_8vec4x32fEEERKS7_SA_RKS6_iiEUliiiE_"
            b"NS_9allocatorISD_EEFviiiEEE"
        ),
    }
    for address_point, expected in expected_rtti.items():
        require(
            rtti_name(data, mapping, address_point) == expected,
            f"RTTI changed at 0x{address_point:x}",
        )

    hashes = {
        (0x96980, 0x96D37): "6b2f5f8123adc0611dd283f65481b1d2914f2480b140d56b46a7cfe0770e123e",
        (0x3588F0, 0x3589BA): "963da055d2d4b297435344859ca0bbc43e3f929420d52852a26c444e02572332",
        (0x2F78E0, 0x2F860E): "a91135d88bd85ee035e8711431cca22ae38a29700c8513ba45f4c8fffc7fc368",
        (0x3066D0, 0x306D40): "bfebe7619117a2db022e28894a2dbc2456fe8f2d255306939a508675d91b3da8",
        (0x3070E0, 0x307D86): "0164b7e286c1d2b09d368ab6b21a6aed5b123908f2a715eb5a03339fb9d47125",
        (0x318A7D, 0x318BC9): "9f88ec20da20ca0dd9bb365567ab56b7212636e681b6b16f32856e04d8612197",
    }
    for (start, end), expected in hashes.items():
        require(
            range_hash(data, mapping, start, end) == expected,
            f"static range 0x{start:x}..0x{end:x} changed",
        )

    require(
        STATIC.bytes_at(data, mapping, 0x2F8418, 5) == bytes.fromhex("ba05000000"),
        "bilateral five-row loop changed",
    )
    property_names = (
        b"nlm_denoiser",
        b"step_size",
        b"window_size",
        b"pyramid_size",
        b"min_luma_std",
        b"patch_size",
        b"chroma_boost",
        b"fast_search",
        b"threshold_multiplier",
    )
    for name in property_names:
        require(name + b"\0" in data, f"missing installed property name {name!r}")

    gaussian = struct.unpack("<7f", bytes.fromhex(GAUSSIAN7_HEX))
    print(
        "static_final_stage_constants=OK "
        f"libcp={digest} wavelet={','.join(f'{v:.12g}' for v in wavelet)} "
        "abs_mask=0x7fffffff bilateral=uniform_5x5"
    )
    return wavelet, gaussian


def verify_runtime(tier: str) -> None:
    path = RUN_ROOT / f"unit1_{tier}.json"
    require(path.exists(), f"missing runtime report {path}")
    report = json.loads(path.read_text())
    require(report["process_exit_status"] == 0, f"{tier}: process exit")
    require(report["process_state"] == 10, f"{tier}: process state")
    require(not report["errors"], f"{tier}: errors {report['errors']}")
    require(len(report["gaussian7"]) == 1, f"{tier}: Gaussian capture count")
    coefficients = report["gaussian7"][0]["coefficients"]
    require(coefficients["read_ok"], f"{tier}: Gaussian read")
    require(coefficients["hex"] == GAUSSIAN7_HEX, f"{tier}: Gaussian coefficients")

    nlm = report["patch_nlm"]
    require(len(nlm) == 16, f"{tier}: NLM sample count")
    for index, sample in enumerate(nlm):
        require(sample["arg0_r8"] == 5, f"{tier}: NLM window at sample {index}")
        require(sample["arg1_r9"] == 2, f"{tier}: NLM step at sample {index}")
        config = sample["config"]
        require(config["read_ok"], f"{tier}: config read at sample {index}")
        require(
            struct.unpack("<3I", bytes.fromhex(config["hex"][:24])) == (5, 5, 2),
            f"{tier}: public config prefix at sample {index}",
        )
    print(f"{tier}: OK gaussian7={GAUSSIAN7_HEX} window_size=5 search_radius=2 step_size=2")


def main() -> None:
    wavelet, gaussian = verify_static()
    require(
        tuple(struct.pack("<f", value) for value in wavelet)
        == tuple(struct.pack("<f", -1.0 / denominator) for denominator in (192, 96, 48, 24)),
        "wavelet values are not the exact float32 dyadic sequence",
    )
    for tier in TIERS:
        verify_runtime(tier)
    print("gaussian7=" + ",".join(f"{value:.12g}" for value in gaussian))
    print("final_stage_constants=OK")


if __name__ == "__main__":
    main()
