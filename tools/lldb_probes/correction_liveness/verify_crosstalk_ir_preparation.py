#!/usr/bin/env python3
"""Replay the selected IR grid and cross-talk matrix preparation exactly."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


AMOUNT = load_module("crosstalk_amount_replay", HERE / "verify_crosstalk_amount_formula.py")
PUBLIC = load_module("crosstalk_public_replay", HERE / "verify_crosstalk_public_origin.py")


CASES = (
    {
        "label": "unit1_28mm_a1",
        "lri": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        "camera_key": 0,
        "amount_dir": ROOT / "runs/correction_liveness/amount_fit_unit1_28mm_a1",
        "formula_dir": ROOT / "runs/correction_liveness/formula_unit1_28mm_a1",
        "owner_grid": ROOT
        / "runs/correction_liveness/formula_unit1_28mm_a1/callback_grid_a_f32.bin",
        "ir_grid": ROOT
        / "runs/correction_liveness/formula_unit1_28mm_a1/callback_grid_b_f32.bin",
        "prepared": True,
    },
    {
        "label": "unit1_28mm_b2",
        "lri": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        "camera_key": 6,
        "amount_dir": ROOT
        / "runs/correction_liveness/amount_fit_unit1_28mm_b2_direct",
        "formula_dir": ROOT
        / "runs/correction_liveness/ir_origin_unit1_28mm_b2_direct",
        # This older capture predates the owner-grid artifact rename.
        "owner_grid": ROOT
        / "runs/correction_liveness/ir_origin_unit1_28mm_b2_direct/public_crosstalk_grid_f32.bin",
        "ir_grid": ROOT
        / "runs/correction_liveness/ir_origin_unit1_28mm_b2_direct/ir_diagonal_grid_f32.bin",
        "prepared": False,
    },
    {
        "label": "unit2_28mm_a1",
        "lri": Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
        "camera_key": 0,
        "amount_dir": ROOT / "runs/correction_liveness/amount_fit_unit2_28mm_a1",
        "formula_dir": ROOT / "runs/correction_liveness/formula_unit2_28mm_a1",
        "owner_grid": ROOT
        / "runs/correction_liveness/formula_unit2_28mm_a1/callback_grid_a_f32.bin",
        "ir_grid": ROOT
        / "runs/correction_liveness/formula_unit2_28mm_a1/callback_grid_b_f32.bin",
        "prepared": True,
    },
)


def selected_sensor_grid(data, mapping, report: dict, camera_key: int) -> tuple[np.ndarray, float]:
    fit = report["fit"]
    sensor = fit["sensor_type"]
    variant = bool(fit["variant_flag"])
    group = AMOUNT.group_for_camera(camera_key)
    amount = np.float32(fit["return_xmm0"][0])
    if amount < np.float32(0.0):
        selected = AMOUNT.table(data, mapping, "C", sensor, variant, group)
    else:
        grid_a = AMOUNT.table(data, mapping, "A", sensor, variant, group)
        grid_b = AMOUNT.table(data, mapping, "B", sensor, variant, group)
        selected = AMOUNT.f32(
            AMOUNT.f32(grid_a * amount)
            + AMOUNT.f32(grid_b * np.float32(np.float32(1.0) - amount))
        )
    return selected.reshape(13, 17, 4), float(amount)


def build_ir_grid(selected: np.ndarray) -> np.ndarray:
    shaped = AMOUNT.f32(
        AMOUNT.f32(AMOUNT.f32(selected - np.float32(1.0)) * np.float32(0.75))
        + np.float32(1.0)
    )
    result = np.zeros((13, 17, 4, 4), dtype=np.float32)
    result[:, :, 0, 0] = shaped[:, :, 0]
    result[:, :, 1, 1] = shaped[:, :, 1]
    result[:, :, 2, 2] = shaped[:, :, 1]
    result[:, :, 3, 3] = shaped[:, :, 2]
    return result


def verify_prepared(case: dict, owner: np.ndarray, ir: np.ndarray) -> dict | None:
    if not case["prepared"]:
        return None
    report = json.loads((case["formula_dir"] / "report.json").read_text(encoding="ascii"))
    vector = report["helper"]["callback_channel_vector_f32"]
    bayer_awb = np.asarray([vector[0], vector[1], vector[1], vector[2]], dtype=np.float32)
    diagonal = np.diag(bayer_awb).astype(np.float32)
    inverse = np.diag(np.float32(1.0) / bayer_awb).astype(np.float32)
    corners = ((0, 0), (1, 0), (0, 1), (1, 1))
    expected = np.stack(
        [((inverse @ owner[y, x] @ diagonal) @ ir[y, x]) for y, x in corners]
    ).astype(np.float32)
    observed = np.fromfile(case["formula_dir"] / "prepared_matrices.bin", dtype="<f4").reshape(
        4, 4, 4
    )
    require(
        np.array_equal(expected.view("<u4"), observed.view("<u4")),
        f"{case['label']}: prepared matrix mismatch",
    )
    return {
        "awb_rgb": [float(vector[index]) for index in range(3)],
        "bayer_awb": [float(value) for value in bayer_awb],
        "corner_order_yx": [list(item) for item in corners],
        "matrix_words_exact": int(expected.size),
    }


def verify_case(case: dict, data, mapping) -> dict:
    amount_report = json.loads((case["amount_dir"] / "report.json").read_text(encoding="ascii"))
    require(
        amount_report["desired_camera_id"] == case["camera_key"],
        f"{case['label']}: amount camera key",
    )
    public_receipt = PUBLIC.verify_case(
        case["label"], case["lri"], case["camera_key"], case["owner_grid"]
    )
    selected, amount = selected_sensor_grid(data, mapping, amount_report, case["camera_key"])
    expected_ir = build_ir_grid(selected)
    observed_ir = np.fromfile(case["ir_grid"], dtype="<f4").reshape(13, 17, 4, 4)
    require(
        np.array_equal(expected_ir.view("<u4"), observed_ir.view("<u4")),
        f"{case['label']}: generated IR grid mismatch",
    )
    owner = np.fromfile(case["owner_grid"], dtype="<f4").reshape(13, 17, 4, 4)
    return {
        "label": case["label"],
        "camera_key": case["camera_key"],
        "public_camera_id": public_receipt["selected_public_match"]["camera_id"],
        "public_module_index": public_receipt["selected_public_match"]["module_index"],
        "public_encoding": public_receipt["selected_public_match"]["encoding"],
        "selected_amount": amount,
        "selected_ir_input_words_exact": int(selected.size),
        "generated_ir_matrix_words_exact": int(expected_ir.size),
        "prepared": verify_prepared(case, owner, observed_ir),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data, mapping = AMOUNT.verify_static()
    public_static = PUBLIC.verify_static()
    cases = [verify_case(case, data, mapping) for case in CASES]
    result = {
        "status": "PASS",
        "libcp_sha256": AMOUNT.LIBCP_SHA256,
        "public_static_hashes": public_static,
        "cases": cases,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"crosstalk_ir_static=OK libcp={AMOUNT.LIBCP_SHA256}")
        for case in cases:
            prepared = case["prepared"]
            print(
                "crosstalk_ir=OK "
                f"label={case['label']} key={case['camera_key']} "
                f"public_camera_id={case['public_camera_id']} "
                f"module_index={case['public_module_index']} "
                f"amount={case['selected_amount']} ir_words={case['generated_ir_matrix_words_exact']} "
                f"prepared_words={prepared['matrix_words_exact'] if prepared else 0}"
            )


if __name__ == "__main__":
    main()
