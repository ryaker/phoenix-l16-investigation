#!/usr/bin/env python3
"""Verify the installed per-payload pipeline stage order and retained liveness."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/src1_virtual_target_census"
CLARITY_RUN = ROOT / "runs/laplacian_clarity/laplacian_clarity_28mm.json"
HELPER = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


spec = importlib.util.spec_from_file_location("pipeline_stage_static_helper", HELPER)
require(spec is not None and spec.loader is not None, f"cannot import {HELPER}")
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


PERMUTATION = (0x000, 0x040, 0x200, 0x080, 0x100, 0x140, 0x180, 0x0C0,
               0x1C0, 0x240, 0x280, 0x2C0, 0x300, 0x340, 0x380, 0x3C0)

# The setup instruction locates the 0x40-byte record carrying each setter's
# std::function at record+0x20. The record's position in PERMUTATION is its
# execution index.
SETUP_PREFIXES = {
    0x329BCB: "4c8dbb000500004c",  # Bayer default-0, record +0x080, index 3
    0x329D85: "4c8dbb4007000044",  # Bayer default-1, record +0x2c0, index 11
    0x329E52: "4c8dbbe00000004c",  # BayerFloat default-0, +0x080, index 3
    0x32A086: "4c8dbb2003000044",  # BayerFloat default-1, +0x2c0, index 11
    0x32A454: "4c8dbb400d00004c",  # Color default-0, +0x080, index 3
    0x32A688: "4c8dbb800f000044",  # Color default-1, +0x2c0, index 11
    0x32B7F8: "4c8dbbc00400004c",  # Bayer hot pixel, +0x040, index 1
    0x32C120: "488d83c005000048",  # Bayer cross talk, +0x140, index 5
    0x32C668: "4c8db3a001000048",  # BayerFloat cross talk, +0x140, index 5
    0x32E089: "498bbc2420060000",  # Bayer demosaic callable +0x20, index 6
    0x32E199: "498bbc2400020000",  # BayerFloat demosaic callable +0x20, index 6
    0x3307BC: "498d8d4006000048",  # Bayer adaptive desaturation, index 8
    0x330C21: "4d8db52002000049",  # BayerFloat adaptive desaturation, index 8
    0x330FDA: "4d8db5800e000049",  # Color adaptive desaturation, index 8
    0x331448: "4c8dbb800600004c",  # Bayer highlight restore, index 2
    0x332554: "4d8dbdc006000049",  # Bayer denoise, index 9
    0x332C73: "498d9da002000049",  # BayerFloat denoise, index 9
    0x33366B: "498d9d000f000049",  # Color denoise, index 9
    0x33492A: "4d8daf8007000049",  # Bayer lens shading, index 12
    0x334A9D: "4d8daf6003000049",  # BayerFloat lens shading, index 12
    0x339E4D: "4d8dbc2440080000",  # Bayer tone map, index 15
    0x33A904: "4d8dbc2420040000",  # BayerFloat tone map, index 15
    0x33AA5F: "4d8dbc2480100000",  # Color tone map, index 15
    0x33D780: "4c8da34005000048",  # Bayer CNR, index 7
    0x33DB5E: "4c8da32001000048",  # BayerFloat CNR, index 7
    0x33DD72: "4c8da3800d000048",  # Color CNR, index 7
}

VTABLES = {
    # vtable address point: (operator target, required RTTI substring)
    0x65AE40: (0x340A30, "PipelineC1EvE3$_0"),
    0x65AEC8: (0x340B00, "PipelineC1EvE3$_1"),
    0x65B3C8: (0x341770, "setHotPixelRemoval"),
    0x65B5C8: (0x342280, "setCrossTalkCorrection"),
    0x65B9C8: (0x342C60, "setDemosaicking"),
    0x65BDB8: (0x343620, "setAdaptiveDesaturation"),
    0x65BF18: (0x343E10, "setHighlightRestore"),
    0x65C818: (0x345A10, "setDenoising"),
    0x65CA18: (0x345D50, "setLensShading"),
    0x65D978: (0x34A610, "setToneMapping"),
    0x65DE38: (0x34B3B0, "setColorNoiseReduction"),
    0x65AF48: (0x340BF0, "PipelineC1EvE3$_2"),
    0x65AFC8: (0x340CC0, "PipelineC1EvE3$_3"),
    0x65B648: (0x342360, "setCrossTalkCorrection"),
    0x65BA48: (0x3430D0, "setDemosaicking"),
    0x65BE38: (0x3438D0, "setAdaptiveDesaturation"),
    0x65C898: (0x345AE0, "setDenoising"),
    0x65CA98: (0x345F30, "setLensShading"),
    0x65D9F8: (0x34A780, "setToneMapping"),
    0x65DEB8: (0x34B8A0, "setColorNoiseReduction"),
    0x65B148: (0x340F70, "PipelineC1EvE3$_6"),
    0x65B1C8: (0x341040, "PipelineC1EvE3$_7"),
    0x65BEA8: (0x343B80, "setAdaptiveDesaturation"),
    0x65C998: (0x345C80, "setDenoising"),
    0x65DA68: (0x34A8F0, "setToneMapping"),
    0x65DF28: (0x34B970, "setColorNoiseReduction"),
    0x65D5C8: (0x3491E0, "setToneAdjust"),
    0x65D648: (0x349460, "setToneAdjust"),
    0x65D6B8: (0x3496E0, "setToneAdjust"),
}

SITES = {
    "virtual_0x33f3e8_in_33f180": "Bayer",
    "virtual_0x33f94f_in_33f480": "BayerFloat",
    "virtual_0x33ffd4_in_33fb30": "Color",
}

BAYER = {
    0x65AE40, 0x65AEC8, 0x65B3C8, 0x65B5C8, 0x65B9C8, 0x65BDB8,
    0x65BF18, 0x65C818, 0x65CA18, 0x65D978, 0x65DE38,
}
BAYER_FLOAT_WIDE = {
    0x65AF48, 0x65AFC8, 0x65B648, 0x65BA48, 0x65CA98, 0x65D9F8,
}
BAYER_FLOAT_TELE = BAYER_FLOAT_WIDE | {0x65BE38, 0x65C898, 0x65DEB8}
COLOR_WIDE = {0x65B148, 0x65B1C8, 0x65BEA8, 0x65C998, 0x65DA68, 0x65DF28}

EXPECTED = {
    "28mm": {"Bayer": BAYER, "BayerFloat": BAYER_FLOAT_WIDE, "Color": COLOR_WIDE},
    "35mm": {"Bayer": BAYER, "BayerFloat": BAYER_FLOAT_WIDE, "Color": COLOR_WIDE},
    "70mm": {"Bayer": BAYER, "BayerFloat": BAYER_FLOAT_TELE, "Color": set()},
    "150mm": {"Bayer": BAYER, "BayerFloat": BAYER_FLOAT_TELE, "Color": set()},
}

HASHES = {
    (0x34D574, 0x34D601): "178792fc1f851d4d0b991394806b6e7a112b717cb9f1819a5bf16ae2f7707e7c",
    (0x33F180, 0x33F456): "8f5f4e655e90f79765f2b44a4573012c69628cd489e0ac8c98bd6510ab57978e",
    (0x33F480, 0x33FB1E): "84f711a5bf23a220013e3ba4127822791db3768b588e73634321dd50814d8f81",
    (0x33FB30, 0x3400B1): "02cc17981dafecf6c35cf876d261a4bd1c6c55a724a0e214e018fb6c5a86d116",
    (0x3299A0, 0x32A944): "80208f5f8c6892a1dd8d77491a53d8b75f0f85dd2638fc0dd046cd65eb1d1082",
    (0x32B7C0, 0x32B91B): "755844e4ceb7b8e0fa3cd27d3587edb80f24f0968d4a663b640271be73011b49",
    (0x32C0DC, 0x32C18B): "ad922836201bcbfbdf787f603746822155fb0aa1ac91e4b332bab81f652998d8",
    (0x32C609, 0x32C775): "8520893f057c98eafe6eeb808bbe11432aa395f7db9b9057b8d661e319e83c97",
    (0x32E023, 0x32E217): "0b7d73deda4db8bf1b979f128198051046c99ca5918a40f578671506c1eb3acb",
    (0x33077B, 0x331056): "8644ea5c8089af2d37b3ea5bf5ac7d948775546a06cdfc47a4efbc0d83eef132",
    (0x331448, 0x33152F): "db75ff2cf2075bbb7c29d7542e996148e6e3b08771267cac2c62fe3875369e5d",
    (0x3324F0, 0x3337D8): "88e38e0952e9d9725c5a78de91e47f027b360e3839eff0004337139d8b7b750e",
    (0x3348D0, 0x334C10): "903ee5b0dbf834110e9bb0bb5309e50961d79d7c97441fbcd1c7c0aeed7777e2",
    (0x339E00, 0x33AAE1): "1ddfb9f3dd7ea715dd6a277a827dda53f98ba47dfbf526a7b375c4aab874ccb9",
    (0x33D700, 0x33DDEC): "d3e34b3d2c335234dfb1a56926d94651dac842f2a7c3e7e1614330faf071e9c2",
}


def verify_static() -> str:
    data = static.LIBCP.read_bytes()
    mapping = static.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == static.LIBCP_SHA256, f"libcp digest changed: {digest}")

    for (start, end), expected in HASHES.items():
        actual = hashlib.sha256(static.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed")

    for va, expected_hex in SETUP_PREFIXES.items():
        actual = static.bytes_at(data, mapping, va, 8).hex()
        require(actual == expected_hex, f"setup bytes changed at 0x{va:x}: {actual}")

    for vtable, (target, name_fragment) in VTABLES.items():
        actual_target = static.u64(static.bytes_at(data, mapping, vtable + 0x30, 8))
        require(actual_target == target, f"vtable 0x{vtable:x} target changed")
        name_slot = vtable + (0x58 if vtable == 0x65AE40 else 0x50)
        name_va = static.u64(static.bytes_at(data, mapping, name_slot, 8))
        name = static.cstring(data, mapping, name_va).decode("ascii")
        require(name_fragment in name, f"vtable 0x{vtable:x} RTTI changed: {name}")

    # Default callbacks are exact helpers; only Color's default-0 is the
    # separately admitted AWB/color-scale body.
    jump_prefixes = {
        0x340A30: "554889e54889f75de9b3050100",  # -> 0x350ff0
        0x340BF0: "554889e54889f75de9f3020100",  # -> 0x350ef0
        0x340F70: "554889e54889f75de973010100",  # -> 0x3510f0
    }
    for va, expected_hex in jump_prefixes.items():
        actual = static.bytes_at(data, mapping, va, len(expected_hex) // 2).hex()
        require(actual == expected_hex, f"default thunk changed at 0x{va:x}")

    # Constructor writes the 16 record pointers in this exact order before
    # copying them into its 0x80-byte vector allocation.
    expected_constructor_hex = (
        "48899d50ffffff4c898558ffffff4c89ad60ffffff4c89bd68ffffff"
        "4c89b570ffffff4c899578ffffff4c895d804c894d884c89659048894d98"
        "488975a048897da8488955b04c8da3400300004c8965b8488d8380030000488945c0"
        "488d83c0030000488945c8"
    )
    actual = static.bytes_at(data, mapping, 0x34D50D, len(expected_constructor_hex) // 2).hex()
    require(actual == expected_constructor_hex, "16-slot constructor permutation bytes changed")
    require(PERMUTATION[3] == 0x80 and PERMUTATION[7] == 0xC0
            and PERMUTATION[11] == 0x2C0 and PERMUTATION[15] == 0x3C0,
            "internal stage permutation invariant changed")

    tone_adjust_layout = {
        # payload: (record-location instruction, bytes, vtable-load instruction,
        #           bytes, payload record base)
        "Bayer": (0x337200, "4d8dbdc007000049", 0x337326,
                  "488d059b62320048", 0x480),
        "BayerFloat": (0x337ECA, "498d9da003000049", 0x337F14,
                       "488d052d57320048", 0x60),
        "Color": (0x3380FC, "498d9d0010000049", 0x338146,
                  "488d056b55320048", 0xCC0),
    }
    for payload, (record_va, record_hex, vtable_va, vtable_hex, base) in tone_adjust_layout.items():
        require(static.bytes_at(data, mapping, record_va, 8).hex() == record_hex,
                f"{payload} ToneAdjust record location changed")
        require(static.bytes_at(data, mapping, vtable_va, 8).hex() == vtable_hex,
                f"{payload} ToneAdjust vtable install changed")
        record_offset = {"Bayer": 0x7C0, "BayerFloat": 0x3A0, "Color": 0x1000}[payload]
        require(record_offset - base == PERMUTATION[13] == 0x340,
                f"{payload} ToneAdjust is no longer stage index 13")

    for call_va, target in (
        (0x3492C6, 0x2E6D50),
        (0x349546, 0x2E6D50),
        (0x3497C6, 0x2E6D50),
        (0x2E6F24, 0x2E40F0),
        (0x2E462C, 0x2E4CF0),
    ):
        require(static.direct_call_target(static.instruction(data, mapping, call_va)) == target,
                f"clarity call edge changed at 0x{call_va:x}")
    return digest


def parse_targets(report: dict) -> dict[str, set[int]]:
    observed = {payload: set() for payload in SITES.values()}
    for key, count in report["target_counts"].items():
        site, vtable_s, target_s = key.split("|")
        require(site in SITES, f"unknown runtime site {site}")
        require(count > 0, f"non-positive target count for {key}")
        vtable = int(vtable_s)
        target = int(target_s)
        require(vtable in VTABLES, f"unknown runtime vtable 0x{vtable:x}")
        require(VTABLES[vtable][0] == target, f"runtime target mismatch for 0x{vtable:x}")
        observed[SITES[site]].add(vtable)
    return observed


def verify_runtime() -> dict[str, dict[str, list[str]]]:
    result = {}
    for focal, expected in EXPECTED.items():
        path = RUN / f"src1_virtual_census_{focal}.json"
        report = json.loads(path.read_text())
        require(report["process"] == {"valid": True, "state": "exited", "exit_status": 0},
                f"{focal}: process did not exit cleanly")
        require(report["errors"] == [], f"{focal}: probe errors: {report['errors']}")
        require(report["gate_hits"] == 1, f"{focal}: expected one visible-src1 gate")
        observed = parse_targets(report)
        for payload in ("Bayer", "BayerFloat", "Color"):
            require(observed[payload] == expected[payload],
                    f"{focal} {payload}: targets changed; got {sorted(observed[payload])}")
        expected_counts = {
            "virtual_0x33f3e8_in_33f180": 512,
            "virtual_0x33f94f_in_33f480": 512,
            "virtual_0x33ffd4_in_33fb30": 512 if focal in ("28mm", "35mm") else 0,
        }
        require(report["virtual_counts"] == expected_counts,
                f"{focal}: virtual-site counts changed")
        result[focal] = {
            payload: [f"0x{vtable:x}->0x{VTABLES[vtable][0]:x}" for vtable in sorted(values)]
            for payload, values in observed.items()
        }
    return result


def verify_clarity_runtime() -> dict:
    report = json.loads(CLARITY_RUN.read_text())
    require(report["process"]["valid"] is True, "clarity process invalid")
    require(report["process"]["exit_status"] == 0, "clarity process did not exit cleanly")
    require(report["errors"] == [], f"clarity probe errors: {report['errors']}")
    require(report["counts"] == {"entry": 67, "callback": 590, "property": 273},
            "retained clarity liveness counts changed")
    require(report["entries"], "clarity report has no entry packets")
    first = report["entries"][0]
    require(first["config_f32_0x00_0x20"][:7] == [0.0, 1.0, 1.0, 0.5, -8.0,
                                                        0.20000000298023224, -1.0],
            "clarity config packet changed")
    require(sorted({sample["level"] for sample in report["callbacks"]}) == [0, 1, 2, 3, 4],
            "clarity callback levels changed")
    return {"scope": "Unit-1 28mm", "entries": 67, "callback_levels": [0, 1, 2, 3, 4]}


def main() -> None:
    digest = verify_static()
    runtime = verify_runtime()
    clarity = verify_clarity_runtime()
    print(json.dumps({
        "clarity_runtime": clarity,
        "libcp_sha256": digest,
        "stage_permutation": [f"0x{x:03x}" for x in PERMUTATION],
        "runtime_targets": runtime,
        "result": "PASS",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
