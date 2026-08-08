#!/usr/bin/env python3
"""Test Lumen's exact mono hot-pixel stage against captured flow source level 0."""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import struct
import sys
from pathlib import Path

import numba
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
PANCHROMATIC_TABLE_VA = 0x5AD7C0
FLOW_LUT_VA = 0x5CC080
WIDTH = 4160
HEIGHT = 3120


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PUBLIC = load_module(
    "mono_flow_public_replay",
    ROOT
    / "tools/lldb_probes/index5_guidance_channel_origin"
    / "verify_create_stereo_mono_public_reconstruction.py",
)
HOT = load_module(
    "mono_flow_hotpixel_formula",
    ROOT
    / "tools/lldb_probes/index5_guidance_channel_origin"
    / "verify_hot_pixel_formula.py",
)


@numba.njit(inline="always")
def rank6(values):
    for i in range(1, 8):
        value = values[i]
        j = i - 1
        while j >= 0 and values[j] > value:
            values[j + 1] = values[j]
            j -= 1
        values[j + 1] = value
    return values[5]


@numba.njit(parallel=True)
def residual_pass(source, phase_xor, border):
    height, width = source.shape
    output = np.zeros_like(source)
    for y in numba.prange(border, height - border):
        for x in range(border, width - border):
            values = np.empty(8, dtype=np.uint16)
            values[0] = source[y, x - 2]
            values[1] = source[y, x + 2]
            values[2] = source[y - 2, x]
            values[3] = source[y + 2, x]
            far = (x & 1) == ((y & 1) ^ phase_xor)
            step = 2 if far else 1
            values[4] = source[y - step, x - step]
            values[5] = source[y - step, x + step]
            values[6] = source[y + step, x - step]
            values[7] = source[y + step, x + step]
            statistic = rank6(values)
            center = source[y, x]
            if center > statistic:
                output[y, x] = center - statistic
    return output


@numba.njit(parallel=True)
def residual_pass_clamped(source, phase_xor):
    height, width = source.shape
    output = np.zeros_like(source)
    for y in numba.prange(height):
        for x in range(width):
            values = np.empty(8, dtype=np.uint16)
            xm2 = max(x - 2, 0)
            xp2 = min(x + 2, width - 1)
            ym2 = max(y - 2, 0)
            yp2 = min(y + 2, height - 1)
            values[0] = source[y, xm2]
            values[1] = source[y, xp2]
            values[2] = source[ym2, x]
            values[3] = source[yp2, x]
            far = (x & 1) == ((y & 1) ^ phase_xor)
            step = 2 if far else 1
            xm = max(x - step, 0)
            xp = min(x + step, width - 1)
            ym = max(y - step, 0)
            yp = min(y + step, height - 1)
            values[4] = source[ym, xm]
            values[5] = source[ym, xp]
            values[6] = source[yp, xm]
            values[7] = source[yp, xp]
            statistic = rank6(values)
            center = source[y, x]
            if center > statistic:
                output[y, x] = center - statistic
    return output


@numba.njit(inline="always")
def marked(markers, y, x):
    return 1 if markers[y, x] else 0


