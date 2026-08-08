#!/usr/bin/env python3
"""Compare one fresh Lumen/Phoenix tele range-generation sequence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LUMEN = ROOT / "runs/index5_range_pool_policy/unit2_70mm_l16_00010_fresh"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pool(prior: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    height, width = prior.shape
    low = np.full((height, width), 0xFFFF, dtype="<u2")
    high = np.zeros((height, width), dtype="<u2")
    any_valid = np.zeros((height, width), dtype=bool)
    ys = np.arange(height)
    xs = np.arange(width)
    for dy in (-1, 0, 1, 2):
        sy = np.clip(ys + dy, 0, height - 1)
        for dx in (-1, 0, 1, 2):
            sx = np.clip(xs + dx, 0, width - 1)
            values = prior[np.ix_(sy, sx)]
            valid = mask[np.ix_(sy, sx)] != 0
            low = np.where(valid, np.minimum(low, values), low).astype("<u2")
            high = np.where(valid, np.maximum(high, values), high).astype("<u2")
            any_valid |= valid
    low[~any_valid] = 0xFFFF
    high[~any_valid] = 0
    return low, high


def map_bands(
    low: np.ndarray, high: np.ndarray, target_width: int, target_height: int
) -> tuple[np.ndarray, np.ndarray]:
    source_height, source_width = low.shape
    mapped_x = (
        np.arange(target_width, dtype=np.int64) * (source_width - 1)
        // (target_width - 1)
    )
    mapped_y = (
        np.arange(target_height, dtype=np.int64) * (source_height - 1)
        // (target_height - 1)
    )
    mapped_low = low[np.ix_(mapped_y, mapped_x)].astype(np.int64)
    mapped_high = high[np.ix_(mapped_y, mapped_x)].astype(np.int64)
    lower = np.maximum(mapped_low - 1, 0).astype("<u2")
    upper = np.minimum(mapped_high + 1, 1463).astype("<u2")
    return lower, upper


def read_u16(path: Path, width: int, height: int) -> np.ndarray:
    values = np.fromfile(path, dtype="<u2")
    if values.size != width * height:
        raise AssertionError(f"{path}: {values.size} words, expected {width * height}")
    return values.reshape(height, width)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lumen", type=Path, default=DEFAULT_LUMEN)
    parser.add_argument("--lumen-repeat", type=Path)
    parser.add_argument("--phoenix-index-prefix", type=Path, required=True)
    parser.add_argument("--phoenix-band-prefix", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads((args.lumen / "report.json").read_text())
    packets = {}
    for packet in report["packets"]:
        width = packet["source"]["width"]
        height = packet["source"]["height"]
        packets[(width, height)] = packet
        for item in packet["files"].values():
            path = Path(item["path"])
            if path.stat().st_size != item["size"] or sha256(path) != item["sha256"]:
                raise AssertionError(f"capture custody failed: {path}")

    dimensions = [(65, 49), (130, 98), (260, 195), (520, 390)]
    lumen_dimensions = dimensions + [(1040, 780)]
    lumen_depth = {}
    lumen_tables = {}
    phoenix_depth = {}
    for level, (width, height) in enumerate(lumen_dimensions):
        packet = packets[(width, height)]
        prior = read_u16(args.lumen / f"prior_depth_{width}x{height}.u16le", width, height)
        mask = np.fromfile(args.lumen / f"prior_skip_{width}x{height}.u8", dtype=np.uint8).reshape(
            height, width
        )
        observed_low = read_u16(
            args.lumen / f"range_low_{width}x{height}.u16le", width, height
        )
        observed_high = read_u16(
            args.lumen / f"range_high_{width}x{height}.u16le", width, height
        )
        expected_low, expected_high = pool(prior, mask)
        low_exact = int(np.count_nonzero(expected_low == observed_low))
        high_exact = int(np.count_nonzero(expected_high == observed_high))
        if low_exact != prior.size or high_exact != prior.size:
            raise AssertionError(f"Lumen pool replay {width}x{height}")
        lumen_depth[(width, height)] = prior
        lumen_tables[(width, height)] = (observed_low, observed_high)
        print(
            f"lumen_pool level={level} dims={width}x{height} "
            f"low_exact={low_exact}/{prior.size} high_exact={high_exact}/{prior.size}"
        )

    for level, (width, height) in enumerate(dimensions):
        prior = lumen_depth[(width, height)]
        phoenix_path = Path(
            f"{args.phoenix_index_prefix}_lvl{level}_{width}x{height}.u16"
        )
        phoenix_depth[(width, height)] = read_u16(phoenix_path, width, height)
        difference = phoenix_depth[(width, height)].astype(np.int32) - prior.astype(np.int32)
        print(
            f"level={level} dims={width}x{height} "
            f"index_exact={int(np.count_nonzero(difference == 0))}/{prior.size} "
            f"within4={100.0 * np.mean(np.abs(difference) <= 4):.4f}% "
            f"median_delta={float(np.median(difference)):.3f}"
        )

    for level in range(1, len(dimensions)):
        source_dims = dimensions[level - 1]
        target_dims = dimensions[level]
        source_width, source_height = source_dims
        target_width, target_height = target_dims
        lumen_low, lumen_high = lumen_tables[source_dims]
        lumen_lower, lumen_upper = map_bands(
            lumen_low, lumen_high, target_width, target_height
        )
        phoenix_mask = np.full((source_height, source_width), 0xFF, dtype=np.uint8)
        phoenix_low, phoenix_high = pool(phoenix_depth[source_dims], phoenix_mask)
        phoenix_lower, phoenix_upper = map_bands(
            phoenix_low, phoenix_high, target_width, target_height
        )

        dumped = np.fromfile(
            Path(f"{args.phoenix_band_prefix}_lvl{level}_{target_width}x{target_height}.u16"),
            dtype="<u2",
        ).reshape(target_height, target_width, 2)
        if not np.array_equal(dumped[..., 0], phoenix_lower):
            raise AssertionError(f"Phoenix lower dump {target_width}x{target_height}")
        if not np.array_equal(dumped[..., 1], phoenix_upper):
            raise AssertionError(f"Phoenix upper dump {target_width}x{target_height}")

        truth = lumen_depth[target_dims]
        lumen_access = (truth >= lumen_lower) & (truth < lumen_upper)
        phoenix_access = (truth >= phoenix_lower) & (truth < phoenix_upper)
        low_exact = np.mean(phoenix_low == lumen_low)
        high_exact = np.mean(phoenix_high == lumen_high)
        print(
            f"transition={source_width}x{source_height}->{target_width}x{target_height} "
            f"source_table_exact_low={100.0 * low_exact:.4f}% "
            f"high={100.0 * high_exact:.4f}% "
            f"truth_in_lumen_band={100.0 * np.mean(lumen_access):.4f}% "
            f"truth_in_phoenix_band={100.0 * np.mean(phoenix_access):.4f}% "
            f"phoenix_band_mean={float(np.mean(phoenix_upper.astype(np.int32) - phoenix_lower)):.3f}"
        )

    if args.lumen_repeat:
        repeat_report = json.loads((args.lumen_repeat / "report.json").read_text())
        for packet in repeat_report["packets"]:
            for item in packet["files"].values():
                path = Path(item["path"])
                if path.stat().st_size != item["size"] or sha256(path) != item["sha256"]:
                    raise AssertionError(f"repeat capture custody failed: {path}")
        for level, (width, height) in enumerate(lumen_dimensions):
            first = lumen_depth[(width, height)].astype(np.int32)
            repeat = read_u16(
                args.lumen_repeat / f"prior_depth_{width}x{height}.u16le",
                width,
                height,
            ).astype(np.int32)
            difference = first - repeat
            print(
                f"lumen_repeat level={level} dims={width}x{height} "
                f"exact={100.0 * np.mean(difference == 0):.4f}% "
                f"within4={100.0 * np.mean(np.abs(difference) <= 4):.4f}% "
                f"mae={float(np.mean(np.abs(difference))):.4f}"
            )

    print("tele_range_generation_comparison=OK")


if __name__ == "__main__":
    main()
