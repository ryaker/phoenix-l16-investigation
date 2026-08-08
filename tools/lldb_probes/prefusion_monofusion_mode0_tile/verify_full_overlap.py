#!/usr/bin/env python3
"""Replay every mode-0 patch contributing to the captured scalar tile."""

from __future__ import annotations

import importlib.util
import argparse
import json
import math
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/prefusion_monofusion_mode0_tile/unit1_28mm"
REMAINDER_RUN = ROOT / "runs/prefusion_monofusion_mode0_tile/unit1_28mm_patch_512"
OVERLAP_WEIGHT_BITS = (
    0x3C1D6831, 0x3DAC933B, 0x3E638C4D, 0x3ECE0E90,
    0x3F18F8B9, 0x3F471CED, 0x3F6A6D99, 0x3F7D8A5F,
    0x3F7D8A5F, 0x3F6A6D98, 0x3F471CEC, 0x3F18F8B7,
    0x3ECE0E8D, 0x3E638C48, 0x3DAC9335, 0x3C1D681E,
)


def load_base_verifier():
    path = Path(__file__).with_name("verify_mode0_tile.py")
    spec = importlib.util.spec_from_file_location("mode0_tile_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import mode-0 base verifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_base_verifier()
f32 = BASE.f32


def gather(image: np.ndarray, x0: int, y0: int) -> tuple[float, ...]:
    ys = np.clip(np.arange(y0, y0 + 16), 0, image.shape[0] - 1)
    xs = np.clip(np.arange(x0, x0 + 16), 0, image.shape[1] - 1)
    return tuple(float(value) for value in np.asarray(image[np.ix_(ys, xs)]).reshape(-1))


def patch_variance(
    target: np.ndarray,
    auxiliary: np.ndarray,
    x0: int,
    y0: int,
    a: float,
    b: float,
    black: float,
    white: float,
) -> float:
    target_xa, target_xb = max(x0, 0), min(x0 + 16, target.shape[1])
    target_ya, target_yb = max(y0, 0), min(y0 + 16, target.shape[0])
    auxiliary_xa, auxiliary_xb = max(x0, 0), min(x0 + 16, auxiliary.shape[1])
    auxiliary_ya, auxiliary_yb = max(y0, 0), min(y0 + 16, auxiliary.shape[0])
    mean_sum = f32(0.0)
    reciprocal_square_sum = f32(0.0)
    for y in range(auxiliary_ya, auxiliary_yb):
        for x in range(auxiliary_xa, auxiliary_xb):
            mean_sum = f32(mean_sum + float(auxiliary[y, x]))
    for y in range(target_ya, target_yb):
        for x in range(target_xa, target_xb):
            shifted = f32(float(target[y, x]) + f32(0.1))
            reciprocal = BASE.x86_rcp(shifted)
            reciprocal_square_sum = f32(
                reciprocal_square_sum + f32(reciprocal * reciprocal)
            )
    auxiliary_count = f32(
        float((auxiliary_xb - auxiliary_xa) * (auxiliary_yb - auxiliary_ya))
    )
    target_count = f32(
        float((target_xb - target_xa) * (target_yb - target_ya))
    )
    mean = f32(mean_sum / auxiliary_count)
    reciprocal_square_mean = f32(reciprocal_square_sum / target_count)
    harmonic = f32(math.sqrt(BASE.x86_rcp(reciprocal_square_mean)))
    inverse_white = f32(f32(1.0) / white)
    low = f32(black * inverse_white)
    shaped = f32(harmonic - black)
    shaped = f32(shaped / mean)
    shaped = f32(black + shaped)
    shaped = f32(shaped * inverse_white)
    model = max(f32(1.0e-5), f32(f32(a * max(shaped, low)) + b))
    white_mean = f32(mean * white)
    return f32(f32(white_mean * white_mean) * model)


def transform_blocks(
    blocks: np.ndarray, mode: str, oracle: Path | None, stem: str
) -> np.ndarray:
    if oracle is None:
        return np.asarray(
            [BASE.transform2d(tuple(block), mode == "inverse") for block in blocks],
            dtype="<f4",
        )
    input_path = RUN / f"full_overlap_{stem}_{mode}_input.f32le"
    output_path = RUN / f"full_overlap_{stem}_{mode}_output.f32le"
    np.asarray(blocks, dtype="<f4").tofile(input_path)
    subprocess.run([str(oracle), str(input_path), str(output_path), mode], check=True)
    output = np.fromfile(output_path, dtype="<f4")
    if output.size != blocks.size:
        raise AssertionError(f"{stem} {mode} transform size")
    return output.reshape(blocks.shape)


def verify_remainder_patch(table: tuple[float, ...]) -> None:
    report = json.loads((REMAINDER_RUN / "report.json").read_text())
    BASE.verify_files(report)
    if report["patch"]["target_origin"] != [512, -8]:
        raise AssertionError("remainder patch origin")
    target = np.fromfile(REMAINDER_RUN / "target_tile.f32le", dtype="<f4").reshape(522, 522)
    source = np.memmap(
        REMAINDER_RUN / "source0_full.f32le", dtype="<f4", mode="r"
    ).reshape(3120, 4160)
    auxiliary = np.memmap(
        REMAINDER_RUN / "auxiliary_full.f32le", dtype="<f4", mode="r"
    ).reshape(3120, 4160)
    flow = np.fromfile(
        REMAINDER_RUN / "flow0_full.i16x2le", dtype="<i2"
    ).reshape(389, 519, 2)
    _alpha, noise_scale, a, b, black, white = struct.unpack_from(
        "<6f", (REMAINDER_RUN / "parameters.bin").read_bytes()
    )
    x0, y0 = report["patch"]["target_origin"]
    dx, dy = (int(value) for value in flow[max(int(y0 / 8), 0), max(int(x0 / 8), 0)])
    expected_domain = [x0 + dx, y0 + dy, x0 + dx + 16, y0 + dy + 16]
    if report["patch"]["source_view"]["domain"] != expected_domain:
        raise AssertionError("remainder source domain")

    target_patch = gather(target, x0, y0)
    source_patch = gather(source, x0 + dx, y0 + dy)
    target_coefficients = BASE.transform2d(target_patch, False)
    source_coefficients = BASE.transform2d(source_patch, False)
    BASE.exact_words(
        list(target_patch),
        BASE.floats(REMAINDER_RUN / "patch_target_spatial.f32le"),
        "remainder target spatial",
    )
    BASE.exact_words(
        target_coefficients,
        BASE.floats(REMAINDER_RUN / "patch_target_coeff.f32le"),
        "remainder target transform",
    )
    BASE.exact_words(
        source_coefficients,
        BASE.floats(REMAINDER_RUN / "patch_source_coeff_pre.f32le"),
        "remainder source transform",
    )
    variance = patch_variance(target, auxiliary, x0, y0, a, b, black, white)
    if BASE.bits(variance) != BASE.bits(report["patch"]["variance"]):
        raise AssertionError("remainder separate-domain variance")

    lambda_scale = f32(noise_scale * variance)
    fused = []
    for source_value, target_value, coefficient_weight in zip(
        source_coefficients, target_coefficients, table
    ):
        delta = f32(source_value - target_value)
        delta2 = f32(delta * delta)
        penalty = f32(coefficient_weight * lambda_scale)
        weight = f32(BASE.x86_rcp(f32(delta2 + penalty)) * delta2)
        target_part = f32(weight * target_value)
        source_part = f32(f32(f32(1.0) - weight) * source_value)
        fused.append(f32(target_part + source_part))
    BASE.exact_words(
        fused,
        BASE.floats(REMAINDER_RUN / "patch_source_coeff_post.f32le"),
        "remainder Wiener coefficients",
    )
    BASE.exact_words(
        BASE.transform2d(fused, True),
        BASE.floats(REMAINDER_RUN / "patch_source_spatial_post.f32le"),
        "remainder inverse transform",
    )
    print(
        "remainder_patch=(512,-8) source_domain="
        f"{expected_domain} variance={variance:.9f} exact=OK"
    )


def replay(oracle: Path | None, table: tuple[float, ...]) -> tuple[np.ndarray, dict[str, int]]:
    report = json.loads((RUN / "report.json").read_text())
    BASE.verify_files(report)
    target = np.fromfile(RUN / "target_tile.f32le", dtype="<f4").reshape(522, 522)
    source = np.memmap(
        RUN / "source0_full.f32le", dtype="<f4", mode="r"
    ).reshape(3120, 4160)
    auxiliary = np.memmap(
        RUN / "auxiliary_full.f32le", dtype="<f4", mode="r"
    ).reshape(3120, 4160)
    flow = np.fromfile(RUN / "flow0_full.f32x2le", dtype="<i2").reshape(389, 519, 2)
    captured_weight_x = np.fromfile(RUN / "overlap_weight_x.f32le", dtype="<u4")
    captured_weight_y = np.fromfile(RUN / "overlap_weight_y.f32le", dtype="<u4")
    expected_weight_bits = np.asarray(OVERLAP_WEIGHT_BITS, dtype="<u4")
    if not np.array_equal(captured_weight_x, expected_weight_bits):
        raise AssertionError("horizontal overlap-weight table")
    if not np.array_equal(captured_weight_y, expected_weight_bits):
        raise AssertionError("vertical overlap-weight table")
    weight_x = expected_weight_bits.view("<f4")
    weight_y = expected_weight_bits.view("<f4")
    _alpha, noise_scale, a, b, black, white = struct.unpack_from(
        "<6f", (RUN / "parameters.bin").read_bytes()
    )

    accumulator = np.zeros(target.shape, dtype="<f4")
    counts = {"patches": 0, "valid_source": 0, "invalid_source": 0}
    records = []
    for y0 in range(-8, 536, 8):
        if y0 >= target.shape[0] or y0 + 16 <= 0:
            continue
        flow_y = min(max(int(y0 / 8), 0), flow.shape[0] - 1)
        for x0 in range(-8, 536, 8):
            if x0 >= target.shape[1] or x0 + 16 <= 0:
                continue
            flow_x = min(max(int(x0 / 8), 0), flow.shape[1] - 1)
            target_patch = gather(target, x0, y0)
            dx, dy = (int(value) for value in flow[flow_y, flow_x])
            source_x, source_y = x0 + dx, y0 + dy
            source_valid = (
                source_x < source.shape[1]
                and source_x + 16 > 0
                and source_y < source.shape[0]
                and source_y + 16 > 0
            )
            source_patch = gather(source, source_x, source_y) if source_valid else target_patch
            variance = (
                patch_variance(target, auxiliary, x0, y0, a, b, black, white)
                if source_valid
                else f32(0.0)
            )
            records.append((x0, y0, source_valid, variance, target_patch, source_patch))
            counts["valid_source" if source_valid else "invalid_source"] += 1
            counts["patches"] += 1

    target_blocks = np.asarray([record[4] for record in records], dtype="<f4")
    source_blocks = np.asarray([record[5] for record in records], dtype="<f4")
    target_coefficients = transform_blocks(target_blocks, "forward", oracle, "target")
    source_coefficients = transform_blocks(source_blocks, "forward", oracle, "source")
    fused_coefficients = np.empty_like(target_coefficients)
    for index, record in enumerate(records):
        if not record[2]:
            fused_coefficients[index] = target_coefficients[index]
            continue
        lambda_scale = f32(noise_scale * record[3])
        for coefficient, (source_value, target_value, coefficient_weight) in enumerate(
            zip(source_coefficients[index], target_coefficients[index], table)
        ):
            delta = f32(float(source_value) - float(target_value))
            delta2 = f32(delta * delta)
            penalty = f32(coefficient_weight * lambda_scale)
            weight = f32(BASE.x86_rcp(f32(delta2 + penalty)) * delta2)
            target_part = f32(weight * float(target_value))
            source_part = f32(f32(f32(1.0) - weight) * float(source_value))
            fused_coefficients[index, coefficient] = f32(target_part + source_part)
    fused_blocks = transform_blocks(fused_coefficients, "inverse", oracle, "fused")
    for index, record in enumerate(records):
        if not record[2]:
            fused_blocks[index] = target_blocks[index]

    for record, fused in zip(records, fused_blocks):
        x0, y0 = record[0], record[1]
        xa, xb = max(x0, 0), min(x0 + 16, target.shape[1])
        ya, yb = max(y0, 0), min(y0 + 16, target.shape[0])
        full = xb - xa == 16 and yb - ya == 16
        for y in range(ya, yb):
            patch_y = y - y0
            for x in range(xa, xb):
                patch_x = x - x0
                value = fused[patch_y * 16 + patch_x]
                if full:
                    term = f32(
                        f32(value * float(weight_x[patch_x]))
                        * float(weight_y[patch_y])
                    )
                else:
                    term = f32(
                        f32(float(weight_y[patch_y]) * value)
                        * float(weight_x[patch_x])
                    )
                accumulator[y, x] = f32(float(accumulator[y, x]) + term)
    return accumulator, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed-transform-oracle", type=Path)
    args = parser.parse_args()
    table = BASE.verify_static()
    verify_remainder_patch(table)
    expected, counts = replay(args.installed_transform_oracle, table)
    actual = np.fromfile(RUN / "overlap_precombine.f32le", dtype="<f4").reshape(522, 522)
    exact = expected.view("<u4") == actual.view("<u4")
    difference = np.abs(expected.astype(np.float64) - actual.astype(np.float64))
    bad = ~exact
    print(json.dumps(counts, sort_keys=True))
    print(
        f"exact={int(np.count_nonzero(exact))}_of_{exact.size} "
        f"mismatch={int(np.count_nonzero(bad))} "
        f"max_abs={float(difference.max()):.9g} mean_abs={float(difference.mean()):.9g}"
    )
    if np.any(bad):
        by_row = np.count_nonzero(bad, axis=1)
        by_column = np.count_nonzero(bad, axis=0)
        print("bad_rows", [(i, int(n)) for i, n in enumerate(by_row) if n][:24])
        print("bad_rows_tail", [(i, int(n)) for i, n in enumerate(by_row) if n][-24:])
        print("bad_columns", [(i, int(n)) for i, n in enumerate(by_column) if n][:24])
        print("bad_columns_tail", [(i, int(n)) for i, n in enumerate(by_column) if n][-24:])
        first = np.argwhere(bad)[:12]
        print(
            "first",
            [
                {
                    "x": int(x),
                    "y": int(y),
                    "expected": float(expected[y, x]),
                    "actual": float(actual[y, x]),
                    "expected_bits": f"0x{int(expected[y, x].view(np.uint32)):08x}",
                    "actual_bits": f"0x{int(actual[y, x].view(np.uint32)):08x}",
                }
                for y, x in first
            ],
        )
        raise AssertionError("full overlap replay mismatch")
    print("prefusion_monofusion_mode0_full_overlap=OK")


if __name__ == "__main__":
    main()
