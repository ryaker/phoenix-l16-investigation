#!/usr/bin/env python3
"""Verify Guidance's live SoftISP config and collapse2 RGBA semantics."""

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
RUN_DIR = ROOT / "runs/index5_guidance_channel_origin"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("guidance_collapse2_static", STATIC_PATH)


def instruction_tuple(data: bytes, mapping, address: int) -> tuple[str, str]:
    item = STATIC.instruction(data, mapping, address)
    return item.mnemonic, item.op_str


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    require(
        STATIC.cstring(data, mapping, 0x631C14) == b"output.color_space",
        "output color-space path drift",
    )
    require(
        STATIC.cstring(data, mapping, 0x631C27) == b"demosaicking.type",
        "demosaicking path drift",
    )
    require(
        STATIC.cstring(data, mapping, 0x632CA1) == b"collapse2",
        "collapse2 comparison string drift",
    )

    variants = {
        (0, 0): {
            "name": 0x5AA620,
            "typeinfo": 0x652600,
            "table": 0x6525A8,
            "worker": 0xA4AC0,
            "body_end": 0xA5000,
            "loads": (0xA4CED, 0xA4CF4, 0xA4CFB, 0xA4D02),
            "sources": (
                "ebx, dword ptr [rax + rcx*4 - 4]",
                "ebx, dword ptr [rax + rcx*4]",
                "ebx, dword ptr [rdi + rcx*4]",
                "ebx, dword ptr [rdi + rcx*4 + 4]",
            ),
            "combine": 0xA4ED3,
            "hash": "2183cdbdb27655632c9badd1079de0c1fa2026129b1a2a138d232a9eeafe0bef",
        },
        (1, 0): {
            "name": 0x5AA780,
            "typeinfo": 0x652680,
            "table": 0x652628,
            "worker": 0xA50D0,
            "body_end": 0xA5610,
            "loads": (0xA52FD, 0xA5303, 0xA530B, 0xA5313),
            "sources": (
                "ebx, dword ptr [rax + rcx*4]",
                "ebx, dword ptr [rax + rcx*4 - 4]",
                "ebx, dword ptr [rdi + rcx*4 + 4]",
                "ebx, dword ptr [rdi + rcx*4]",
            ),
            "combine": 0xA54E3,
            "hash": "005cd3eb5470611af08bae593c4d81b07002746c6c8ca7ba9348e8817df58c20",
        },
        (0, 1): {
            "name": 0x5AA8E0,
            "typeinfo": 0x652700,
            "table": 0x6526A8,
            "worker": 0xA56E0,
            "body_end": 0xA5C20,
            "loads": (0xA590D, 0xA5913, 0xA591B, 0xA5923),
            "sources": (
                "ebx, dword ptr [rdi + rcx*4]",
                "ebx, dword ptr [rax + rcx*4 - 4]",
                "ebx, dword ptr [rdi + rcx*4 + 4]",
                "ebx, dword ptr [rax + rcx*4]",
            ),
            "combine": 0xA5AF3,
            "hash": "e0db597ea57a18012909b09f930fa72d9c2bdd4f99e7fa1690f66d9106c5427e",
        },
        (1, 1): {
            "name": 0x5AAA40,
            "typeinfo": 0x652780,
            "table": 0x652728,
            "worker": 0xA5CF0,
            "body_end": 0xA6230,
            "loads": (0xA5F1D, 0xA5F24, 0xA5F2B, 0xA5F32),
            "sources": (
                "ebx, dword ptr [rdi + rcx*4 + 4]",
                "ebx, dword ptr [rax + rcx*4]",
                "ebx, dword ptr [rdi + rcx*4]",
                "ebx, dword ptr [rax + rcx*4 - 4]",
            ),
            "combine": 0xA6103,
            "hash": "ac11d3e219fc5fb6e39464c260df6d07a0b79ab86bb01597590eabaf56c4dc4b",
        },
    }
    for phase, item in variants.items():
        name = STATIC.cstring(data, mapping, item["name"]).decode("ascii")
        require(
            f"DemosaickFilterE3EfLi{phase[0]}ELi{phase[1]}EE" in name,
            f"phase {phase}: RTTI name drift",
        )
        require(
            struct.unpack_from("<Q", data, item["typeinfo"] + 8)[0]
            == item["name"],
            f"phase {phase}: typeinfo name pointer drift",
        )
        require(
            struct.unpack_from("<Q", data, item["table"] + 8)[0]
            == item["typeinfo"],
            f"phase {phase}: table typeinfo drift",
        )
        require(
            struct.unpack_from("<Q", data, item["table"] + 0x40)[0]
            == item["worker"],
            f"phase {phase}: worker slot drift",
        )
        actual_hash = hashlib.sha256(
            STATIC.bytes_at(
                data,
                mapping,
                item["worker"],
                item["body_end"] - item["worker"],
            )
        ).hexdigest()
        require(actual_hash == item["hash"], f"phase {phase}: body drift")

        for address, source in zip(item["loads"], item["sources"]):
            require(
                instruction_tuple(data, mapping, address) == ("mov", source),
                f"phase {phase}: Bayer lane load drift at 0x{address:x}",
            )

        combine = item["combine"]
        for address, expected_target in (
            (combine, 0x5A9AE0),
            (combine + 7, 0x5A9AF0),
            (combine + 14, 0x5A88D0),
        ):
            require(
                STATIC.rip_target(STATIC.instruction(data, mapping, address))
                == expected_target,
                f"phase {phase}: combine constant drift at 0x{address:x}",
            )
        expected_tail = {
            combine + 0x33: ("mulps", "xmm4, xmm0"),
            combine + 0x36: ("psrldq", "xmm3, 4"),
            combine + 0x3B: ("mulps", "xmm3, xmm1"),
            combine + 0x3E: ("addps", "xmm3, xmm4"),
            combine + 0x41: ("blendps", "xmm3, xmm2, 8"),
        }
        for address, expected in expected_tail.items():
            require(
                instruction_tuple(data, mapping, address) == expected,
                f"phase {phase}: final RGBA combine drift at 0x{address:x}",
            )

    require(
        struct.unpack_from("<4f", data, 0x5A9AE0) == (1.0, 0.5, 0.0, 0.0),
        "first collapse2 weight drift",
    )
    require(
        struct.unpack_from("<4f", data, 0x5A9AF0) == (0.0, 0.5, 1.0, 0.0),
        "second collapse2 weight drift",
    )
    require(
        struct.unpack_from("<4f", data, 0x5A88D0) == (0.0, 0.0, 0.0, 1.0),
        "collapse2 alpha constant drift",
    )
    return digest


