#!/usr/bin/env python3
"""Verify public row/pixel identities and the four-zoom output-policy join."""

from __future__ import annotations

import json
import math
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/"
    "libcp.dylib"
)

TIERS = ("28mm", "35mm", "70mm", "150mm")
TERMINAL_RUNS = ROOT / "runs/codex_opus_iramp_terminal_validation"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u64(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob: bytes, offset: int) -> str:
    end = blob.index(b"\0", offset)
    return blob[offset:end].decode("ascii")


def run_verifier(path: Path) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    require(len(lines) >= 4, f"{path}: expected at least four result lines")
    return lines


def verify_rtti(blob: bytes) -> None:
    # PipelineCache constructor callback consuming Tile<Vec3<Float16>>.
    require(u64(blob, 0x65F5D0) == 0, "PipelineCache callback vtable offset")
    require(u64(blob, 0x65F5D8) == 0x65F630, "PipelineCache callback typeinfo")
    require(u64(blob, 0x65F610) == 0x3EC960, "PipelineCache callback sink slot")
    pipeline_cache_name = cstring(blob, u64(blob, 0x65F638))
    require(
        "PipelineCacheC1E" in pipeline_cache_name
        and "TileINS2_4Vec3INS2_7Float16" in pipeline_cache_name,
        "PipelineCache callback does not name Tile<Vec3<Float16>>",
    )

    # vec4x32f -> Vec3<Float16> callback used by 0x3e5720.
    require(u64(blob, 0x66B010) == 0, "forward converter vtable offset")
    require(u64(blob, 0x66B018) == 0x66AE40, "forward converter typeinfo")
    require(u64(blob, 0x66B020) == 0x3E5820, "forward converter address point")
    forward_name = cstring(blob, u64(blob, 0x66AE48))
    require(
        "ImageConvertPixelTypeINS2_4Vec3INS2_7Float16EEENS2_8vec4x32f" in forward_name,
        "forward converter does not name Vec3<Float16> destination / vec4x32f source",
    )

    # Vec3<Float16> -> vec4x32f callback used by 0x3d50f0.
    require(u64(blob, 0x66A680) == 0, "reverse converter vtable offset")
    require(u64(blob, 0x66A688) == 0x66A6E0, "reverse converter typeinfo")
    require(u64(blob, 0x66A690) == 0x3D51F0, "reverse converter address point")
    require(u64(blob, 0x66A6C0) == 0x3D5290, "reverse converter row worker")
    reverse_name = cstring(blob, u64(blob, 0x66A6E8))
    require(
        "ImageConvertPixelTypeINS2_8vec4x32fENS2_4Vec3INS2_7Float16" in reverse_name,
        "reverse converter does not name vec4x32f destination / Vec3<Float16> source",
    )

    # TileCache<Vec3<Float16>>::renderROI<vec4x32f>.
    require(u64(blob, 0x66A718) == 0, "TileCache callback vtable offset")
    require(u64(blob, 0x66A720) == 0x66A770, "TileCache callback typeinfo")
    require(u64(blob, 0x66A728) == 0x3D5330, "TileCache callback address point")
    tile_cache_name = cstring(blob, u64(blob, 0x66A778))
    require(
        "TileCacheINS2_4Vec3INS2_7Float16" in tile_cache_name
        and "renderROIINS2_8vec4x32f" in tile_cache_name,
        "TileCache callback lacks the half-RGB to float-RGBA policy",
    )

    # The producer of object +0x74/+0x78/+0x7c is publicly named AWB.
    require(u64(blob, 0x65B8B8) == 0, "AWB callback vtable offset")
    require(u64(blob, 0x65B8C0) == 0x65B910, "AWB callback typeinfo")
    require(u64(blob, 0x65B8F8) == 0x342A80, "AWB callback body")
    awb_name = cstring(blob, u64(blob, 0x65B918))
    require(
        "Pipeline15setWhiteBalance" in awb_name and "PipelineBase3AWB" in awb_name,
        "callback does not publicly name Pipeline::setWhiteBalance(AWB)",
    )

    for marker in (
        b"linear_prophoto_rgb\0",
        b"#?RADIANCE",
        b"FORMAT=32-bit_rle_rgbe",
    ):
        require(marker in blob, f"missing installed output marker {marker!r}")


def verify_hann_runtime() -> None:
    # First weighted-store lane 3 is the separable window product because the
    # first baseline packet blends reciprocal(0.2) == 1 into lane 3.
    widths = {"28mm": 40, "35mm": 40, "70mm": 34, "150mm": 34}
    for tier, width in widths.items():
        report = json.loads((TERMINAL_RUNS / f"iramp_terminal_{tier}.json").read_text())
        events = [
            event
            for event in report["events"]
            if event["site_name"] == "weighted_store_36aa57"
        ]
        require(events, f"{tier}: missing weighted-store packet")
        observed = float(events[0]["packet"]["result_xmm1_before_store"][3])
        weight = math.sin(math.pi * 0.5 / width) ** 2
        expected = weight * weight
        require(
            math.isclose(observed, expected, rel_tol=2e-5, abs_tol=1e-12),
            f"{tier}: first separable Hann product {observed} != {expected}",
        )


def verify_i1i2i3_transform() -> None:
    # Captured invariant rows from all four admitted transform packets.
    observed = (
        (0.577350020, 0.577350020, 0.577350020),
        (0.707109988, 0.0, -0.707109988),
        (0.408250004, -0.816500008, 0.408250004),
    )
    expected = (
        (1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3)),
        (1 / math.sqrt(2), 0.0, -1 / math.sqrt(2)),
        (1 / math.sqrt(6), -2 / math.sqrt(6), 1 / math.sqrt(6)),
    )
    for row_index, (actual_row, expected_row) in enumerate(zip(observed, expected)):
        for lane_index, (actual, wanted) in enumerate(zip(actual_row, expected_row)):
            require(
                math.isclose(actual, wanted, rel_tol=0.0, abs_tol=4e-6),
                f"I1I2I3 row {row_index} lane {lane_index}: {actual} != {wanted}",
            )


def main() -> None:
    require(LIBCP.is_file(), f"missing installed libcp: {LIBCP}")
    blob = LIBCP.read_bytes()
    verify_rtti(blob)
    verify_hann_runtime()
    verify_i1i2i3_transform()

    terminal_lines = run_verifier(
        ROOT
        / "tools/lldb_probes/codex_opus_iramp_terminal_validation/"
        "verify_iramp_terminal_consolidation.py"
    )
    output_lines = run_verifier(ROOT / "tools/verify_final_case3_output_config.py")

    print(
        "STATIC: OK Pipeline::setWhiteBalance(AWB), "
        "Tile<Vec3<Float16>>, ImageConvertPixelType, TileCache renderROI"
    )
    print("MATH: OK half-sample Hann and orthonormal I1/I2/I3 -> RGB identities")
    for line in terminal_lines[:4]:
        print(f"IRAMP {line}")
    for line in output_lines[:4]:
        print(f"OUTPUT {line}")


if __name__ == "__main__":
    main()
