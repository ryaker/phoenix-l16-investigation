#!/usr/bin/env python3
"""Verify G40 level-0 seeding and dynamic per-level hypothesis extents."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = (
    ROOT / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
REPORTS = {
    "28mm": ROOT / "runs/g40_hypothesis_policy/hypothesis_28mm.json",
    "35mm": ROOT / "runs/g40_hypothesis_policy/hypothesis_35mm.json",
    "70mm": ROOT / "runs/g40_hypothesis_policy/hypothesis_70mm.json",
    "150mm": ROOT / "runs/g40_hypothesis_policy/hypothesis_150mm.json",
}
EXPECTED = {
    "28mm": [
        (65, 49, 752, 0, 752, 752),
        (130, 98, 752, 6, 629, 632),
        (260, 195, 752, 8, 268, 272),
        (520, 390, 752, 8, 253, 256),
        (1040, 780, 752, 7, 250, 256),
        (2080, 1560, 752, 6, 250, 256),
    ],
    "35mm": [
        (65, 49, 752, 0, 752, 752),
        (130, 98, 752, 0, 751, 752),
        (260, 195, 752, 0, 750, 752),
        (520, 390, 752, 0, 748, 752),
        (1040, 780, 752, 0, 748, 752),
        (2080, 1560, 752, 0, 746, 752),
    ],
    "70mm": [
        (65, 49, 1472, 0, 1472, 1472),
        (130, 98, 1472, 0, 1407, 1408),
        (260, 195, 1472, 0, 1392, 1392),
        (520, 390, 1472, 0, 1324, 1328),
        (1040, 780, 1472, 0, 1193, 1200),
        (2080, 1560, 1472, 0, 1149, 1152),
    ],
    "150mm": [
        (65, 49, 1472, 0, 1472, 1472),
        (130, 98, 1472, 4, 44, 48),
        (260, 195, 1472, 15, 42, 48),
        (520, 390, 1472, 15, 42, 48),
        (1040, 780, 1472, 14, 42, 48),
        (2080, 1560, 1472, 13, 42, 48),
    ],
}
STATIC_SPANS = {
    (0x26C246, 0x26C29E): "e7a3058aaa8b201b583bc04895fc46d0f7966abe85e19a8520bd26059528abad",
    (0x26D8AC, 0x26D9D6): "1f92df6c82b2a4473e3986329c7cc5ea7bdde01730f3c705ede741d5e68048f9",
    (0x26BE9E, 0x26BEC6): "0aa2b0ebe5808e55be29e776ce9f12ddb84f17d952791b36c74bb8ef3a13c482",
    (0x26C13E, 0x26C163): "ffba494c057e73aeefcd77d5398a40c0572e03b0f486d7355aba2fd966d819ef",
    (0x299FD0, 0x29A109): "0c7996bf404fc048604a1ba60ab6c1a7e5bac1a2319501a939b4c80a95f4c764",
    (0x29A1D0, 0x29A430): "b8a6ec61ffa53915d58c0ca24778393b9cfea3cad9141102b15bf53c5151ed43",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("g40_static", HELPER_PATH)


def verify_static():
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    for (start, end), expected in STATIC_SPANS.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static body changed: 0x{start:x}..0x{end:x}")

    calls = {
        0x26C241: 0x26C480,
        0x26C299: 0x29A520,
        0x26BE35: 0x26D750,
        0x26BE50: 0x29A140,
        0x26C0D7: 0x26D750,
        0x26C0F1: 0x29A140,
    }
    for address, expected in calls.items():
        actual = STATIC.direct_call_target(STATIC.instruction(data, mapping, address))
        # 0x29a525 is a tail jump, whose rel32 decoder is identical here.
        require(actual == expected, f"call/jump drift at 0x{address:x}: {actual}")
    tail = STATIC.bytes_at(data, mapping, 0x29A525, 5)
    require(tail[:1] == b"\xe9", "0x29a525: expected rel32 tail jump")
    tail_target = 0x29A52A + struct.unpack_from("<i", tail, 1)[0]
    require(tail_target == 0x29A1D0, f"0x29a525 tail target: 0x{tail_target:x}")
    return digest


def packet_tuple(packet):
    return (
        packet["width"],
        packet["height"],
        packet["lookup_count"],
        packet["min_lower"],
        packet["raw_max_upper"],
        packet["rounded_extent"],
    )


def verify_report(tier, path):
    report = json.loads(path.read_text())
    require(report["libcp_sha256"] == STATIC.LIBCP_SHA256, f"{tier}: libcp digest")
    require(report["exit_status"] == 0, f"{tier}: render exit")
    require(not report["errors"], f"{tier}: probe errors")
    packets = report["packets"]
    require(len(packets) == 6, f"{tier}: six pyramid levels")
    require(packets[0]["kind"] == "level0_full_lookup_seed", f"{tier}: level 0 kind")
    require(
        all(item["kind"] == "range_from_prior_layer" for item in packets[1:]),
        f"{tier}: higher-level producer kind",
    )
    require(all(item["mode"] == 8 for item in packets), f"{tier}: mode 8")
    require(all(item["store_matches_formula"] is True for item in packets), f"{tier}: ceil formula")
    require([packet_tuple(item) for item in packets] == EXPECTED[tier], f"{tier}: packet values")
    return [item["rounded_extent"] for item in packets]


def main():
    digest = verify_static()
    print(f"g40_static=OK libcp={digest} mode=8 levels=6")
    for tier, path in REPORTS.items():
        extents = verify_report(tier, path)
        print(f"{tier}: rounded_extents={extents}")
    print("level0=ceil(lookup_count/8)*8 lower=0")
    print("higher=ceil(max_pixel_upper/8)*8; per-pixel lower/count derive from prior depth range")
    print("g40_hypothesis_policy=OK")


if __name__ == "__main__":
    main()
