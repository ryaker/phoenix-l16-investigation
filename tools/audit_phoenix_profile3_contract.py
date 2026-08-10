#!/usr/bin/env python3
"""Audit high-impact Phoenix profile-3 contracts against admitted truth.

This is intentionally narrow and machine-deterministic. It checks execution
and source patterns whose required behavior is already admitted; it does not
promote source comments or parity metrics into evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


EXPECTED_SKIP_SHA = "1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba"


class Mt19937:
    """The std::mt19937 engine, sufficient for the admitted low-bit draws."""

    def __init__(self, seed: int) -> None:
        self.state = [0] * 624
        self.state[0] = seed & 0xFFFFFFFF
        for i in range(1, 624):
            x = self.state[i - 1] ^ (self.state[i - 1] >> 30)
            self.state[i] = (1812433253 * x + i) & 0xFFFFFFFF
        self.index = 624

    def _twist(self) -> None:
        for i in range(624):
            x = (self.state[i] & 0x80000000) | (self.state[(i + 1) % 624] & 0x7FFFFFFF)
            xa = x >> 1
            if x & 1:
                xa ^= 0x9908B0DF
            self.state[i] = self.state[(i + 397) % 624] ^ xa
        self.index = 0

    def next(self) -> int:
        if self.index >= 624:
            self._twist()
        y = self.state[self.index]
        self.index += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= y >> 18
        return y & 0xFFFFFFFF


def canonical_edges(length: int, tile: int = 64) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    start = 0
    while start < length:
        end = length if start + 2 * tile > length else start + tile
        out.append((start, end))
        if end == length:
            break
        start = end
    return out


def naive_edges(length: int, tile: int = 64) -> list[tuple[int, int]]:
    return [(start, min(start + tile, length)) for start in range(0, length, tile)]


def skip_mask(width: int, height: int, edge_builder) -> tuple[bytes, int]:
    mask = bytearray([0xFF]) * (width * height)
    tasks = 0
    for y0, y1 in edge_builder(height):
        for x0, x1 in edge_builder(width):
            tasks += 1
            rng = Mt19937(5489)
            for y in range(y0, y1, 2):
                for x in range(x0, x1, 2):
                    dx = rng.next() & 1
                    dy = rng.next() & 1
                    mask[min(y + dy, height - 1) * width + min(x + dx, width - 1)] = 0
    return bytes(mask), tasks


def source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phoenix",
        type=Path,
        default=Path("/Users/ryaker/L16_Phoenix/phoenix"),
        help="live Phoenix repository root",
    )
    args = parser.parse_args()
    root = args.phoenix.resolve()

    cmake = source(root / "CMakeLists.txt")
    depth = source(root / "tools/phoenix_depth.cpp")
    fuse = source(root / "tools/phoenix_fuse.cpp")
    engine_sgm = source(root / "engine/depth/cost_sgm.cpp")
    engine_sgm_h = source(root / "engine/depth/cost_sgm.h")
    engine_report = source(root / "engine/depth/PHASE3_DEPTH_REPORT.md")

    failures: list[str] = []
    warnings: list[str] = []

    if Mt19937(5489).next() != 3499211612:
        raise RuntimeError("internal MT19937 implementation failed its standard first-word check")

    admitted_mask, admitted_tasks = skip_mask(2080, 1560, canonical_edges)
    admitted_sha = hashlib.sha256(admitted_mask).hexdigest()
    naive_mask, naive_tasks = skip_mask(2080, 1560, naive_edges)
    naive_sha = hashlib.sha256(naive_mask).hexdigest()
    mask_delta = sum(a != b for a, b in zip(admitted_mask, naive_mask))
    if admitted_tasks != 768 or admitted_sha != EXPECTED_SKIP_SHA:
        raise RuntimeError(
            f"internal admitted-mask replay failed: tasks={admitted_tasks} sha={admitted_sha}"
        )

    naive_loop = (
        "for (int ty = 0; ty < H; ty += kTile)" in depth
        and "for (int tx = 0; tx < W; tx += kTile)" in depth
    )
    absorbed_edge = "start + 2 *" in depth or "tx + 2 * kTile" in depth
    if naive_loop and not absorbed_edge:
        failures.append(
            "SKIP_MASK_EDGE_TILING: production tool uses simple +=64 edge tiles; "
            f"that is {naive_tasks} task RNG restarts, not admitted {admitted_tasks}, "
            f"and changes {mask_delta} bytes (wrong sha {naive_sha})."
        )
    if "return depth::buildSkipMaskPattern2(W, H, 64, 64);" not in depth:
        failures.append(
            "SKIP_MASK_IMPLEMENTATION: production tool does not delegate pattern 2 "
            "to the admitted absorbed-edge generator."
        )

    option_uses = len(re.findall(r"\bPHOENIX_DETERMINISTIC\b", cmake))
    if option_uses == 1:
        failures.append(
            "DETERMINISTIC_OPTION_UNUSED: PHOENIX_DETERMINISTIC is declared but never "
            "consumed by a target definition or runtime policy."
        )

    production_dirs = re.findall(
        r"aggregateBandedPath\(local, guide, params,\s*(-?\d),\s*(-?\d),",
        depth,
    )
    expected_dirs = [
        ("1", "0"),
        ("1", "1"),
        ("0", "1"),
        ("-1", "1"),
        ("-1", "0"),
        ("-1", "-1"),
        ("0", "-1"),
        ("1", "-1"),
    ]
    if len(production_dirs) != 8:
        failures.append(f"G43_PATH_COUNT: production tool has {len(production_dirs)} parsed passes, not 8.")
    elif production_dirs != expected_dirs:
        warnings.append(
            "G43_TRACE_ORDER: production serial order is "
            + str(production_dirs)
            + "; admitted positive-group then negative-group order is "
            + str(expected_dirs)
            + ". Values remain equivalent only while contributions are nonnegative "
            "and each combine is saturating-u16."
        )

    if "bool g_satU16 = true;" not in depth:
        failures.append("G43_REPRESENTATION: production default is not saturating-u16 accumulation.")
    if "g_sgmInit2000 = std::getenv(\"PHX_SGMINITHUGE\") == nullptr" not in depth:
        failures.append("G43_INIT: production default does not select the admitted u16-2000 scratch init.")

    if "meanA := 1" in fuse and "lane 3 == 1.0" in fuse:
        failures.append(
            "CNR_LANE3: production CNR still substitutes alpha/guide lane 1.0 even though "
            "the admitted producer transform is data-driven lane3=guide^2. The guide's "
            "public source remains investigation work."
        )

    if 'std::string refine_mode = "auto";' in depth:
        warnings.append(
            "PREFUSION_FIT_ACTIVE: production depth defaults to an explicitly labeled "
            "NCC self-calibration fit instead of a formula-closed installed BA replay."
        )

    stale_four_path = (
        "standard 4-path set" in engine_sgm_h
        or "four SGM" in engine_sgm_h
        or "4-path set" in engine_report
        or "SGM aggregation over 4 paths" in source(root / "engine/depth/pipeline.cpp")
    )
    engine_passes = len(re.findall(r"aggregatePath\(local, guide, params,", engine_sgm))
    if stale_four_path:
        warnings.append(
            "STALE_DEPTH_CONTRACT: engine/depth headers/report/pipeline still describe four-path "
            f"G-43 although cost_sgm.cpp now invokes {engine_passes} paths."
        )

    print(f"phoenix={root}")
    print(
        "admitted_skip_mask="
        f"tasks:{admitted_tasks} sha256:{admitted_sha} zeros:{admitted_mask.count(0)}"
    )
    print(
        "simple_edge_skip_mask="
        f"tasks:{naive_tasks} sha256:{naive_sha} byte_delta:{mask_delta}"
    )
    for item in failures:
        print(f"FAIL {item}")
    for item in warnings:
        print(f"WARN {item}")
    print(f"result failures={len(failures)} warnings={len(warnings)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
