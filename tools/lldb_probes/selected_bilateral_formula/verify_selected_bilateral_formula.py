#!/usr/bin/env python3
"""Verify selected bilateral worker constants and runtime formula replay."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/selected_bilateral_formula"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)

REPORTS = {
    "unit1_35mm": RUN_ROOT / "unit1_35mm.json",
    "unit2_35mm": RUN_ROOT / "unit2_35mm.json",
}

EPSILON = struct.unpack("<f", bytes.fromhex("bd378635"))[0]
STORE_TOLERANCE = 1.0e-7
OBSERVED_DIVIDE_TOLERANCE = 8.0e-4
REPLAY_SUM_TOLERANCE = 8.0e-2
REPLAY_OUTPUT_TOLERANCE = 8.0e-2


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("selected_bilateral_static_helpers", STATIC_PATH)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def vec_sub(a, b):
    return [f32(x - y) for x, y in zip(a, b)]


def vec_mul(a, b):
    return [f32(x * y) for x, y in zip(a, b)]


def vec_add(a, b):
    return [f32(x + y) for x, y in zip(a, b)]


def vec_div(a, b):
    out = []
    for x, y in zip(a, b):
        out.append(f32(x / y) if y not in (0.0, -0.0) else math.nan)
    return out


def max_abs_delta(a, b) -> float:
    vals = []
    for x, y in zip(a or [], b or []):
        if x is None or y is None or not math.isfinite(x) or not math.isfinite(y):
            continue
        vals.append(abs(float(x) - float(y)))
    return max(vals) if vals else math.inf


def range_hash(data: bytes, mapping, start: int, end: int) -> str:
    return hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()


def verify_static() -> str:
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == STATIC.LIBCP_SHA256, f"libcp digest changed: {digest}")

    constants = {
        0x5A81F0: struct.pack("<4I", *([0x7FFFFFFF] * 4)),
        0x5A88D0: struct.pack("<4f", 0.0, 0.0, 0.0, 1.0),
        0x5A8920: struct.pack("<4f", 1.0, 1.0, 1.0, 1.0),
        0x5E7380: struct.pack("<4f", EPSILON, EPSILON, EPSILON, EPSILON),
    }
    for va, expected in constants.items():
        require(STATIC.bytes_at(data, mapping, va, 16) == expected, f"constant 0x{va:x} changed")

    hashes = {
        (0x2FB320, 0x2FC11F): "c6a6926cffdfa8f79b8f6c0caa4a65066ab0b7f42f7ce4e15dc95a1ed65b7861",
        (0x2FD070, 0x2FDCE0): "c4660f0f361c2a4e9886d125197181dab9f50b7757c5ce3032197c65f547860a",
        (0x2F6420, 0x2F68A0): "5f28dc1fdbd035a13e71867718f6865cc1b3c43ebfa70869526f090ae2b7cbb0",
    }
    for (start, end), expected in hashes.items():
        require(range_hash(data, mapping, start, end) == expected, f"range 0x{start:x}..0x{end:x} changed")

    print(
        "static_selected_bilateral=OK "
        f"libcp={digest} constants=abs_mask,alpha_lane,one,epsilon"
    )
    return digest


def sample_vec(sample: dict, key: str):
    packet = sample[key]
    require(packet["read_ok"], f"{sample['site']} {key} unreadable")
    return [f32(v) for v in packet["f32"]]


def coefficient_vec(sample: dict):
    packet = sample["callback"]["field_decodes"]["+0x20_coefficient_vec4"]
    require(packet["read_ok"], f"{sample['site']} coefficient vector unreadable")
    return [f32(v) for v in packet["f32"]]


def callback_descriptor(sample: dict, key: str):
    packet = sample["callback"]["field_decodes"][key]
    require(packet["read_ok"], f"{sample['site']} callback descriptor {key} unreadable")
    return packet


def require_descriptor_custody(sample: dict) -> None:
    radius = sample["radius"]
    source = callback_descriptor(sample, "+0x10_source_descriptor")
    scale = callback_descriptor(sample, "+0x08_range_scale_descriptor")
    dest = callback_descriptor(sample, "+0x18_destination_descriptor")
    local_source = sample["local_source_descriptor_rbp_minus_0x60"]
    local_scale = sample["local_range_scale_descriptor_rbp_minus_0x90"]

    for packet, label in ((local_source, "local source"), (local_scale, "local range scale")):
        require(packet["read_ok"], f"{sample['site']} {label} descriptor unreadable")

    common = ("rect_i32_0x00", "width_0x10", "height_0x14", "stride_0x18")
    for key in common:
        require(source[key] == scale[key], f"{sample['site']} source/scale {key} mismatch")
        require(source[key] == dest[key], f"{sample['site']} source/destination {key} mismatch")

    x0, y0, x1, y1 = source["rect_i32_0x00"]
    expected_padded_rect = [x0 - radius, y0 - radius, x1 + radius, y1 + radius]
    expected_padded_stride = source["stride_0x18"] + 2 * radius
    for packet, label in ((local_source, "source"), (local_scale, "range scale")):
        require(
            packet["rect_i32_0x00"] == expected_padded_rect,
            f"{sample['site']} padded {label} rectangle mismatch",
        )
        require(packet["width_0x10"] == source["width_0x10"], f"{sample['site']} {label} width mismatch")
        require(packet["height_0x14"] == source["height_0x14"], f"{sample['site']} {label} height mismatch")
        require(
            packet["stride_0x18"] == expected_padded_stride,
            f"{sample['site']} padded {label} stride mismatch",
        )

    require(
        sample_vec(sample, "source_center") == sample_vec(sample, "callback_source_at_xy"),
        f"{sample['site']} callback +0x10 source did not feed local source center",
    )
    require(
        sample_vec(sample, "range_scale_vec4") == sample_vec(sample, "callback_range_scale_at_xy"),
        f"{sample['site']} callback +0x08 range scale did not feed local range-scale center",
    )
    require(
        sample_vec(sample, "dest_after_vec4") == sample_vec(sample, "callback_destination_after_at_xy"),
        f"{sample['site']} callback +0x18 destination did not receive the store",
    )

    expected_dest = dest["data_ptr_0x20"] + (
        sample["y"] * dest["stride_0x18"] + sample["x"]
    ) * 16
    require(sample["dest_addr"] == expected_dest, f"{sample['site']} destination address mismatch")


def neighborhood_vectors(sample: dict):
    packet = sample["source_neighborhood"]
    require(packet["read_ok"], f"{sample['site']} source neighborhood unreadable")
    source = callback_descriptor(sample, "+0x10_source_descriptor")
    x0, y0, x1, y1 = source["rect_i32_0x00"]
    rows = []
    for row in packet["rows"]:
        out_row = []
        for item in row:
            vec = item["vec4"]
            require(vec["read_ok"], f"{sample['site']} neighbor {item['dx']},{item['dy']} unreadable")
            value = [f32(v) for v in vec["f32"]]
            qx = sample["x"] + item["dx"]
            qy = sample["y"] + item["dy"]
            if qx < x0 or qx >= x1 or qy < y0 or qy >= y1:
                require(value == [0.0, 0.0, 0.0, 0.0], f"{sample['site']} nonzero padded neighbor")
            out_row.append(value)
        rows.append(out_row)
    return rows


def replay_sample(sample: dict) -> dict:
    center = sample_vec(sample, "source_center")
    scale_source = sample_vec(sample, "range_scale_vec4")
    coeff = coefficient_vec(sample)
    scale = vec_mul(coeff, scale_source)
    reciprocal_source = [scale[0], scale[1], scale[2], 1.0]
    reciprocal = [f32(1.0 / value) if value not in (0.0, -0.0) else math.inf for value in reciprocal_source]
    sum_weight = [0.0, 0.0, 0.0, 0.0]
    sum_weighted = [0.0, 0.0, 0.0, 0.0]

    for row in neighborhood_vectors(sample):
        for value in row:
            delta = vec_sub(value, center)
            max_abs_rgb = f32(max(abs(delta[0]), abs(delta[1]), abs(delta[2])))
            over = [f32(max(f32(max_abs_rgb - lane), 0.0)) for lane in scale]
            over = vec_mul(over, reciprocal)
            weight = [f32(max(f32(1.0 - lane), EPSILON)) for lane in over]
            sum_weight = vec_add(sum_weight, weight)
            sum_weighted = vec_add(sum_weighted, vec_mul(value, weight))

    output = vec_div(sum_weighted, sum_weight)
    return {
        "scale": scale,
        "reciprocal_source": reciprocal_source,
        "sum_weight": sum_weight,
        "sum_weighted": sum_weighted,
        "output": output,
    }


def verify_sample(sample: dict) -> dict:
    require(sample["callback"]["read_ok"], f"{sample['site']} callback unreadable")
    worker = sample["callback"].get("worker_slot_0x30_va")
    require(worker == sample["worker_va"], f"{sample['site']} worker slot mismatch")
    require_descriptor_custody(sample)

    dest = sample_vec(sample, "dest_after_vec4")
    observed_store = sample["observed_store_xmm0"]
    observed_sum = sample["observed_sum_weight"]
    observed_weighted = sample["observed_sum_weighted"]
    require(max_abs_delta(dest, observed_store) <= STORE_TOLERANCE, f"{sample['site']} destination != xmm0")

    observed_divide = vec_div([f32(v) for v in observed_weighted], [f32(v) for v in observed_sum])
    observed_divide_delta = max_abs_delta(observed_store, observed_divide)
    require(
        observed_divide_delta <= OBSERVED_DIVIDE_TOLERANCE,
        f"{sample['site']} observed divide delta {observed_divide_delta}",
    )

    replay = replay_sample(sample)
    sum_delta = max_abs_delta(replay["sum_weight"], observed_sum)
    weighted_delta = max_abs_delta(replay["sum_weighted"], observed_weighted)
    output_delta = max_abs_delta(replay["output"], dest)
    require(sum_delta <= REPLAY_SUM_TOLERANCE, f"{sample['site']} sum-weight replay delta {sum_delta}")
    require(
        weighted_delta <= REPLAY_SUM_TOLERANCE,
        f"{sample['site']} weighted-sum replay delta {weighted_delta}",
    )
    require(output_delta <= REPLAY_OUTPUT_TOLERANCE, f"{sample['site']} output replay delta {output_delta}")
    return {
        "site": sample["site"],
        "radius": sample["radius"],
        "sum_delta": sum_delta,
        "weighted_delta": weighted_delta,
        "output_delta": output_delta,
        "observed_divide_delta": observed_divide_delta,
    }


def load_report(label: str, path: Path) -> dict:
    require(path.exists(), f"missing report {path}")
    report = json.loads(path.read_text())
    process = report["process"]
    require(process["valid"], f"{label}: invalid process packet")
    require(process["exit_status"] == 0, f"{label}: process exit {process['exit_status']}")
    require(not report["errors"], f"{label}: errors {report['errors']}")
    require(not report.get("drive_hit_step_cap"), f"{label}: hit drive step cap")
    return report


def verify_report(label: str, report: dict) -> list[dict]:
    samples = report["samples"]
    require(samples, f"{label}: no samples")
    results = [verify_sample(sample) for sample in samples]
    counts = report["counts"]
    if label == "unit1_35mm":
        require(counts["after_store_0x2fb320_radius2"] > 0, "Unit-1 did not hit radius-2 worker")
        require(counts["after_store_0x2fd070_radius4"] == 0, "Unit-1 unexpectedly hit radius-4 worker")
    if label == "unit2_35mm":
        require(counts["after_store_0x2fd070_radius4"] > 0, "Unit-2 did not hit radius-4 worker")
    return results


def main() -> None:
    digest = verify_static()
    all_results = []
    for label, path in REPORTS.items():
        report = load_report(label, path)
        results = verify_report(label, report)
        all_results.extend(results)
        by_site = {}
        for result in results:
            site = result["site"]
            by_site.setdefault(site, 0)
            by_site[site] += 1
        print(f"{label}: OK samples={by_site}")

    max_sum = max(result["sum_delta"] for result in all_results)
    max_weighted = max(result["weighted_delta"] for result in all_results)
    max_output = max(result["output_delta"] for result in all_results)
    max_divide = max(result["observed_divide_delta"] for result in all_results)
    print(
        "selected_bilateral_formula=OK "
        f"libcp={digest} samples={len(all_results)} "
        f"max_sum_delta={max_sum:.9g} "
        f"max_weighted_delta={max_weighted:.9g} "
        f"max_output_delta={max_output:.9g} "
        f"max_observed_divide_delta={max_divide:.9g}"
    )


if __name__ == "__main__":
    main()