def verify_property_reports() -> None:
    expected_1 = {
        "demosaicking.type": "none",
        "hot_pixel_removal.type": "none",
        "color_correction.type": "none",
        "bayer_phase_fix.type": "none",
        "highlight_restore.type": "none",
        "lens_shading.type": "default",
        "denoising.type": "none",
        "tone_adjust.type": "none",
        "contrast_adjust.type": "none",
        "tone_mapping.type": "none",
        "output.color_space": "none",
        "output.white_point": "native",
    }
    expected_2 = dict(expected_1)
    expected_2["demosaicking.type"] = "collapse2"
    expected_2["hot_pixel_removal.type"] = "default"

    names = (
        "softisp_properties_unit1_28mm.json",
        "softisp_properties_unit1_35mm.json",
        "softisp_properties_unit1_70mm.json",
        "softisp_properties_unit1_150mm.json",
        "softisp_properties_unit2_28mm.json",
    )
    for name in names:
        report = json.loads((RUN_DIR / name).read_text())
        require(report["capture_complete"], f"{name}: capture incomplete")
        require(report["terminated_after_capture"], f"{name}: no bounded stop")
        require(report["process"]["exit_status"] == 9, f"{name}: exit status")
        require(not report["errors"], f"{name}: {report['errors']}")
        require(len(report["create_entries"]) == 1, f"{name}: producer entry count")
        observed = {"softisp_1": {}, "softisp_2": {}}
        for item in report["queried_properties"]:
            require("error" not in item, f"{name}: query error {item}")
            observed[item["softisp_role"]][item["name"]] = item["value"]
        require(observed["softisp_1"] == expected_1, f"{name}: softisp_1 drift")
        require(observed["softisp_2"] == expected_2, f"{name}: softisp_2 drift")
        require(
            [item["name"] for item in report["lookups"]]
            == ["demosaicking.type"],
            f"{name}: natural property lookups changed",
        )
        require(
            [item["value"] for item in report["string_extracts"]]
            == ["collapse2"],
            f"{name}: natural demosaic selection changed",
        )


def verify_worker_reports() -> None:
    expected = {
        "collapse2_worker_unit1_28mm.json": (0xA50D0, 3, [1, 0]),
        "collapse2_worker_unit1_70mm.json": (0xA5CF0, 3, [1, 1]),
    }
    for name, values in expected.items():
        report = json.loads((RUN_DIR / name).read_text())
        require(report["capture_complete"], f"{name}: capture incomplete")
        require(report["terminated_after_capture"], f"{name}: no bounded stop")
        require(not report["errors"], f"{name}: {report['errors']}")
        require(len(report["create_entries"]) == 1, f"{name}: no producer gate")
        require(len(report["hits"]) == 1, f"{name}: worker hit count")
        hit = report["hits"][0]
        require(
            (hit["site"], hit["filter_enum"], hit["phase_bits"]) == values,
            f"{name}: selected worker drift",
        )


def main() -> None:
    digest = verify_static()
    verify_property_reports()
    verify_worker_reports()
    print(f"guidance_collapse2_static=OK libcp={digest} variants=4")
    print("live_softisp=Unit1(28,35,70,150)+Unit2(28) collapse2 none/native")
    print("gated_workers=28mm:E3/GRBG 70mm:E3/BGGR")
    print("guidance_components=C0:R C1:(G1+G2)/2 C2:B C3:1")
    print("guidance_collapse2_semantics=OK")


if __name__ == "__main__":
    main()
