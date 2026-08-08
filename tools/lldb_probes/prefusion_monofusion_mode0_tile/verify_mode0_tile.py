#!/usr/bin/env python3
"""Verify a captured production-profile MonoFusion mode-0 tile."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/prefusion_monofusion_mode0_tile/unit1_28mm"
REPORT = RUN / "report.json"
UNIT1_LRI = Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri")
THRESHOLD_REPORT = (
    ROOT / "runs/prefusion_monofusion_flow_origin/unit1_28mm_threshold/threshold_map.json"
)
FLOW_STAGE = (
    ROOT
    / "runs/prefusion_monofusion_flow_origin/unit1_28mm_stages/overlap_16x16_search_r2.f32x2le"
)
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def x86_rcp(value: float) -> float:
    word = bits(value)
    sign = word & 0x80000000
    exponent = (word >> 23) & 0xFF
    fraction = word & 0x7FFFFF
    if exponent == 0:
        output = sign | 0x7F800000
    elif exponent == 0xFF:
        output = sign if fraction == 0 else word | 0x400000
    elif exponent >= 253:
        output = sign
    else:
        index = fraction >> 12
        denominator = 4097 + 2 * index
        quotient = ((1 << 25) + denominator // 2) // denominator
        output = sign | ((253 - exponent) << 23) | ((quotient - 4096) << 11)
    return struct.unpack("<f", struct.pack("<I", output))[0]


def floats(path: Path) -> tuple[float, ...]:
    raw = path.read_bytes()
    return struct.unpack(f"<{len(raw) // 4}f", raw)


K_INV_SQRT2 = f32(0.7071067690849304)
K_INV_2_SQRT2 = f32(0.3535533845424652)
K_SQRT2 = f32(1.4142135381698608)
K_HALF = f32(0.4999999701976776)
K_EDGE = f32(0.9999999403953552)
K_TERMINAL_INV_SQRT2 = struct.unpack("<f", bytes.fromhex("f204353f"))[0]
K_TERMINAL_HALF = f32(0.4999999403953552)
K_INVERSE_HALF = f32(0.5)
K_NEG_QUARTER = f32(-0.2499999850988388)


def forward_line(values: list[float], first_stage: bool = False) -> list[float]:
    half = len(values) // 2
    even = values[0::2]
    odd = values[1::2]
    detail = []
    for index in range(half):
        if index + 1 == half and not first_stage:
            detail.append(f32(f32(odd[index] - even[index]) * K_INV_SQRT2))
        else:
            right = even[index + 1] if index + 1 < half else even[-1]
            first = f32(odd[index] * K_INV_SQRT2)
            second = f32(f32(even[index] + right) * K_INV_2_SQRT2)
            detail.append(f32(first - second))
    smooth = []
    for index in range(half):
        first = f32(K_SQRT2 * even[index])
        if index == 0 and not first_stage:
            second = f32(detail[0] * K_EDGE)
        else:
            left = detail[index - 1] if index else detail[0]
            second = f32(f32(left + detail[index]) * K_HALF)
        smooth.append(f32(first + second))
    result = [0.0] * len(values)
    result[0::2] = smooth
    result[1::2] = detail
    return result


def inverse_line(values: list[float], first_stage: bool = False) -> list[float]:
    half = len(values) // 2
    smooth = values[0::2]
    detail = values[1::2]
    even = []
    for index in range(half):
        if index == 0:
            if first_stage:
                even.append(
                    f32(
                        f32(smooth[0] * K_INV_SQRT2)
                        - f32(detail[0] * K_INV_SQRT2)
                    )
                )
            else:
                even.append(f32(f32(smooth[0] - detail[0]) * K_INV_SQRT2))
        else:
            first = f32(smooth[index] * K_INV_SQRT2)
            second = f32(f32(detail[index - 1] + detail[index]) * K_INV_2_SQRT2)
            even.append(f32(first - second))
    odd = []
    for index in range(half):
        first = f32(K_SQRT2 * detail[index])
        if index + 1 == half:
            second = even[index]
        else:
            second = f32(f32(even[index] + even[index + 1]) * K_INVERSE_HALF)
        odd.append(f32(first + second))
    result = [0.0] * len(values)
    result[0::2] = even
    result[1::2] = odd
    return result


def transform_axis(
    result: list[float], stride: int, axis: str, inverse: bool, first_stage: bool = False
) -> None:
    count = 16 // stride
    for fixed in range(count):
        if axis == "row":
            indices = [(fixed * stride) * 16 + k * stride for k in range(count)]
        else:
            indices = [fixed * stride + (k * stride) * 16 for k in range(count)]
        line = [result[index] for index in indices]
        line = inverse_line(line, first_stage) if inverse else forward_line(line, first_stage)
        for index, value in zip(indices, line):
            result[index] = value


def forward_terminal_lattice(result: list[float]) -> None:
    a, b, c, d = (result[index] for index in (0, 8, 128, 136))
    top_delta = f32(b - a)
    top_smooth = f32(
        f32(a * K_SQRT2) + f32(top_delta * K_TERMINAL_INV_SQRT2)
    )
    bottom_delta = f32(d - c)
    smooth_delta = f32(
        f32(f32(c * K_SQRT2) - top_smooth)
        + f32(bottom_delta * K_TERMINAL_INV_SQRT2)
    )
    result[128] = f32(smooth_delta * K_INV_SQRT2)
    result[0] = f32(
        f32(top_smooth * K_SQRT2)
        + f32(smooth_delta * K_TERMINAL_INV_SQRT2)
    )
    detail_delta = f32(bottom_delta - top_delta)
    result[136] = f32(detail_delta * K_HALF)
    result[8] = f32(
        f32(top_delta * K_EDGE) + f32(detail_delta * K_TERMINAL_HALF)
    )


def inverse_coarse_lattice(result: list[float]) -> None:
    """Replay 0x1a2c19..0x1a2fcd on the 4x4 coarse coefficient lattice."""
    x1 = result[8]
    x6 = result[0]
    x0 = result[4]
    x6 = f32(x6 - x1)
    x2 = f32(x6 * K_INV_SQRT2)
    x1 = f32(x1 * K_SQRT2)
    x1 = f32(x1 + x2)
    x9 = result[128]
    x8 = result[136]
    x9 = f32(x9 - x8)
    x3 = f32(x9 * K_INV_SQRT2)
    x8 = f32(x8 * K_SQRT2)
    x8 = f32(x8 + x3)
    x6 = f32(x6 - x9)
    x6 = f32(x6 * K_HALF)
    x9 = f32(x9 * K_EDGE)
    x9 = f32(x9 + x6)
    x1 = f32(x1 - x8)
    x3 = f32(x1 * K_INV_SQRT2)
    x8 = f32(x8 * K_SQRT2)
    x8 = f32(x8 + x3)
    x6 = f32(x6 - x0)
    x3 = f32(x6 * K_INV_SQRT2)
    x1 = f32(x1 * K_HALF)
    x4 = result[12]
    x5 = f32(x4 + x0)
    x5 = f32(x5 * K_INV_2_SQRT2)
    x1 = f32(x1 - x5)
    result[8] = x1
    x0 = f32(x0 * K_SQRT2)
    x3 = f32(x3 + x1)
    x3 = f32(x3 * K_INVERSE_HALF)
    x3 = f32(x3 + x0)
    x4 = f32(x4 * K_SQRT2)
    x4 = f32(x4 + x1)
    result[12] = x4

    x11 = result[64]
    x0 = result[68]
    x11 = f32(x11 - x0)
    x5 = f32(x11 * K_INV_SQRT2)
    x15 = f32(result[72] * K_INV_SQRT2)
    x14 = result[76]
    x1 = f32(x14 + x0)
    x1 = f32(x1 * K_INV_2_SQRT2)
    x15 = f32(x15 - x1)
    x0 = f32(x0 * K_SQRT2)
    x5 = f32(x5 + x15)
    x5 = f32(x5 * K_INVERSE_HALF)
    x5 = f32(x5 + x0)
    x14 = f32(x14 * K_SQRT2)
    x14 = f32(x14 + x15)
    result[76] = x14

    x0 = result[132]
    x12 = result[140]
    x8 = f32(x8 * K_INV_SQRT2)
    x1 = f32(x12 + x0)
    x1 = f32(x1 * K_INV_2_SQRT2)
    x8 = f32(x8 - x1)
    x9 = f32(x9 - x0)
    x7 = f32(x9 * K_INV_SQRT2)
    x0 = f32(x0 * K_SQRT2)
    x7 = f32(x7 + x8)
    x7 = f32(x7 * K_INVERSE_HALF)
    x7 = f32(x7 + x0)

    x4 = f32(result[200] * K_INV_SQRT2)
    x2 = result[196]
    x10 = result[204]
    x0 = f32(x10 + x2)
    x0 = f32(x0 * K_INV_2_SQRT2)
    x4 = f32(x4 - x0)
    x1 = result[192]
    x1 = f32(x1 - x2)
    x0 = f32(x1 * K_INV_SQRT2)
    x2 = f32(x2 * K_SQRT2)
    x0 = f32(x0 + x4)
    x0 = f32(x0 * K_INVERSE_HALF)
    x0 = f32(x0 + x2)

    x6 = f32(x6 - x11)
    x6 = f32(x6 * K_HALF)
    x9 = f32(x9 * K_HALF)
    x2 = f32(x1 + x11)
    x2 = f32(x2 * K_NEG_QUARTER)
    x2 = f32(x2 + x9)
    result[0] = x6
    x11 = f32(x11 * K_EDGE)
    x6 = f32(x6 + x2)
    x6 = f32(x6 * K_INVERSE_HALF)
    x6 = f32(x6 + x11)
    result[128] = x2
    result[64] = x6
    x1 = f32(x1 * K_EDGE)
    x1 = f32(x1 + x2)
    result[192] = x1

    x7 = f32(x7 * K_INV_SQRT2)
    x1 = f32(x0 + x5)
    x1 = f32(x1 * K_INV_2_SQRT2)
    x7 = f32(x7 - x1)
    x3 = f32(x3 - x5)
    x3 = f32(x3 * K_INV_SQRT2)
    result[4] = x3
    x5 = f32(x5 * K_SQRT2)
    x3 = f32(x3 + x7)
    x3 = f32(x3 * K_INVERSE_HALF)
    x3 = f32(x3 + x5)
    result[132] = x7
    result[68] = x3
    x0 = f32(x0 * K_SQRT2)
    x0 = f32(x0 + x7)
    x12 = f32(x12 * K_SQRT2)
    x12 = f32(x12 + x8)
    result[196] = x0

    x8 = f32(x8 * K_INV_SQRT2)
    x0 = f32(x4 + x15)
    x0 = f32(x0 * K_INV_2_SQRT2)
    x8 = f32(x8 - x0)
    x0 = f32(result[8] - x15)
    x0 = f32(x0 * K_INV_SQRT2)
    result[8] = x0
    x15 = f32(x15 * K_SQRT2)
    x0 = f32(x0 + x8)
    x0 = f32(x0 * K_INVERSE_HALF)
    x0 = f32(x0 + x15)
    result[136] = x8
    result[72] = x0
    x10 = f32(x10 * K_SQRT2)
    x10 = f32(x10 + x4)
    x4 = f32(x4 * K_SQRT2)
    x4 = f32(x4 + x8)
    result[200] = x4

    x0 = f32(result[12] - x14)
    x0 = f32(x0 * K_INV_SQRT2)
    x12 = f32(x12 * K_INV_SQRT2)
    x1 = f32(x10 + x14)
    x1 = f32(x1 * K_INV_2_SQRT2)
    x12 = f32(x12 - x1)
    result[12] = x0
    x0 = f32(x0 + x12)
    x0 = f32(x0 * K_INVERSE_HALF)
    x14 = f32(x14 * K_SQRT2)
    x0 = f32(x0 + x14)
    result[140] = x12
    result[76] = x0
    x10 = f32(x10 * K_SQRT2)
    x10 = f32(x10 + x12)
    result[204] = x10


def transform2d(values: tuple[float, ...] | list[float], inverse: bool) -> list[float]:
    result = list(values)
    if inverse:
        inverse_coarse_lattice(result)
        for axis in ("row", "column"):
            transform_axis(result, 2, axis, True)
        transform_axis(result, 1, "row", True, first_stage=True)
        transform_axis(result, 1, "column", True)
        return result

    transform_axis(result, 1, "row", False, first_stage=True)
    for stride, axis in (
        (1, "column"),
        (2, "row"),
        (2, "column"),
        (4, "row"),
        (4, "column"),
    ):
        transform_axis(result, stride, axis, False)
    forward_terminal_lattice(result)
    return result


def exact_words(expected: list[float], actual: tuple[float, ...], label: str) -> None:
    mismatches = [index for index, (a, b) in enumerate(zip(expected, actual)) if bits(a) != bits(b)]
    require(not mismatches, f"{label}: {len(mismatches)} mismatches, first={mismatches[:8]}")


def verify_static() -> tuple[float, ...]:
    data = LIBCP.read_bytes()
    require(sha256_bytes(data) == LIBCP_SHA256, "installed libcp SHA-256 changed")
    windows = {
        (0x1A3C00, 0x1A4DE0): "b340bbcc8191a708cfe7872f2c57cd2efbe9c675ee01a294b132674f6445f855",
        (0x18E940, 0x18EA20): "40bd296eaa1c0d0c4405971c5c3508c8c5900e1744255c5962bd4ef6f43b12cc",
        (0x18DA80, 0x18DC20): "4ba05579f24e311e23ad8fddcb56a3e749bcae331e3a7255b70493d9a611d6e9",
        (0x1A4DE0, 0x1A5720): "9bbeb64ca1342dea83301743c48192bcae850b15c74f38c7125680372350b4b7",
        (0x1A28F0, 0x1A2C10): "960205b48b16561cd498e8415fa456d61890faa4a1a068eb15a121a3f6046ce4",
        (0x1A2C10, 0x1A2FF0): "f58f4d6380855b24bb1bbb21fffa418b45ca9fc16f9fa7461767d012fbc98ab2",
        (0x1908B0, 0x190DA0): "fa0a42c2cffd6d7d42c6bc115800dc8ef08949bf04ec4d1344aaa15a4d541c55",
        (0x1A7F20, 0x1A8320): "ddbe94f0fbf63d00175abde84e96a6ee749577e7e37d4eaf4b9beefd4cc5908a",
    }
    for (start, end), expected in windows.items():
        require(sha256_bytes(data[start:end]) == expected, f"static window 0x{start:x} changed")
    table = data[0x5D0070:0x5D0470]
    require(
        sha256_bytes(table) == "3eebf27ff044f8a715e45ab3fe17972728f2bf0e596d1259d7d2aa3d25c85ca4",
        "coefficient table changed",
    )
    return struct.unpack("<256f", table)


def verify_files(report: dict) -> None:
    for name, item in report["files"].items():
        path = Path(item["path"])
        require(path.is_file(), f"missing capture {name}")
        require(path.stat().st_size == item["size"], f"capture size changed: {name}")
        require(sha256_bytes(path.read_bytes()) == item["sha256"], f"capture hash changed: {name}")


def verify_auxiliary_public_origin(report: dict) -> tuple[int, float]:
    helper_path = (
        ROOT
        / "tools/lldb_probes/prefusion_monofusion_flow_origin/verify_threshold_map_public_origin.py"
    )
    spec = importlib.util.spec_from_file_location("mode0_threshold_public", helper_path)
    require(spec is not None and spec.loader is not None, "cannot import threshold verifier")
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)

    threshold = json.loads(THRESHOLD_REPORT.read_text())
    build = threshold["threshold_map_builds"][0]
    models = helper.decode_modules(UNIT1_LRI)
    camera_id = list(models)[build["calibration_index_0x60"]]
    grid_width, grid_height, profile = helper.interpolate(
        models[camera_id], build["mirror_position_0x50"]
    )
    require((grid_width, grid_height) == (17, 13), "public vignetting grid changed")

    actual = np.memmap(RUN / "auxiliary_full.f32le", dtype="<f4", mode="r").reshape(3120, 4160)
    step = f32(260.0)
    inverse = f32(f32(1.0) / step)
    checked = 0
    for y in range(3120):
        grid_y = min(y // 260, 11)
        local_y = f32(float(y - grid_y * 260))
        ty = f32(local_y * inverse)
        for grid_x in range(16):
            start = grid_x * 260
            end = min(start + 260, 4160)
            top_left = profile[grid_y * 17 + grid_x]
            top_right = profile[grid_y * 17 + grid_x + 1]
            bottom_left = profile[(grid_y + 1) * 17 + grid_x]
            bottom_right = profile[(grid_y + 1) * 17 + grid_x + 1]
            left_delta = f32(bottom_left - top_left)
            right_delta = f32(bottom_right - top_right)
            left = f32(f32(ty * left_delta) + top_left)
            right = f32(f32(ty * right_delta) + top_right)
            row_slope = f32(f32(right - left) * inverse)
            local_x = np.arange(end - start, dtype=np.float64)
            expected = (local_x * float(row_slope) + float(left)).astype("<f4")
            observed = actual[y, start:end]
            require(
                np.array_equal(expected.view("<u4"), observed.view("<u4")),
                f"public auxiliary map mismatch in row {y}, segment {grid_x}",
            )
            checked += end - start
    patch_sum = f32(0.0)
    for y in range(8):
        for x in range(8):
            patch_sum = f32(patch_sum + float(actual[y, x]))
    patch_mean = f32(patch_sum / f32(64.0))
    require(
        bits(patch_mean) == bits(report["patch"]["auxiliary_mean"]),
        "public auxiliary 8x8 mean mismatch",
    )
    return checked, patch_mean


def verify_flow_conversion(report: dict) -> tuple[int, int]:
    flow_item = next(item for item in report["files"].values() if item.get("element") == "i16x2")
    packed = np.fromfile(flow_item["path"], dtype="<i2").astype(np.int64)
    produced = np.fromfile(FLOW_STAGE, dtype="<f4").astype(np.int64)
    require(len(packed) == len(produced) == 519 * 389 * 2, "flow component count")
    wrapped = ((produced + 32768) & 0xFFFF) - 32768
    require(np.array_equal(wrapped, packed), "float-flow to packed-int16 conversion mismatch")
    wrapped_components = int(np.count_nonzero(produced != wrapped))
    require(wrapped_components == 146146, "wrapped rejection component count changed")
    return len(packed), wrapped_components


def verify_inverse_stages() -> int:
    source = floats(RUN / "patch_source_coeff_post.f32le")
    expected = list(source)
    checkpoints = []
    inverse_coarse_lattice(expected)
    checkpoints.append(("coarse", list(expected)))
    for axis in ("row", "column"):
        transform_axis(expected, 2, axis, True)
    checkpoints.append(("stride2", list(expected)))
    transform_axis(expected, 1, "row", True, first_stage=True)
    checkpoints.append(("stride1row", list(expected)))
    for name, values in checkpoints:
        exact_words(values, floats(RUN / f"inverse_{name}.f32le"), f"inverse {name} stage")
    return len(checkpoints)


def verify_noise(report: dict, mean: float) -> float:
    target = floats(RUN / "patch_target_spatial.f32le")
    alpha, noise_scale, a, b, black, white = struct.unpack_from(
        "<6f", (RUN / "parameters.bin").read_bytes()
    )
    require(alpha > 0.0 and noise_scale > 0.0, "parameter packet sanity")
    reciprocal_square_sum = f32(0.0)
    for value in target:
        shifted = f32(value + f32(0.1))
        reciprocal = x86_rcp(shifted)
        reciprocal_square_sum = f32(reciprocal_square_sum + f32(reciprocal * reciprocal))
    reciprocal_square_mean = f32(reciprocal_square_sum / f32(256.0))
    harmonic = f32(math.sqrt(x86_rcp(reciprocal_square_mean)))
    inv_white = f32(f32(1.0) / white)
    low = f32(black * inv_white)
    shaped = f32(harmonic - black)
    shaped = f32(shaped / mean)
    shaped = f32(black + shaped)
    shaped = f32(shaped * inv_white)
    z_value = max(shaped, low)
    model = f32(f32(a * z_value) + b)
    model = max(f32(1.0e-5), model)
    white_mean = f32(mean * white)
    variance = f32(f32(white_mean * white_mean) * model)
    require(bits(variance) == bits(report["patch"]["variance"]), "auxiliary-mean variance mismatch")
    return variance


def verify_patch(report: dict, table: tuple[float, ...], variance: float) -> int:
    target_spatial = floats(RUN / "patch_target_spatial.f32le")
    target_coeff = floats(RUN / "patch_target_coeff.f32le")
    source_pre = floats(RUN / "patch_source_coeff_pre.f32le")
    source_post = floats(RUN / "patch_source_coeff_post.f32le")
    source_spatial = floats(RUN / "patch_source_spatial_post.f32le")
    exact_words(transform2d(target_spatial, False), target_coeff, "target forward transform")

    noise_scale = struct.unpack_from("<f", (RUN / "parameters.bin").read_bytes(), 4)[0]
    lambda_scale = f32(noise_scale * variance)
    expected = []
    weights = []
    for source, target, coefficient_weight in zip(source_pre, target_coeff, table):
        delta = f32(source - target)
        delta2 = f32(delta * delta)
        penalty = f32(coefficient_weight * lambda_scale)
        weight = f32(x86_rcp(f32(delta2 + penalty)) * delta2)
        weights.append(weight)
        target_part = f32(weight * target)
        source_part = f32(f32(f32(1.0) - weight) * source)
        expected.append(f32(target_part + source_part))
    exact_words(expected, source_post, "Wiener coefficient blend")
    exact_words(transform2d(source_post, True), source_spatial, "source inverse transform")

    confidence = f32(256.0)
    for index in range(0, 256, 4):
        group = weights[index:index + 4]
        pair02 = f32(group[0] + group[2])
        pair13 = f32(group[1] + group[3])
        group_sum = f32(pair02 + pair13)
        confidence = f32(confidence - group_sum)
    confidence = f32(confidence * f32(1.0 / 256.0))
    require(bits(confidence) == bits(report["patch"]["confidence"]), "Wiener confidence mismatch")
    return len(expected)


def verify_final_combine(report: dict) -> int:
    alpha = struct.unpack_from("<f", (RUN / "parameters.bin").read_bytes())[0]
    one_minus_alpha = f32(f32(1.0) - alpha)
    target = floats(RUN / "target_tile.f32le")
    overlap = floats(RUN / "overlap_precombine.f32le")
    output = floats(RUN / "output_post.f32le")
    require(len(target) == len(overlap) == len(output) == 522 * 522, "tile size changed")
    mismatches = 0
    for target_value, overlap_value, actual in zip(target, overlap, output):
        expected = f32(f32(alpha * target_value) + f32(one_minus_alpha * overlap_value))
        mismatches += bits(expected) != bits(actual)
    require(mismatches == 0, f"final combine mismatches: {mismatches}")
    return len(output)


def main() -> None:
    table = verify_static()
    report = json.loads(REPORT.read_text())
    require(not report["errors"], f"capture errors: {report['errors']}")
    require(report["entry"]["sources"]["count"] == 1, "source count changed")
    require(report["entry"]["flows"]["count"] == 1, "flow count changed")
    require(report["entry"]["flows"]["records"][0]["size"] == [519, 389], "flow size changed")
    require(report["entry"]["secondary_output"]["size"] == [0, 0], "secondary output changed")
    verify_files(report)
    auxiliary_cells, auxiliary_mean = verify_auxiliary_public_origin(report)
    flow_components, wrapped_components = verify_flow_conversion(report)
    variance = verify_noise(report, auxiliary_mean)
    coefficients = verify_patch(report, table, variance)
    inverse_stages = verify_inverse_stages()
    cells = verify_final_combine(report)
    flow_item = next(
        item for item in report["files"].values() if item.get("element") == "i16x2"
    )
    flow = Path(flow_item["path"]).read_bytes()
    first_flow = struct.unpack_from("<2h", flow)
    print("prefusion_monofusion_mode0_tile=OK")
    print(f"auxiliary_mean_noise_variance={variance:.9g} exact_float32=OK")
    print(f"public_vignetting_auxiliary_exact={auxiliary_cells}_of_{auxiliary_cells}")
    print(
        f"flow_int16_conversion_exact={flow_components}_of_{flow_components} "
        f"wrapped_rejection_components={wrapped_components}"
    )
    print(f"inverse_stage_checkpoints_exact={inverse_stages}_of_{inverse_stages}")
    print(f"forward_wiener_inverse_exact={coefficients}_of_{coefficients}")
    print(f"final_combine_exact={cells}_of_{cells}")
    print(f"flow_type=i16x2 first_displacement={first_flow}")


if __name__ == "__main__":
    main()
