#!/usr/bin/env python3
"""Replay the 0xfa530 vector cross-talk stage before the live AWB solve."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_PATH = (
    ROOT
    / "tools/lldb_probes/correction_liveness/verify_crosstalk_public_origin.py"
)
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
VECTOR_BODY = (0xFA530, 0xFAFF2)
VECTOR_BODY_SHA256 = "f730f7cffb498bcbab34f098201f098f8296a6ea73774e01831af9003c82c19f"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(value):
    return np.float32(value)


def load_public_module():
    spec = importlib.util.spec_from_file_location("awb_crosstalk_public", PUBLIC_PATH)
    require(spec is not None and spec.loader is not None, "cannot import public decoder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def selected_public_grid(lri_path: Path, camera_id: int) -> tuple[np.ndarray, dict]:
    public = load_public_module()
    matches = []
    for block in public.calibration_blocks(lri_path):
        for module in block["modules"]:
            if module["camera_id"] == camera_id:
                matches.append((block, module))
    require(len(matches) == 1, f"camera {camera_id}: expected one public grid, got {len(matches)}")
    block, module = matches[0]
    grid = np.frombuffer(module["raw"], dtype="<f4").reshape(
        module["height"], module["width"], 4, 4
    )
    receipt = {
        "block_index": block["block_index"],
        "module_index": module["index"],
        "camera_id": camera_id,
        "width": module["width"],
        "height": module["height"],
        "encoding": module["encoding"],
        "sha256": module["sha256"],
    }
    return grid, receipt


def collapsed_rgb_grid(public_grid: np.ndarray) -> np.ndarray:
    """Installed nonzero-m32 branch, specialized for caller gains [1,1,1]."""
    require(np.all(public_grid[:, :, 3, 2] != f32(0.0)), "mixed/zero m32 grid")
    height, width = public_grid.shape[:2]
    result = np.zeros((height, width, 3, 4), dtype=np.float32)
    for y in range(height):
        for x in range(width):
            matrix = public_grid[y, x]
            result[y, x, 0] = (
                matrix[0, 0],
                f32(matrix[0, 1] + matrix[0, 1]),
                f32(0.0),
                f32(0.0),
            )
            result[y, x, 1] = (
                f32(f32(matrix[2, 0] + matrix[1, 0]) * f32(0.5)),
                f32(f32(matrix[2, 2] + matrix[1, 1]) * f32(0.5)),
                f32(f32(matrix[2, 3] + matrix[1, 3]) * f32(0.5)),
                f32(0.0),
            )
            result[y, x, 2] = (
                f32(0.0),
                f32(matrix[3, 1] + matrix[3, 1]),
                matrix[3, 3],
                f32(0.0),
            )
    return result


def interpolate(grid: np.ndarray, u_value, v_value) -> np.ndarray:
    height, width = grid.shape[:2]
    scaled_x = f32(f32(u_value) * f32(width - 1))
    scaled_y = f32(f32(height - 1) * f32(v_value))
    x0 = int(np.trunc(scaled_x))
    y0 = int(np.trunc(scaled_y))
    x1 = min(x0 + 1, width - 1)
    y1 = min(y0 + 1, height - 1)
    fx = f32(scaled_x - f32(x0))
    fy = f32(scaled_y - f32(y0))
    result = np.empty((3, 4), dtype=np.float32)
    for row in range(3):
        for lane in range(4):
            top = grid[y0, x0, row, lane]
            bottom = grid[y1, x0, row, lane]
            left = f32(f32(f32(bottom - top) * fy) + top)
            top = grid[y0, x1, row, lane]
            bottom = grid[y1, x1, row, lane]
            right = f32(f32(f32(bottom - top) * fy) + top)
            result[row, lane] = f32(f32(f32(right - left) * fx) + left)
    return result


def transform_candidates(
    candidates: np.ndarray, aux: np.ndarray, public_grid: np.ndarray
) -> tuple[np.ndarray, dict]:
    require(candidates.shape == (aux.shape[0], 4), "candidate/aux shape mismatch")
    grid = collapsed_rgb_grid(public_grid)
    result = np.empty_like(candidates, dtype=np.float32)
    denominator = f32(f32(1.0) + f32(-0.9999899864196777))
    limiter_scale = f32(f32(1.0) / denominator)
    alpha_zero = 0
    alpha_one = 0
    alpha_partial = 0
    for index, (candidate, position) in enumerate(zip(candidates, aux)):
        matrix = interpolate(grid, position[0], position[1])
        red = f32(candidate[0] * matrix[0])
        green = f32(candidate[1] * matrix[1])
        blue = f32(candidate[2] * matrix[2])
        corrected = f32(f32(green + red) + blue)
        limiter = f32(f32(candidate[:3] - f32(1.0)) * limiter_scale)
        alpha = f32(min(f32(1.0), max(f32(0.0), *limiter)))
        if alpha == f32(0.0):
            alpha_zero += 1
        elif alpha == f32(1.0):
            alpha_one += 1
        else:
            alpha_partial += 1
        corrected[3] = candidate[3]
        result[index] = f32(corrected + f32(f32(candidate - corrected) * alpha))
    return result, {
        "limiter_scale": float(limiter_scale),
        "alpha_zero": alpha_zero,
        "alpha_one": alpha_one,
        "alpha_partial": alpha_partial,
    }


def records(report: dict) -> tuple[np.ndarray, np.ndarray]:
    for item in report.get("completed", []):
        payload = item.get("stats", {}).get("awb_worker", {}).get("candidates")
        if payload and payload["vec4"].get("payload") and payload["aux"].get("payload"):
            candidates = np.frombuffer(
                bytes.fromhex(payload["vec4"]["payload"]), dtype="<f4"
            ).reshape((-1, 4)).copy()
            aux = np.frombuffer(
                bytes.fromhex(payload["aux"]["payload"]), dtype="<f4"
            ).reshape((-1, 2)).copy()
            return candidates, aux
    raise AssertionError("report has no pre-transform candidate payload")


def replay(report: dict, lri_path: Path, camera_id: int):
    image = LIBCP.read_bytes()
    start, end = VECTOR_BODY
    require(
        hashlib.sha256(image[start:end]).hexdigest() == VECTOR_BODY_SHA256,
        "0xfa530 body hash drift",
    )
    candidates, aux = records(report)
    public_grid, receipt = selected_public_grid(lri_path, camera_id)
    transformed, stats = transform_candidates(candidates, aux, public_grid)
    return transformed, {"public_grid": receipt, **stats}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("lri", type=Path)
    parser.add_argument("camera_id", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="ascii"))
    transformed, stats = replay(report, args.lri, args.camera_id)
    raw = transformed.astype("<f4", copy=False).tobytes()
    if args.output:
        args.output.write_bytes(raw)
    print(
        "candidate_crosstalk=PASS",
        "count=" + str(transformed.shape[0]),
        "sha256=" + hashlib.sha256(raw).hexdigest(),
        "grid_sha256=" + stats["public_grid"]["sha256"],
        "alpha=zero:%d,partial:%d,one:%d"
        % (stats["alpha_zero"], stats["alpha_partial"], stats["alpha_one"]),
    )


if __name__ == "__main__":
    main()
