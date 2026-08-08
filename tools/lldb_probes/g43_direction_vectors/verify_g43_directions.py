#!/usr/bin/env python3
"""Verify G-43 SGM directions, sweep order, and scratch initialization."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = (
    ROOT / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
CENSUS = {
    "35mm": ROOT / "runs/g43_g40_census/census_35mm.json",
    "70mm": ROOT / "runs/g43_g40_census/census_70mm.json",
}
POSITIVE = ROOT / "runs/g43_direction_vectors/g43_spatial_pos_35mm.json"
NEGATIVE = ROOT / "runs/g43_direction_vectors/g43_spatial_neg_35mm.json"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("g43_static", HELPER_PATH)


def verify_static():
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    window = STATIC.bytes_at(data, mapping, 0x276860, 0x277B6C - 0x276860)
    require(
        hashlib.sha256(window).hexdigest()
        == "0fabe986085ce8eccbe5c340d35b6f0047abb63242e03a6b6d263b60db306b0a",
        "mode-8 SGM worker changed",
    )
    guards = {
        0x27687B: "4189cd",              # save signed sweep direction
        0x276A29: "4585ed",              # choose forward/reverse origin
        0x2777A6: "468b1cb1",            # component = directions[path]
        0x2777AA: "4d85f6",              # path 0 special row selection
        0x2779FC: "f30f7f0451",          # current Line buf path store
        0x277A01: "660f383ae0",          # path minimum reduction
        0x277A0C: "660fdde8",            # saturating aggregate
        0x277A10: "f3410f7f2c51",        # aggregate store
        0x277A41: "49ffc6",              # next path
        0x277A5E: "4983fe04",            # exactly four paths per sweep
        0x277AA9: "448bad7cfdffff",      # restore signed sweep direction
        0x277AB0: "4401ad2cfeffff",      # advance outer coordinate by sign
    }
    for va, expected_hex in guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    pattern = bytes.fromhex("d007" * 8)
    require(STATIC.bytes_at(data, mapping, 0x5DAE00, 16) == pattern, "u16=2000 pattern")
    for xref in (0x26C97C, 0x26CA6F):
        require(
            STATIC.rip_target(STATIC.instruction(data, mapping, xref)) == 0x5DAE00,
            f"initialization pattern xref 0x{xref:x}",
        )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x26C986)) == 0x556044,
        "Line buf pattern-fill call",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x26CA79)) == 0x556044,
        "Min cost buf pattern-fill call",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x26CBB2)) == 0x555EB2,
        "Pixel buf zero-fill call",
    )
    return digest


def ordered_layers(report):
    return [report["layers"][str(item["ptr"])] for item in report["order"]]


def verify_census(tier, path):
    report = json.loads(path.read_text())
    require(report["libcp_sha256"] == STATIC.LIBCP_SHA256, f"{tier}: libcp digest")
    layers = ordered_layers(report)
    require(
        [(item["guidance_w"], item["guidance_h"]) for item in layers]
        == [(65, 49), (130, 98), (260, 195), (520, 390), (1040, 780), (2080, 1560)],
        f"{tier}: layer dimensions",
    )
    for index, layer in enumerate(layers):
        require(layer["direction_offsets_i32"] == [-1, -1, 0, 1], f"{tier}:{index}: forward array")
    for index, layer in enumerate(layers[:5]):
        require(layer["ecx_runs"] == [[1, 234], [-1, 234]], f"{tier}:{index}: sweep runs")
    return len(layers)


def groups_of_four(captures):
    require(len(captures) % 4 == 0, "spatial captures not grouped by four")
    return [captures[index:index + 4] for index in range(0, len(captures), 4)]


def verify_spatial(path, sign, expected_components):
    report = json.loads(path.read_text())
    require(report["libcp_sha256"] == STATIC.LIBCP_SHA256, f"sign {sign}: digest")
    require(report["desired_sign"] == sign and report["done"], f"sign {sign}: completion")
    require(not report["errors"], f"sign {sign}: errors")
    require(report["direction_offsets_i32"] == expected_components, f"sign {sign}: component array")
    groups = groups_of_four(report["captures"])
    require(len(groups) == 8, f"sign {sign}: expected eight sampled pixels")
    ring_stride = report["guidance_width"] + 2
    for group in groups:
        require([item["path_index"] for item in group] == [0, 1, 2, 3], f"sign {sign}: path order")
        require(
            [item["direction_component_r11"] for item in group] == expected_components,
            f"sign {sign}: live components",
        )
        predecessors = [item["predecessor_index"] for item in group]
        require(predecessors[0] - predecessors[1] == ring_stride, f"sign {sign}: row relation")
        require(
            [predecessors[2] - predecessors[1], predecessors[3] - predecessors[2]]
            == [sign, sign],
            f"sign {sign}: adjacent-row horizontal order",
        )
    return len(report["captures"])


def main():
    digest = verify_static()
    print(f"g43_static=OK libcp={digest} line_min_init_u16=2000 pixel_init=zero paths_per_sweep=4")
    for tier, path in CENSUS.items():
        print(f"{tier}: OK layers={verify_census(tier, path)} coarse_sweeps=+234,-234")
    positive = verify_spatial(POSITIVE, 1, [-1, -1, 0, 1])
    negative = verify_spatial(NEGATIVE, -1, [1, 1, 0, -1])
    print(f"spatial=OK positive_packets={positive} negative_packets={negative}")
    print("directions=(-1,0),(-1,-1),(0,-1),(1,-1) + opposites; aggregation=eight_path_saturating_u16")
    print("g43_direction_policy=OK")


if __name__ == "__main__":
    main()