@numba.njit(inline="always")
def isolated(markers, y, x, phase_selector):
    if (x & 1) == phase_selector:
        outer = (
            marked(markers, y - 2, x - 2)
            + marked(markers, y - 2, x)
            + marked(markers, y - 2, x + 2)
            + marked(markers, y, x - 2)
            + marked(markers, y, x + 2)
            + marked(markers, y + 2, x - 2)
            + marked(markers, y + 2, x)
            + marked(markers, y + 2, x + 2)
        )
        inner = (
            marked(markers, y - 1, x - 1)
            + marked(markers, y - 1, x)
            + marked(markers, y - 1, x + 1)
            + marked(markers, y, x - 1)
            + marked(markers, y, x + 1)
            + marked(markers, y + 1, x - 1)
            + marked(markers, y + 1, x)
            + marked(markers, y + 1, x + 1)
        )
        if outer == 0:
            return inner < 2
        if outer != 1:
            return False
        continuation = (
            marked(markers, y - 4, x - 4) * marked(markers, y - 2, x - 2)
            + marked(markers, y - 4, x) * marked(markers, y - 2, x)
            + marked(markers, y - 4, x + 4) * marked(markers, y - 2, x + 2)
            + marked(markers, y, x - 4) * marked(markers, y, x - 2)
            + marked(markers, y, x + 4) * marked(markers, y, x + 2)
            + marked(markers, y + 4, x - 4) * marked(markers, y + 2, x - 2)
            + marked(markers, y + 4, x) * marked(markers, y + 2, x)
            + marked(markers, y + 4, x + 4) * marked(markers, y + 2, x + 2)
        )
        return inner + continuation == 0

    diamond = (
        marked(markers, y - 2, x)
        + marked(markers, y - 1, x - 1)
        + marked(markers, y - 1, x + 1)
        + marked(markers, y, x - 2)
        + marked(markers, y, x + 2)
        + marked(markers, y + 1, x - 1)
        + marked(markers, y + 1, x + 1)
        + marked(markers, y + 2, x)
    )
    cross = (
        marked(markers, y - 1, x)
        + marked(markers, y + 1, x)
        + marked(markers, y, x - 1)
        + marked(markers, y, x + 1)
    )
    if diamond == 0:
        adjacent = (
            marked(markers, y - 1, x + 2) * marked(markers, y, x + 1)
            + marked(markers, y + 1, x + 2) * marked(markers, y, x + 1)
            + marked(markers, y - 1, x - 2) * marked(markers, y, x - 1)
            + marked(markers, y + 1, x - 2) * marked(markers, y, x - 1)
            + marked(markers, y - 2, x - 1) * marked(markers, y - 1, x)
            + marked(markers, y - 2, x + 1) * marked(markers, y - 1, x)
            + marked(markers, y + 2, x - 1) * marked(markers, y + 1, x)
            + marked(markers, y + 2, x + 1) * marked(markers, y + 1, x)
        )
        return cross + adjacent < 2
    if diamond != 1:
        return False
    continuation = (
        (marked(markers, y - 1, x - 1) | marked(markers, y - 2, x))
        * marked(markers, y - 2, x - 1)
        + (marked(markers, y - 1, x + 1) | marked(markers, y - 2, x))
        * marked(markers, y - 2, x + 1)
        + (marked(markers, y + 1, x - 1) | marked(markers, y + 2, x))
        * marked(markers, y + 2, x - 1)
        + (marked(markers, y + 1, x + 1) | marked(markers, y + 2, x))
        * marked(markers, y + 2, x + 1)
        + (marked(markers, y, x + 2) | marked(markers, y - 1, x + 1))
        * marked(markers, y - 1, x + 2)
        + (marked(markers, y + 1, x + 1) | marked(markers, y, x + 2))
        * marked(markers, y + 1, x + 2)
        + (marked(markers, y, x - 2) | marked(markers, y - 1, x - 1))
        * marked(markers, y - 1, x - 2)
        + (marked(markers, y + 1, x - 1) | marked(markers, y, x - 2))
        * marked(markers, y + 1, x - 2)
        + marked(markers, y - 2, x + 2) * marked(markers, y - 1, x + 1)
        + marked(markers, y + 2, x + 2) * marked(markers, y + 1, x + 1)
        + marked(markers, y - 2, x - 2) * marked(markers, y - 1, x - 1)
        + marked(markers, y + 2, x - 2) * marked(markers, y + 1, x - 1)
        + marked(markers, y - 4, x) * marked(markers, y - 2, x)
        + marked(markers, y + 4, x) * marked(markers, y + 2, x)
        + marked(markers, y, x - 4) * marked(markers, y, x - 2)
        + marked(markers, y, x + 4) * marked(markers, y, x + 2)
    )
    return cross + continuation == 0


@numba.njit(parallel=True)
def apply_isolated(
    source, first_residual, second_residual, lut, phase_xor, threshold_multiplier
):
    height, width = source.shape
    markers = np.zeros(source.shape, dtype=np.uint8)
    for y in numba.prange(4, height - 4):
        for x in range(4, width - 4):
            candidate = source[y, x] - first_residual[y, x]
            if second_residual[y, x] > threshold_multiplier * lut[candidate]:
                markers[y, x] = 1

    output = source.copy()
    for y in numba.prange(8, height - 8):
        for x in range(8, width - 8):
            phase_selector = (y & 1) ^ phase_xor
            if markers[y, x] and isolated(markers, y, x, phase_selector):
                output[y, x] = source[y, x] - first_residual[y, x]
    return output, markers


