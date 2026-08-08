#!/usr/bin/env python3
"""Verify the installed and captured MonoFusion mode-1 formula."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/prefusion_monofusion_mode1"
TILE = RUN / "unit1_35mm_profile1"
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bytes(value: float) -> bytes:
    return struct.pack("<f", value)


def call_target(data: bytes, va: int) -> int:
    require(data[va] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", data, va + 1)[0]


def verify_static() -> list[float]:
    require(sha256(LIBCP) == LIBCP_SHA256, "installed libcp SHA-256 changed")
    data = LIBCP.read_bytes()
    windows = {
        (0x19F790, 0x1A2520): "561a50843c894405604ce235b46856a3229151113cf2cd5f670e6d3f8446c060",
        (0x1A2FF0, 0x1A3C00): "57ec3832784ce4181ec28cb211232394a210375f8ef79c04c2e0a27f7f45cb31",
        (0x1A750, 0x1AB10): "94bc41c8984cc9cfb5dc323fe23c4ff0de7a88e4240ca5405dfe5160ba347dd1",
        (0x1A05D7, 0x1A068E): "1f6d5905c890c2c3129cfe0055ced064edf73a100bbe17ee80406fce2f63f577",
        (0x1A0730, 0x1A1D30): "1436eb9ba21ebede9ef1f19f561804ffd60b42f4dc1c9831edae8c0e47af3f78",
        (0x1A1D8D, 0x1A1F30): "544019bf8cb8d1e586b59d763cff1ef28e0762849983eb4304178060b963a063",
        (0x1A2144, 0x1A2242): "e1f276343a4d70c4d04e450b180d9caf40120369569454ba8555fc1094d6200c",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(data[start:end]).hexdigest()
        require(actual == expected, f"installed window 0x{start:x}..0x{end:x} changed")
    calls = {
        0x1A05B0: 0x1A750,
        0x1A1D52: 0x1A28F0,
        0x1A1D80: 0x18DA80,
        0x1A1D88: 0x1A2C10,
        0x1A1FF2: 0x18CE90,
        0x1A2042: 0x18D530,
        0x1A2091: 0x18CE90,
        0x1A223D: 0x1A2FF0,
    }
    for call, expected in calls.items():
        require(call_target(data, call) == expected, f"call target changed at 0x{call:x}")
    kernel_raw = data[0x5D0470 : 0x5D0484]
    require(
        hashlib.sha256(kernel_raw).hexdigest()
        == "33d2895fd798a81d2a80731bdff7a594382282c401f969288d620629d3ae9912",
        "mode-1 low-pass kernel changed",
    )
    kernel = list(struct.unpack("<5f", kernel_raw))
    require(
        kernel
        == [
            0.021900000050663948,
            0.22849999368190765,
            0.4991999864578247,
            0.22849999368190765,
            0.021900000050663948,
        ],
        "mode-1 low-pass coefficients changed",
    )
    return kernel


def verify_report_files(report: dict) -> None:
    for name, item in report["files"].items():
        path = Path(item["path"])
        require(path.is_file(), f"missing capture {name}")
        require(path.stat().st_size == item["size"], f"capture size changed: {name}")
        require(sha256(path) == item["sha256"], f"capture SHA-256 changed: {name}")


def source_region(path: Path, stride: int, x0: int, y0: int, width: int, height: int):
    rows = []
    with path.open("rb") as stream:
        for y in range(y0, y0 + height):
            stream.seek((y * stride + x0) * 4)
            raw = stream.read(width * 4)
            require(len(raw) == width * 4, "short source-region read")
            rows.append(list(struct.unpack(f"<{width}f", raw)))
    return rows


def verify_lowpass(kernel: list[float], patch_report: dict) -> None:
    desc = patch_report["patch"]["source_original"]
    stride = desc["stride"]
    delta = (desc["data"] - desc["owner"]) // 4
    y0, x0 = divmod(delta, stride)
    require((x0, y0) == (61, 56), "captured source-patch origin changed")

    source = source_region(TILE / "source0_full.f32", stride, x0 - 2, y0 - 2, 20, 20)
    original_raw = (TILE / "patch_source_original.f32").read_bytes()
    original = list(struct.unpack("<256f", original_raw))
    expected_original = [source[y + 2][x + 2] for y in range(16) for x in range(16)]
    require(
        b"".join(f32_bytes(value) for value in expected_original) == original_raw,
        "captured original patch does not join to full source",
    )

    # The installed helper performs the vertical pass first, then horizontal;
    # both five-term sums advance from offset -2 through +2 in float32.
    vertical = [[0.0] * 20 for _ in range(16)]
    for y in range(16):
        for x in range(20):
            total = f32(0.0)
            for tap in range(5):
                total = f32(total + f32(source[y + tap][x] * kernel[tap]))
            vertical[y][x] = total
    lowpass = []
    for y in range(16):
        for x in range(16):
            total = f32(0.0)
            for tap in range(5):
                total = f32(total + f32(vertical[y][x + tap] * kernel[tap]))
            lowpass.append(total)
    lowpass_raw = b"".join(f32_bytes(value) for value in lowpass)
    require(lowpass_raw == (TILE / "patch_source_raw.f32").read_bytes(), "low-pass replay mismatch")

    residual = [f32(a - b) for a, b in zip(original, lowpass)]
    residual_raw = b"".join(f32_bytes(value) for value in residual)
    require(
        residual_raw == (TILE / "patch_residual_raw.f32").read_bytes(),
        "original-minus-lowpass residual mismatch",
    )


def verify_gate() -> tuple[float, float]:
    report = json.loads((RUN / "unit1_35mm_profile1_gate.json").read_text())
    confidence = report["gate"]["confidence"]
    captured = report["gate"]["residual_scale"]
    require(0.5 < confidence <= 0.9, "capture no longer exercises the sloped gate arm")
    expected = f32(f32(confidence - f32(0.5)) * f32(2.25))
    require(f32_bytes(expected) == f32_bytes(captured), "residual confidence gate mismatch")
    return confidence, captured


def verify_partial_boundary() -> tuple[list[int], list[int]]:
    report = json.loads((RUN / "unit1_35mm_profile1_edge.json").read_text())
    verify_report_files(report)
    edge = report["edge"]
    require(edge["entry_pc"] != edge["ready_pc"], "partial arm did not reach its join")
    source_desc = edge["source_at_entry"]
    lowpass_desc = edge["lowpass_at_entry"]
    require(source_desc["size"] == [16, 10], "captured source partial changed")
    require(lowpass_desc["size"] == [16, 10], "captured low-pass partial changed")

    root = RUN / "edge"
    source = read_floats(root / "edge_source_partial.f32")
    lowpass = read_floats(root / "edge_lowpass_partial.f32")
    lowpass_block = (root / "edge_lowpass_block.f32").read_bytes()
    residual_block = (root / "edge_residual_block.f32").read_bytes()
    require(len(source) == len(lowpass) == 160, "partial payload length changed")

    # This first live partial hit starts six rows above the valid source domain.
    # The installed arm clamps every requested coordinate to the nearest valid
    # source coordinate before constructing its fixed 16x16 work blocks.
    row_map = [0] * 7 + list(range(1, 10))
    expected_lowpass = []
    expected_residual = []
    for row in row_map:
        for column in range(16):
            index = row * 16 + column
            expected_lowpass.append(lowpass[index])
            expected_residual.append(f32(source[index] - lowpass[index]))
    require(
        b"".join(f32_bytes(value) for value in expected_lowpass) == lowpass_block,
        "partial nearest-edge low-pass extension mismatch",
    )
    require(
        b"".join(f32_bytes(value) for value in expected_residual) == residual_block,
        "partial nearest-edge residual mismatch",
    )
    report2 = json.loads((RUN / "unit2_28mm_profile1_horizontal_edge.json").read_text())
    verify_report_files(report2)
    edge2 = report2["edge"]
    require(edge2["entry_pc"] != edge2["ready_pc"], "horizontal arm did not reach its join")
    source_desc2 = edge2["source_at_entry"]
    lowpass_desc2 = edge2["lowpass_at_entry"]
    require(source_desc2["size"] == [9, 16], "captured horizontal source partial changed")
    require(lowpass_desc2["size"] == [9, 16], "captured horizontal low-pass partial changed")

    root2 = RUN / "unit2_horizontal_edge"
    source2 = read_floats(root2 / "edge_source_partial.f32")
    lowpass2 = read_floats(root2 / "edge_lowpass_partial.f32")
    lowpass_block2 = (root2 / "edge_lowpass_block.f32").read_bytes()
    residual_block2 = (root2 / "edge_residual_block.f32").read_bytes()
    require(len(source2) == len(lowpass2) == 144, "horizontal partial length changed")

    column_map = list(range(9)) + [8] * 7
    expected_lowpass2 = []
    expected_residual2 = []
    for row in range(16):
        for column in column_map:
            index = row * 9 + column
            expected_lowpass2.append(lowpass2[index])
            expected_residual2.append(f32(source2[index] - lowpass2[index]))
    require(
        b"".join(f32_bytes(value) for value in expected_lowpass2) == lowpass_block2,
        "horizontal nearest-edge low-pass extension mismatch",
    )
    require(
        b"".join(f32_bytes(value) for value in expected_residual2) == residual_block2,
        "horizontal nearest-edge residual mismatch",
    )
    return row_map, column_map


def verify_invalid_overlap() -> None:
    report = json.loads((RUN / "unit1_35mm_profile1_invalid.json").read_text())
    verify_report_files(report)
    packet = report["invalid"]
    require(packet["entry_pc"] != packet["ready_pc"], "invalid arm did not reach its join")
    root = RUN / "invalid"
    target = read_floats(root / "invalid_target.f32")
    filtered_pre = read_floats(root / "invalid_filtered_pre.f32")
    filtered_post = (root / "invalid_filtered_post.f32").read_bytes()
    expected = [f32(a + b) for a, b in zip(filtered_pre, target)]
    require(
        b"".join(f32_bytes(value) for value in expected) == filtered_post,
        "invalid-overlap target fallback mismatch",
    )
    require(
        (root / "invalid_residual_pre.f32").read_bytes()
        == (root / "invalid_residual_post.f32").read_bytes(),
        "invalid-overlap branch changed residual accumulator",
    )
    require(
        f32_bytes(packet["x_after"]) == f32_bytes(f32(packet["x_before"] + 1.0)),
        "invalid-overlap X accumulator mismatch",
    )
    require(
        f32_bytes(packet["y_after"]) == f32_bytes(packet["y_before"]),
        "invalid-overlap Y accumulator changed",
    )


def read_floats(path: Path) -> tuple[float, ...]:
    raw = path.read_bytes()
    return struct.unpack(f"<{len(raw) // 4}f", raw)


def verify_final_combine(tile_report: dict) -> int:
    params = (TILE / "parameters.bin").read_bytes()
    alpha, noise_scale, vst_a, vst_b, black, white = struct.unpack_from("<6f", params)
    p0, p1, inverse_n, p3 = struct.unpack_from("<4f", params, 0x28)
    require(f32_bytes(alpha) == f32_bytes(p0), "alpha packet copy mismatch")
    require(f32_bytes(f32(1.0 - alpha)) == f32_bytes(p1), "1-alpha packet mismatch")
    require(inverse_n == 1.0, "capture source count is not one")
    require((black, white) == (42.0, 1023.0), "black/white packet changed")
    require(noise_scale > 0.0 and vst_a > 0.0 and vst_b < 0.0 and p3 > 0.0, "mode-1 packet sanity")

    target = read_floats(TILE / "scalar_map.f32")
    filtered = read_floats(TILE / "filtered_overlap.f32")
    residual = read_floats(TILE / "residual_overlap.f32")
    output = read_floats(TILE / "output_post.f32")
    require(len(target) == len(filtered) == len(residual) == len(output), "tile lengths differ")
    mismatches = 0
    for a, b, c, actual in zip(target, filtered, residual, output):
        expected = f32(f32(a * p0) + f32(b * p1))
        expected = f32(expected + f32(c * inverse_n))
        mismatches += f32_bytes(expected) != f32_bytes(actual)
    require(mismatches == 0, f"final three-image combine mismatches: {mismatches}")
    width, height = tile_report["entry"]["output"]["size"]
    require(width * height == len(output), "tile descriptor length mismatch")
    return len(output)


def main() -> None:
    kernel = verify_static()
    tile_report = json.loads((RUN / "unit1_35mm_profile1.json").read_text())
    patch_report = json.loads((RUN / "unit1_35mm_profile1_patch.json").read_text())
    require(tile_report["return"] is not None, "tile capture did not reach mode-1 return")
    require(tile_report["entry"]["sources"]["count"] == 1, "source count changed")
    require(tile_report["entry"]["flows"]["count"] == 1, "flow count changed")
    verify_report_files(tile_report)
    verify_lowpass(kernel, patch_report)
    row_map, column_map = verify_partial_boundary()
    verify_invalid_overlap()
    confidence, gate = verify_gate()
    cells = verify_final_combine(tile_report)
    print("prefusion_monofusion_mode1=OK")
    print("lowpass=vertical_then_horizontal_5tap exact_256_of_256")
    print("residual=original_source_minus_lowpass exact_256_of_256")
    print(f"partial_boundary_nearest_edge=row_map_{row_map} exact_256_of_256")
    print(f"partial_boundary_nearest_edge=column_map_{column_map} exact_256_of_256")
    print("invalid_overlap=target_fallback_c0 exact_256_of_256")
    print(f"gate_confidence={confidence:.9g} gate_scale={gate:.9g} exact_float32=OK")
    print(f"final_combine_exact={cells}_of_{cells}")


if __name__ == "__main__":
    main()
