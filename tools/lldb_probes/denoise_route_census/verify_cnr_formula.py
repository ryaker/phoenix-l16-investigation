#!/usr/bin/env python3
"""Verify the captured ColorNoiseReduction worker formula samples."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "tools/lldb_probes/denoise_route_census"
STATIC_REPORT = ROOT / "runs/denoise_route_census/cnr_static_inspect.json"
RUNTIME_REPORTS = {
    "unit1_28mm": {
        "path": ROOT / "runs/denoise_route_census/unit1_28mm_cnr_formula.json",
        "low_endpoint": 42,
    },
    "unit1_35mm": {
        "path": ROOT / "runs/denoise_route_census/unit1_35mm_cnr_formula.json",
        "low_endpoint": 42,
    },
    "unit1_70mm": {
        "path": ROOT / "runs/denoise_route_census/unit1_70mm_cnr_formula.json",
        "low_endpoint": 42,
    },
    "unit1_150mm": {
        "path": ROOT / "runs/denoise_route_census/unit1_150mm_cnr_formula.json",
        "low_endpoint": 42,
    },
    "unit2_35mm": {
        "path": ROOT / "runs/denoise_route_census/unit2_35mm_cnr_formula.json",
        "low_endpoint": 43,
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def near(actual: float, expected: float, abs_tol: float = 1e-6, rel_tol: float = 1e-6) -> bool:
    return math.isclose(actual, expected, abs_tol=abs_tol, rel_tol=rel_tol)


def is_power_of_four_recip(value: float) -> bool:
    if value <= 0:
        return False
    exponent = -math.log2(value)
    return near(exponent, round(exponent), 1e-7, 1e-7) and int(round(exponent)) % 2 == 0


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tile_stats(raw: bytes) -> dict[str, object]:
    sum_sq = [0.0, 0.0, 0.0, 0.0]
    sum_cross = [0.0, 0.0, 0.0, 0.0]
    sum_alpha_products = [0.0, 0.0, 0.0, 0.0]
    alpha_sum = 0.0
    for offset in range(0, len(raw), 16):
        p = list(struct.unpack_from("<4f", raw, offset))
        products = [f32(p[index] * p[index]) for index in range(4)]
        crosses = [f32(p[0] * p[1]), f32(p[0] * p[2]), f32(p[1] * p[2]), 0.0]
        alpha_products = [f32(p[3] * p[index]) for index in range(4)]
        for index in range(4):
            sum_sq[index] = f32(sum_sq[index] + products[index])
            sum_cross[index] = f32(sum_cross[index] + crosses[index])
            sum_alpha_products[index] = f32(
                sum_alpha_products[index] + alpha_products[index]
            )
        alpha_sum = f32(alpha_sum + p[3])
    return {
        "count": len(raw) // 16,
        "sum_sq_f32": sum_sq,
        "sum_cross_f32": sum_cross,
        "sum_alpha_products_f32": sum_alpha_products,
        "alpha_sum_f32": alpha_sum,
    }


def same_f32_list(actual: list[float], expected: list[float], label: str) -> None:
    require(len(actual) == len(expected), f"{label}: length mismatch")
    for index, (a, e) in enumerate(zip(actual, expected)):
        require(f32_bits(a) == f32_bits(e), f"{label}[{index}] {a} != {e}")


def verify_static() -> dict[str, object]:
    inspector = load_module("inspect_cnr_static", PROBE_DIR / "inspect_cnr_static.py")
    report = inspector.inspect(inspector.LIBCP.read_bytes())
    STATIC_REPORT.parent.mkdir(parents=True, exist_ok=True)
    STATIC_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for name, item in report["ranges"].items():
        require(item["hash_ok"], f"static range hash drift: {name}")
    calls = {(item["at"], item["target"]) for item in report["call_targets"]}
    require(("0x3088a8", "0x309270") in calls, "worker no longer calls matrix helper")
    require(("0x30960e", "0x309d50") in calls, "matrix helper no longer calls rotation helper")
    constants = {item["target"]: item for item in report["rip_reads"]}
    require(constants["0x5f1040"]["bytes"]["f32"][0] == 5.0, "log2 level bias")
    require(constants["0x5a8128"]["bytes"]["f32"][0] == 1.0, "unity constant")
    require(
        constants["0x5a8920"]["bytes"]["f32"][:4] == [1.0, 1.0, 1.0, 1.0],
        "vec4 unity constant",
    )
    require(
        constants["0x5a88e0"]["bytes"]["u32"][:4]
        == [0x80000000, 0x80000000, 0x80000000, 0x80000000],
        "vec4 sign mask",
    )
    return report


def recompute_noise(stats: dict[str, object], params: list[float]) -> list[float]:
    area_inv = f32(1.0 / f32(stats["count"]))
    low = params[0]
    mean_alpha = f32(stats["alpha_sum_f32"] * area_inv)
    term0 = f32(mean_alpha * low)
    blend_weight = f32(f32(1.0 - low) * area_inv)
    term1 = [
        f32(f32(blend_weight * stats["sum_alpha_products_f32"][index]) * params[4 + index])
        for index in range(4)
    ]
    shaped = [f32(f32(term0 + term1[index]) * params[12 + index]) for index in range(4)]
    alpha_vec = [f32(mean_alpha * params[16 + index]) for index in range(4)]
    scale = [f32(params[1] * params[8 + index]) for index in range(4)]
    return [f32(f32(alpha_vec[index] + shaped[index]) * scale[index]) for index in range(4)]


def recompute_matrix(stats: dict[str, object], rsqrt_stack: list[float]) -> list[float]:
    area_inv = f32(1.0 / f32(stats["count"]))
    avg_sq = [f32(value * area_inv) for value in stats["sum_sq_f32"]]
    avg_cross = [f32(value * area_inv) for value in stats["sum_cross_f32"]]
    r0, r1, r2 = rsqrt_stack[0], rsqrt_stack[4], rsqrt_stack[8]

    def mul(a: float, b: float) -> float:
        return f32(a * b)

    return [
        mul(mul(avg_sq[0], r0), r0),
        mul(mul(avg_cross[0], r0), r1),
        mul(mul(avg_cross[1], r0), r2),
        mul(mul(avg_cross[0], r0), r1),
        mul(mul(avg_sq[1], r1), r1),
        mul(mul(avg_cross[2], r1), r2),
        mul(mul(avg_cross[1], r0), r2),
        mul(mul(avg_cross[2], r1), r2),
        mul(mul(avg_sq[2], r2), r2),
    ]


def verify_sample(
    sample: dict[str, object], index: int, expected_low_endpoint: int
) -> tuple[float, float]:
    entry = sample["entry"]
    helper_pre = sample["helper_pre"]
    tile = entry["source_tile"]
    require(tile["read_ok"], f"sample {index}: tile read failed")
    raw = bytes.fromhex(tile["hex"])
    require(hashlib.sha256(raw).hexdigest() == tile["sha256"], f"sample {index}: tile hash")
    stats = tile_stats(raw)
    require(stats["count"] == tile["stats"]["count"], f"sample {index}: tile count")
    same_f32_list(stats["sum_sq_f32"], tile["stats"]["sum_sq_f32"], f"sample {index} sum_sq")
    same_f32_list(
        stats["sum_cross_f32"], tile["stats"]["sum_cross_f32"], f"sample {index} sum_cross"
    )
    same_f32_list(
        stats["sum_alpha_products_f32"],
        tile["stats"]["sum_alpha_products_f32"],
        f"sample {index} sum_alpha_products",
    )
    require(
        f32_bits(stats["alpha_sum_f32"]) == f32_bits(tile["stats"]["alpha_sum_f32"]),
        f"sample {index}: alpha sum",
    )

    params = entry["param_block"]["f32"]
    require(
        near(params[0], expected_low_endpoint / 1023.0, 0.0, 1e-7),
        f"sample {index}: low endpoint",
    )
    require(is_power_of_four_recip(params[1]), f"sample {index}: level variance")

    expected_noise = recompute_noise(stats, params)
    live_noise = helper_pre["noise_vector"]["f32"]
    same_f32_list(live_noise, expected_noise, f"sample {index} noise")

    expected_matrix = recompute_matrix(stats, helper_pre["rsqrt_diag_stack"]["f32"])
    live_matrix = helper_pre["matrix_input_9d"]["f64"][:9]
    matrix_max_abs = max(abs(a - e) for a, e in zip(live_matrix, expected_matrix))
    matrix_max_rel = max(
        abs(a - e) / max(1.0, abs(a), abs(e)) for a, e in zip(live_matrix, expected_matrix)
    )
    require(matrix_max_abs <= 0.3, f"sample {index}: matrix abs error {matrix_max_abs}")
    require(matrix_max_rel <= 2e-7, f"sample {index}: matrix rel error {matrix_max_rel}")
    return matrix_max_abs, matrix_max_rel


def verify_store(event: dict[str, object], index: int) -> float:
    pixel = event["pixel_before"]
    rows = [
        event["row_from_p0_xmm2"]["f32"],
        event["row_from_p1_xmm1"]["f32"],
        event["row_from_p2_xmm0"]["f32"],
    ]
    expected = [
        pixel[0] * rows[0][lane] + pixel[1] * rows[1][lane] + pixel[2] * rows[2][lane]
        for lane in range(4)
    ]
    live = event["pixel_after_xmm3"]["f32"]
    err = max(abs(a - e) for a, e in zip(live, expected))
    require(err <= 2e-6, f"store {index}: transform mismatch {err}")
    require(live[3] == 0.0 or math.copysign(1.0, live[3]) < 0.0, f"store {index}: alpha lane")
    return err


def verify_runtime_report(
    label: str, path: Path, expected_low_endpoint: int
) -> tuple[int, int, float, float]:
    require(path.exists(), f"missing {path}")
    report = json.loads(path.read_text())
    require(not report["errors"], f"probe errors: {report['errors']}")
    require(report["process"]["state"] == "exited", "probe did not exit")
    require(len(report["store_samples"]) >= 12, "store sample count")
    complete = [
        sample
        for sample in report["samples"]
        if sample.get("entry")
        and sample.get("helper_pre")
        and sample.get("helper_post")
        and sample.get("transform_tail")
    ]
    require(len(complete) >= 3, "complete worker sample count")
    matrix_abs = 0.0
    matrix_rel = 0.0
    for index, sample in enumerate(complete):
        abs_err, rel_err = verify_sample(sample, index, expected_low_endpoint)
        matrix_abs = max(matrix_abs, abs_err)
        matrix_rel = max(matrix_rel, rel_err)

    by_rbp = {sample["rbp"]: sample for sample in complete}
    max_store_err = 0.0
    for index, event in enumerate(report["store_samples"]):
        max_store_err = max(max_store_err, verify_store(event, index))
        sample = by_rbp.get(event["rbp"])
        if sample is not None:
            tail = sample["transform_tail"]
            for row_name in ("row_from_p0_xmm2", "row_from_p1_xmm1", "row_from_p2_xmm0"):
                same_f32_list(event[row_name]["f32"], tail[row_name]["f32"], f"{label} store {index} {row_name}")
    return len(complete), len(report["store_samples"]), max_store_err, matrix_abs


def verify_runtime() -> tuple[int, int, float, float]:
    total_complete = 0
    total_stores = 0
    max_store_err = 0.0
    max_matrix_abs = 0.0
    for label, meta in RUNTIME_REPORTS.items():
        complete, stores, store_err, matrix_abs = verify_runtime_report(
            label, meta["path"], meta["low_endpoint"]
        )
        total_complete += complete
        total_stores += stores
        max_store_err = max(max_store_err, store_err)
        max_matrix_abs = max(max_matrix_abs, matrix_abs)
    return total_complete, total_stores, max_store_err, max_matrix_abs


def main() -> None:
    static_report = verify_static()
    complete_count, store_count, max_store_err, max_matrix_abs = verify_runtime()
    print(
        "cnr_formula=OK "
        f"libcp={static_report['libcp_sha256']} "
        f"complete_samples={complete_count} stores={store_count} "
        f"max_store_err={max_store_err:.3g} max_matrix_abs={max_matrix_abs:.3g}"
    )


if __name__ == "__main__":
    main()