@numba.njit
def apply_isolated_tiled(source, residual, lut, phase_xor, threshold_multiplier):
    height, width = source.shape
    initial_markers = np.zeros(source.shape, dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            candidate = source[y, x] - residual[y, x]
            if residual[y, x] > threshold_multiplier * lut[candidate]:
                initial_markers[y, x] = 1

    output = source.copy()
    for y0 in range(0, height, 256):
        y1 = min(y0 + 256, height)
        tile_height = y1 - y0
        for x0 in range(0, width, 256):
            x1 = min(x0 + 256, width)
            tile_width = x1 - x0
            local = np.empty((tile_height + 8, tile_width + 8), dtype=np.uint8)
            for local_y in range(tile_height + 8):
                global_y = min(max(y0 + local_y - 4, 0), height - 1)
                for local_x in range(tile_width + 8):
                    global_x = min(max(x0 + local_x - 4, 0), width - 1)
                    local[local_y, local_x] = initial_markers[global_y, global_x]

            for y in range(y0, y1):
                local_y = y - y0 + 4
                for x in range(x0, x1):
                    local_x = x - x0 + 4
                    phase_selector = (y & 1) ^ phase_xor
                    if local[local_y, local_x] and isolated(
                        local, local_y, local_x, phase_selector
                    ):
                        output[y, x] = source[y, x] - residual[y, x]
                        local[local_y, local_x] = 0
    return output, initial_markers


def apply_isolated_padded(source, lut, phase_xor, threshold_multiplier, mode):
    pad = 8
    padded = np.pad(source, pad, mode=mode)
    residual = residual_pass(padded, phase_xor, 2)
    corrected, markers = apply_isolated(
        padded,
        residual,
        residual,
        lut,
        phase_xor,
        threshold_multiplier,
    )
    return (
        corrected[pad:-pad, pad:-pad].copy(),
        markers[pad:-pad, pad:-pad].copy(),
    )


def bayer_median_halo(source, pad=6):
    height, width = source.shape
    padded = np.empty((height + 2 * pad, width + 2 * pad), dtype=source.dtype)
    padded[pad:-pad, pad:-pad] = source

    def project_parity(coordinate, extent):
        if coordinate < 0:
            return coordinate & 1
        if coordinate >= extent:
            return extent - 2 + (coordinate & 1)
        return coordinate

    for py in range(height + 2 * pad):
        y = py - pad
        for px in range(width + 2 * pad):
            x = px - pad
            if 0 <= y < height and 0 <= x < width:
                continue
            center_y = project_parity(y, height)
            center_x = project_parity(x, width)
            values = [
                source[neighbor_y, neighbor_x]
                for neighbor_y in (center_y - 2, center_y, center_y + 2)
                if 0 <= neighbor_y < height
                for neighbor_x in (center_x - 2, center_x, center_x + 2)
                if 0 <= neighbor_x < width
            ]
            values.sort()
            padded[py, px] = values[len(values) // 2]
    return padded


@numba.njit(parallel=True)
def apply_isolated_bayer_halo(
    padded, source, residual, luts, phase_xor, threshold_multiplier, pad
):
    padded_height, padded_width = padded.shape
    markers = np.zeros(padded.shape, dtype=np.uint8)
    for py in numba.prange(2, padded_height - 2):
        for px in range(2, padded_width - 2):
            candidate = padded[py, px] - residual[py, px]
            lane = (((py - pad) & 1) << 1) | ((px - pad) & 1)
            if residual[py, px] > threshold_multiplier * luts[lane, candidate]:
                markers[py, px] = 1

    output = source.copy()
    height, width = source.shape
    for y in numba.prange(height):
        py = y + pad
        for x in range(width):
            px = x + pad
            phase_selector = (y & 1) ^ phase_xor
            if markers[py, px] and isolated(markers, py, px, phase_selector):
                output[y, x] = source[y, x] - residual[py, px]
    return output, markers[pad:-pad, pad:-pad].copy()


@numba.njit(parallel=True)
def apply_marker_halo(
    source, residual, lut, phase_xor, threshold_multiplier, halo_kind
):
    height, width = source.shape
    pad = 4
    marker_halo = np.empty((height + 2 * pad, width + 2 * pad), dtype=np.uint8)
    for py in numba.prange(height + 2 * pad):
        for px in range(width + 2 * pad):
            if pad <= py < height + pad and pad <= px < width + pad:
                y = py - pad
                x = px - pad
                candidate = source[y, x] - residual[y, x]
                marker_halo[py, px] = 1 if residual[y, x] > threshold_multiplier * lut[candidate] else 0
            elif halo_kind == 0:
                marker_halo[py, px] = 0
            elif halo_kind == 1:
                marker_halo[py, px] = 1
            elif halo_kind == 2:
                marker_halo[py, px] = 1 if (px & 1) == 0 else 0
            else:
                marker_halo[py, px] = 1 if (px & 1) != 0 else 0

    output = source.copy()
    for y in numba.prange(height):
        for x in range(width):
            py = y + pad
            px = x + pad
            phase_selector = (y & 1) ^ phase_xor
            if marker_halo[py, px] and isolated(
                marker_halo, py, px, phase_selector
            ):
                output[y, x] = source[y, x] - residual[y, x]
    return output, marker_halo[pad:-pad, pad:-pad].copy()


def installed_row(libcp: bytes, gain: float):
    key = int(np.float32(gain) * np.float32(100.0))
    rows = []
    for index in range(28):
        values = struct.unpack_from("<I7f", libcp, PANCHROMATIC_TABLE_VA + index * 0x20)
        rows.append(values)
    return next((row for row in rows if row[0] >= key), rows[-1])


def decision_signature(markers, y, x, phase_selector):
    f = lambda dy, dx: int(markers[y + dy, x + dx] != 0)
    if (x & 1) == phase_selector:
        outer = sum(f(dy, dx) for dy in (-2, 0, 2) for dx in (-2, 0, 2)) - f(0, 0)
        inner = sum(f(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - f(0, 0)
        continuation = (
            sum(f(-4, dx) * f(-2, dx // 2) for dx in (-4, 0, 4))
            + f(0, -4) * f(0, -2)
            + f(0, 4) * f(0, 2)
            + sum(f(4, dx) * f(2, dx // 2) for dx in (-4, 0, 4))
        )
        return ("square", outer, inner, continuation)

    diamond = sum(
        f(dy, dx)
        for dy, dx in ((-2, 0), (-1, -1), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 1), (2, 0))
    )
    cross = f(-1, 0) + f(1, 0) + f(0, -1) + f(0, 1)
    adjacent = (
        f(-1, 2) * f(0, 1)
        + f(1, 2) * f(0, 1)
        + f(-1, -2) * f(0, -1)
        + f(1, -2) * f(0, -1)
        + f(-2, -1) * f(-1, 0)
        + f(-2, 1) * f(-1, 0)
        + f(2, -1) * f(1, 0)
        + f(2, 1) * f(1, 0)
    )
    continuation = (
        (f(-1, -1) | f(-2, 0)) * f(-2, -1)
        + (f(-1, 1) | f(-2, 0)) * f(-2, 1)
        + (f(1, -1) | f(2, 0)) * f(2, -1)
        + (f(1, 1) | f(2, 0)) * f(2, 1)
        + (f(0, 2) | f(-1, 1)) * f(-1, 2)
        + (f(1, 1) | f(0, 2)) * f(1, 2)
        + (f(0, -2) | f(-1, -1)) * f(-1, -2)
        + (f(1, -1) | f(0, -2)) * f(1, -2)
        + f(-2, 2) * f(-1, 1)
        + f(2, 2) * f(1, 1)
        + f(-2, -2) * f(-1, -1)
        + f(2, -2) * f(1, -1)
        + f(-4, 0) * f(-2, 0)
        + f(4, 0) * f(2, 0)
        + f(0, -4) * f(0, -2)
        + f(0, 4) * f(0, 2)
    )
    return ("diamond", diamond, cross, adjacent, continuation)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", required=True, type=Path)
    parser.add_argument("--lri", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--gain", required=True, type=float)
    parser.add_argument("--hotpixel-observed", type=Path)
    parser.add_argument("--threshold-factor", type=float, default=4.0)
    args = parser.parse_args()

    libcp = args.libcp.read_bytes()
    assert hashlib.sha256(libcp).hexdigest() == LIBCP_SHA256
    flow_lut = np.frombuffer(libcp, dtype="<u2", count=4096, offset=FLOW_LUT_VA)
    row = installed_row(libcp, args.gain)
    _, _scale, _threshold, cliff, black, white, a, b = row
    noise_lut = np.asarray(HOT.noise_lut(a, b, black, white, cliff), dtype=np.float32)

    surface, packed, context = PUBLIC.find_a2_surface(args.lri)
    raw = PUBLIC.unpack_raw10(packed, surface["row_stride"])
    public_black, _ = PUBLIC.sensor_levels(context["blocks"])
    profile = PUBLIC.selected_profile(args.lri, 1, surface["lens_position"])
    shading = PUBLIC.vignetting_plane(profile)
    observed = np.fromfile(args.observed, dtype="<u2").reshape(HEIGHT, WIDTH)

    baseline_prepared = np.multiply(
        np.subtract(raw.astype(np.float32), public_black, dtype=np.float32),
        shading,
        dtype=np.float32,
    )
    baseline_indices = np.trunc(baseline_prepared + np.float32(0.5)).astype(np.int32)
    np.clip(baseline_indices, 1, 4095, out=baseline_indices)
    baseline_mismatch = flow_lut[baseline_indices] != observed

    hotpixel_observed = None
    if args.hotpixel_observed:
        hotpixel_observed = np.fromfile(args.hotpixel_observed, dtype="<u2").reshape(
            HEIGHT, WIDTH
        )

    first = residual_pass(raw, 0, 2)
    clamped = residual_pass_clamped(raw, 0)
    variants = [
        (
            "immutable",
            apply_isolated(
                raw, first, first, noise_lut, 0, np.float32(args.threshold_factor)
            ),
        ),
    ]
    exact_padded = bayer_median_halo(raw)
    exact_residual = residual_pass(exact_padded, 0, 2)
    variants.append(
        (
            "padded_bayer_median",
            apply_isolated_bayer_halo(
                exact_padded,
                raw,
                exact_residual,
                np.stack((noise_lut, noise_lut, noise_lut, noise_lut)),
                0,
                np.float32(args.threshold_factor),
                6,
            ),
        )
    )
    for mode in ("reflect", "symmetric", "edge"):
        variants.append(
            (
                "padded_" + mode,
                apply_isolated_padded(
                    raw,
                    noise_lut,
                    0,
                    np.float32(args.threshold_factor),
                    mode,
                ),
            )
        )
    reflected = np.pad(raw, 2, mode="reflect")
    reflected_residual = residual_pass(reflected, 0, 2)[2:-2, 2:-2].copy()
    if hotpixel_observed is not None:
        actual_residual = raw.astype(np.int32) - hotpixel_observed.astype(np.int32)
        border = np.ones(raw.shape, dtype=np.bool_)
        border[8:-8, 8:-8] = False
        changed_border = border & (actual_residual != 0)
        residual_receipts = []
        for mode in ("reflect", "symmetric", "edge", "wrap"):
            padded = np.pad(raw, 2, mode=mode)
            candidate_residual = residual_pass(padded, 0, 2)[2:-2, 2:-2]
            residual_receipts.append(
                (
                    mode,
                    int(np.count_nonzero(candidate_residual[changed_border] == actual_residual[changed_border])),
                    int(np.count_nonzero(changed_border)),
                )
            )
        print("edge_residual_receipts=" + repr(residual_receipts))
        rows = np.arange(HEIGHT)[:, None]
        columns = np.arange(WIDTH)[None, :]
        side_masks = {
            "top": changed_border & (rows < 8),
            "bottom": changed_border & (rows >= HEIGHT - 8),
            "left": changed_border & (columns < 8),
            "right": changed_border & (columns >= WIDTH - 8),
        }
        print(
            "reflect_residual_by_side="
            + repr(
                {
                    name: (
                        int(np.count_nonzero(reflected_residual[mask] == actual_residual[mask])),
                        int(np.count_nonzero(mask)),
                    )
                    for name, mask in side_masks.items()
                }
            )
        )
    for halo_kind, halo_name in enumerate(
        ("zero", "one", "sentinel_even", "sentinel_odd")
    ):
        variants.append(
            (
                "reflected_source_marker_" + halo_name,
                apply_marker_halo(
                    raw,
                    reflected_residual,
                    noise_lut,
                    0,
                    np.float32(args.threshold_factor),
                    halo_kind,
                ),
            )
        )
    for score_name, (corrected, markers) in variants:
            if hotpixel_observed is not None:
                hotpixel_bad_mask = corrected != hotpixel_observed
                hotpixel_mismatch = int(np.count_nonzero(hotpixel_bad_mask))
                actual_changed = hotpixel_observed != raw
                predicted_changed = corrected != raw
                missed_changes = int(np.count_nonzero(actual_changed & ~predicted_changed))
                false_changes = int(np.count_nonzero(~actual_changed & predicted_changed))
                missed_marker_zero = int(
                    np.count_nonzero(actual_changed & ~predicted_changed & (markers == 0))
                )
                missed_marker_one = int(
                    np.count_nonzero(actual_changed & ~predicted_changed & (markers != 0))
                )
                unequal_changes = int(
                    np.count_nonzero(
                        actual_changed & predicted_changed & hotpixel_bad_mask
                    )
                )
                bad_y, bad_x = np.nonzero(hotpixel_bad_mask)
                x_mod = np.bincount(bad_x % 256, minlength=256)
                y_mod = np.bincount(bad_y % 256, minlength=256)
                top_x_mod = sorted(
                    enumerate(x_mod.tolist()), key=lambda item: item[1], reverse=True
                )[:8]
                top_y_mod = sorted(
                    enumerate(y_mod.tolist()), key=lambda item: item[1], reverse=True
                )[:8]
                decision_counts = collections.Counter()
                decision_examples = []
                target_windows = {}
                if score_name == "immutable":
                    target_x, target_y = 3952, 179
                    for dy in (-4, -2, -1, 0, 1, 2, 4):
                        target_windows[str(dy)] = markers[
                            target_y + dy, target_x - 5 : target_x + 6
                        ].astype(int).tolist()
                    for y, x in zip(bad_y.tolist(), bad_x.tolist()):
                        if 8 <= y < HEIGHT - 8 and 8 <= x < WIDTH - 8:
                            signature = decision_signature(markers, y, x, y & 1)
                            disposition = (
                                "missed" if actual_changed[y, x] else "false"
                            )
                            decision_counts[(disposition,) + signature] += 1
                            if len(decision_examples) < 24:
                                decision_examples.append(
                                    {
                                        "xy": [x, y],
                                        "disposition": disposition,
                                        "signature": signature,
                                    }
                                )
            else:
                hotpixel_mismatch = -1
                missed_changes = false_changes = unequal_changes = -1
                missed_marker_zero = missed_marker_one = -1
                top_x_mod = top_y_mod = []
                decision_counts = collections.Counter()
                decision_examples = []
                target_windows = {}

            prepared = np.multiply(
                np.subtract(corrected.astype(np.float32), public_black, dtype=np.float32),
                shading,
                dtype=np.float32,
            )
            indices = np.trunc(prepared + np.float32(0.5)).astype(np.int32)
            np.clip(indices, 1, 4095, out=indices)
            rebuilt = flow_lut[indices]
            mismatch = rebuilt != observed
            bad = np.argwhere(mismatch)
            interior = mismatch[8:-8, 8:-8]
            border_mismatch = int(mismatch.sum()) - int(interior.sum())
            fixed = baseline_mismatch & ~mismatch
            introduced = ~baseline_mismatch & mismatch
            examples = [
                {
                    "xy": [int(x), int(y)],
                    "raw": int(raw[y, x]),
                    "corrected": int(corrected[y, x]),
                    "marker": int(markers[y, x]),
                    "rebuilt": int(rebuilt[y, x]),
                    "observed": int(observed[y, x]),
                }
                for y, x in bad[:12]
            ]
            print(
                "first_phase_xor=0",
                f"isolation_mode={score_name}",
                "phase_selector=0",
                f"pixels_exact={rebuilt.size - len(bad)}/{rebuilt.size}",
                f"interior_mismatch={int(interior.sum())}",
                f"border_mismatch={border_mismatch}",
                f"fixed={int(fixed.sum())}",
                f"introduced={int(introduced.sum())}",
                f"markers={int(markers.sum())}",
                f"changed={int(np.count_nonzero(corrected != raw))}",
                f"hotpixel_mismatch={hotpixel_mismatch}",
                f"missed_changes={missed_changes}",
                f"false_changes={false_changes}",
                f"missed_marker_zero={missed_marker_zero}",
                f"missed_marker_one={missed_marker_one}",
                f"unequal_changes={unequal_changes}",
                f"top_x_mod256={top_x_mod}",
                f"top_y_mod256={top_y_mod}",
                f"decision_counts={decision_counts.most_common(24)}",
                f"decision_examples={decision_examples}",
                f"target_windows={target_windows}",
                f"row={int(row[0])}",
                f"examples={examples}",
            )


if __name__ == "__main__":
    main()
