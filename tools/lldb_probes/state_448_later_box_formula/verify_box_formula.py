#!/usr/bin/env python3
"""Validate state+0x448 later box/origin/scale formula reports."""

from __future__ import annotations

import json
import math
import struct
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/state_448_later_box_formula"
TIERS = ("28mm", "35mm", "70mm", "150mm")
EXPECTED_KEYS = {
    "28mm": [0, 1, 2, 3, 4],
    "35mm": [0, 1, 2, 3, 4],
    "70mm": [5, 6, 7, 8, 9],
    "150mm": [5, 6, 7, 8, 9],
}
SITE_ORDER = (
    "post_145980_box",
    "pre_260e40_formula",
    "post_260e40_formula",
    "copy_scale_to_payload_2415d0",
    "copy_origin_to_payload_2415f0",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", f32(value)))[0]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def require_hdr_output(tier: str) -> None:
    hdr = RUN_ROOT / f"box_formula_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def key_for_event(event: dict) -> int:
    packet = event["packet"]
    if "key" in packet and packet["key"] is not None:
        return int(packet["key"])
    return int(packet["node_key_from_payload_minus_0x04"])


def formula_words(box: list[int], size: list[int]) -> tuple[list[int], list[int], list[float], list[float]]:
    x0, y0, x1, y1 = box
    width, height = size
    span_x = x1 - x0
    span_y = y1 - y0
    require(span_x > 0 and span_y > 0, f"bad box span {box}")
    sx = f32(f32(float(width)) / f32(float(span_x)))
    sy = f32(f32(float(height)) / f32(float(span_y)))
    uniform = f32(max(sx, sy))
    origin = [f32(float(x0)), f32(float(y0))]
    scale = [uniform, uniform]
    return (
        [f32_word(origin[0]), f32_word(origin[1])],
        [f32_word(scale[0]), f32_word(scale[1])],
        origin,
        scale,
    )


def validate_tier(tier: str) -> str:
    packet = load_json(RUN_ROOT / f"box_formula_{tier}.json")
    process = packet["process"]
    require(process["state"] == "exited", f"{tier}: process did not exit")
    require(process["exit_status"] == 0, f"{tier}: nonzero exit")
    require(not packet.get("errors"), f"{tier}: JSON errors {packet.get('errors')}")
    require(not packet.get("drive_hit_step_cap"), f"{tier}: hit step cap")
    require(packet["events"], f"{tier}: no events")
    require_hdr_output(tier)

    grouped: dict[int, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for event in packet["events"]:
        site = event["site_name"]
        require(site in SITE_ORDER, f"{tier}: unexpected site {site}")
        grouped[key_for_event(event)][site].append(event)

    require(sorted(grouped) == EXPECTED_KEYS[tier], f"{tier}: key set {sorted(grouped)}")

    rows = []
    for key in EXPECTED_KEYS[tier]:
        by_site = grouped[key]
        for site in SITE_ORDER:
            require(len(by_site[site]) == 1, f"{tier} key {key}: {site} count {len(by_site[site])}")
        post_box = by_site["post_145980_box"][0]["packet"]
        pre = by_site["pre_260e40_formula"][0]["packet"]
        post = by_site["post_260e40_formula"][0]["packet"]
        scale_copy = by_site["copy_scale_to_payload_2415d0"][0]["packet"]
        origin_copy = by_site["copy_origin_to_payload_2415f0"][0]["packet"]

        box = post_box["box_i32_xyxy"]
        size = pre["size_i32_wh"]
        require(box == pre["box_i32_xyxy"] == post["box_i32_xyxy"], f"{tier} key {key}: box mismatch")
        if post["size_i32_wh"] is not None:
            require(size == post["size_i32_wh"], f"{tier} key {key}: size mismatch")
        require(size == [4160, 3120], f"{tier} key {key}: unexpected size {size}")
        obj = post_box["object_block_0x10c"]
        require(obj["read_ok"], f"{tier} key {key}: object block unreadable")
        require([obj["i32_0x114"], obj["i32_0x118"]] == size, f"{tier} key {key}: object size mismatch")
        require(obj["f32_0x124"] == 1.0 and obj["f32_0x128"] == 1.0, f"{tier} key {key}: nonidentity object scale")
        require(pre["force_uniform_edx"] == 1, f"{tier} key {key}: formula is not uniform-scale mode")

        origin_words, scale_words, origin_f32, scale_f32 = formula_words(box, size)
        require(post["origin_words"] == origin_words, f"{tier} key {key}: origin words mismatch")
        require(post["scale_words"] == scale_words, f"{tier} key {key}: scale words mismatch")
        require(origin_copy["source_words"] == origin_words, f"{tier} key {key}: origin copy mismatch")
        require(scale_copy["source_words"] == scale_words, f"{tier} key {key}: scale copy mismatch")
        require(origin_copy["node_key_from_payload_minus_0x04"] == key, f"{tier} key {key}: origin payload key")
        require(scale_copy["node_key_from_payload_minus_0x04"] == key, f"{tier} key {key}: scale payload key")

        # Check reported floats too; raw-word checks above are the admission gate.
        for observed, expected in zip(post["origin_f32"], origin_f32):
            require(math.isclose(observed, expected, rel_tol=0, abs_tol=0), f"{tier} key {key}: origin f32")
        for observed, expected in zip(post["scale_f32"], scale_f32):
            require(math.isclose(observed, expected, rel_tol=0, abs_tol=0), f"{tier} key {key}: scale f32")

        rows.append(
            f"{key}:box={box}:origin={','.join(f'{v:g}' for v in origin_f32)}:"
            f"scale={scale_f32[0]:.9f}"
        )

    return f"{tier}: OK keys={','.join(str(k) for k in EXPECTED_KEYS[tier])}; " + "; ".join(rows)


def main() -> None:
    for tier in TIERS:
        print(validate_tier(tier))


if __name__ == "__main__":
    main()
