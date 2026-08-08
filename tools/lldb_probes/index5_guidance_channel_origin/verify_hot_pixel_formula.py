#!/usr/bin/env python3
"""Verify the live default Guidance hot-pixel worker and isolation policy."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "runs/index5_guidance_channel_origin"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
CNR_ORIGINS_PATH = (
    ROOT / "tools/lldb_probes/denoise_route_census/verify_cnr_public_origins.py"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
RANGE_HASHES = {
    (0x2E8680, 0x2E8A00): "e844d7726efbf374695082da4ae80cc0c388146616f3d95418084c8287058cc5",
    (0x2E8CC0, 0x2E9C00): "11c88ea6ac2096820cbdfb47809353951a461486380aff51b92eeabeac6c94e2",
    (0xEF050, 0xEF0B5): "db9d1952623599ee03402d43b4bfab268336336c6773f07a4cfffadc8a8db9c3",
    (0xEF120, 0xEF503): "4ddc450d7c896a2f534890a26ea879fd4008e22c7443ea22b3893a9a431b3504",
    (0xED830, 0xEDCF2): "98526c264c2e22bdbb83b93c83ced2a976a9a871f7bad310f0b799f40354a854",
    (0xEE510, 0xEEB28): "1a1a190e39ae86278ee8e3921bb6a2101f434520f564d008fbdfe6466c8399f0",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("hot_pixel_static", STATIC_PATH)
CNR_ORIGINS = load_module("hot_pixel_cnr_origins", CNR_ORIGINS_PATH)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def noise_lut(a: float, b: float, black: float, white: float, cliff: float) -> list[float]:
    coefficients = (
        1.430853e-06,
        3.2172868e-07,
        -2.6295693e-05,
        -8.5123452e-05,
        -1.7851033e-05,
        0.0020282884,
        0.024377832,
        0.037234715,
        0.70309281,
        0.16923658,
    )
    import math

    count = int(f32(white + 1.0))
    values = []
    for index in range(count):
        x = (index + 0.5) / count
        sigma = math.sqrt(max(a * x + b, 1.0e-10))
        u = x / sigma
        polynomial = u * coefficients[0] + coefficients[1]
        for coefficient in coefficients[2:]:
            polynomial = polynomial * u + coefficient
        values.append(f32(sigma * 0.5 * (math.tanh(polynomial) + 1.0)))

    cliff_index = int(f32(black * cliff))
    slope = f32(f32(values[cliff_index + 2] - values[cliff_index - 2]) * f32(0.25))
    for index in range(cliff_index):
        values[index] = f32(
            values[cliff_index] - f32(f32(cliff_index - index) * slope)
        )
    return [f32(value * f32(white)) for value in values]


def rank6_network(values: list[int]) -> int:
    """Scalar transcription of the unsigned network at 0x2e92dd..0x2e9360."""
    r12, r11, esi, r10, edi, r14, ecx, ebx = values
    edx, r11 = min(r12, r11), max(r12, r11)
    eax, r10 = min(esi, r10), max(esi, r10)
    esi, r14 = min(edi, r14), max(edi, r14)
    edi, ebx = min(ecx, ebx), max(ecx, ebx)
    eax = max(eax, edx)
    ecx, r10 = min(r10, r11), max(r10, r11)
    edi = max(edi, esi)
    edx, ebx = min(ebx, r14), max(ebx, r14)
    esi, ecx = min(ecx, eax), max(ecx, eax)
    eax, edx = min(edx, edi), max(edx, edi)
    eax = max(eax, esi)
    edx = max(edx, ecx)
    ebx = min(ebx, r10)
    ebx = max(ebx, eax)
    ebx = min(ebx, edx)
    return ebx


def flag(value: int) -> int:
    return 1 if value & 0x8000 else 0


def isolation_decision(event: dict) -> bool:
    rows = {
        int(key): [flag(value) for value in window]
        for key, window in event["marker_windows_x_minus5_plus5"].items()
    }

    def f(y: int, dx: int) -> int:
        return rows[y][5 + dx]

    if event["x_parity"] == event["phase_selector"]:
        outer = (
            sum(f(-2, dx) for dx in (-2, 0, 2))
            + f(0, -2)
            + f(0, 2)
            + sum(f(2, dx) for dx in (-2, 0, 2))
        )
        inner = (
            sum(f(-1, dx) for dx in (-1, 0, 1))
            + f(0, -1)
            + f(0, 1)
            + sum(f(1, dx) for dx in (-1, 0, 1))
        )
        if outer == 0:
            return inner < 2
        if outer != 1:
            return False
        continuation = (
            sum(f(-4, dx) & f(-2, dx // 2) for dx in (-4, 0, 4))
            + (f(0, -4) & f(0, -2))
            + (f(0, 4) & f(0, 2))
            + sum(f(4, dx) & f(2, dx // 2) for dx in (-4, 0, 4))
        )
        return inner + continuation == 0

    diamond = (
        f(-2, 0)
        + f(-1, -1)
        + f(-1, 1)
        + f(0, -2)
        + f(0, 2)
        + f(1, -1)
        + f(1, 1)
        + f(2, 0)
    )
    cross = f(-1, 0) + f(1, 0) + f(0, -1) + f(0, 1)
    if diamond == 0:
        adjacent = (
            (f(-1, 2) & f(0, 1))
            + (f(1, 2) & f(0, 1))
            + (f(-1, -2) & f(0, -1))
            + (f(1, -2) & f(0, -1))
            + (f(-2, -1) & f(-1, 0))
            + (f(-2, 1) & f(-1, 0))
            + (f(2, -1) & f(1, 0))
            + (f(2, 1) & f(1, 0))
        )
        return cross + adjacent < 2
    if diamond != 1:
        return False
    continuation = (
        ((f(-1, -1) | f(-2, 0)) & f(-2, -1))
        + ((f(-1, 1) | f(-2, 0)) & f(-2, 1))
        + ((f(1, -1) | f(2, 0)) & f(2, -1))
        + ((f(1, 1) | f(2, 0)) & f(2, 1))
        + ((f(0, 2) | f(-1, 1)) & f(-1, 2))
        + ((f(1, 1) | f(0, 2)) & f(1, 2))
        + ((f(0, -2) | f(-1, -1)) & f(-1, -2))
        + ((f(1, -1) | f(0, -2)) & f(1, -2))
        + (f(-2, 2) & f(-1, 1))
        + (f(2, 2) & f(1, 1))
        + (f(-2, -2) & f(-1, -1))
        + (f(2, -2) & f(1, -1))
        + (f(-4, 0) & f(-2, 0))
        + (f(4, 0) & f(2, 0))
        + (f(0, -4) & f(0, -2))
        + (f(0, 4) & f(0, 2))
    )
    return cross + continuation == 0


def rank_residuals(
    source: list[list[int]], global_x: int, global_y: int, phase_xor: int
) -> tuple[list[list[int]], list[list[int]]]:
    cross = ((-2, 0), (2, 0), (0, -2), (0, 2))
    far_diagonal = ((-2, -2), (-2, 2), (2, -2), (2, 2))
    near_diagonal = ((-1, -1), (-1, 1), (1, -1), (1, 1))

    def neighborhood(x: int, y: int):
        absolute_x = global_x + x - 6
        absolute_y = global_y + y - 6
        far = (absolute_x & 1) == ((absolute_y & 1) ^ phase_xor)
        return cross + (far_diagonal if far else near_diagonal)

    first = [[0] * 13 for _ in range(13)]
    for y in range(2, 11):
        for x in range(2, 11):
            rank = sorted(source[y + dy][x + dx] for dy, dx in neighborhood(x, y))[5]
            first[y][x] = max(0, source[y][x] - rank)

    second = [[0] * 13 for _ in range(13)]
    for y in range(4, 9):
        for x in range(4, 9):
            rank = sorted(first[y + dy][x + dx] for dy, dx in neighborhood(x, y))[5]
            second[y][x] = max(0, first[y][x] - rank)
    return first, second


def verify_static() -> None:
    data = STATIC.LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    mapping = STATIC.segments(data)
    for (start, end), expected in RANGE_HASHES.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"body hash drift at {start:#x}")
    require(STATIC.instruction(data, mapping, 0x2E9467).op_str == "esi, 0x8000", "marker set")
    require(STATIC.instruction(data, mapping, 0x2E9B07).op_str == "cx, 0x7fff", "marker clear")
    require(STATIC.instruction(data, mapping, 0x2E9462).mnemonic == "mulss", "threshold multiply")
    rng = random.Random(0x2E8CC0)
    for _ in range(10000):
        values = [rng.randrange(0x10000) for _ in range(8)]
        require(rank6_network(values) == sorted(values)[5], "rank6 network mismatch")


def verify_runtime() -> tuple[int, int, int, int, str]:
    formula = json.loads((RUN_DIR / "hot_pixel_formula_unit1_28mm.json").read_text())
    decisions = json.loads((RUN_DIR / "hot_pixel_decision_unit1_28mm.json").read_text())
    require(formula["capture_complete"] and formula["patches"], "formula capture incomplete")
    patch = formula["patches"][0]
    require(len(patch["luts"]) == 4, "missing four Bayer LUT lanes")
    require(all(len(item["values_1024f"]) == 1024 for item in patch["luts"]), "LUT length")
    data = STATIC.LIBCP.read_bytes()
    sections = CNR_ORIGINS.static_helpers().macho_sections(data)
    table = CNR_ORIGINS.decode_installed_color_table(data, sections)
    matches = []
    for captured in patch["luts"]:
        captured_bytes = b"".join(struct.pack("<f", value) for value in captured["values_1024f"])
        lane_matches = []
        for row in table:
            for channel in ("red", "green", "blue"):
                generated = noise_lut(
                    row[channel]["a"],
                    row[channel]["b"],
                    row["black"][("red", "green", "blue").index(channel)],
                    row["white"][("red", "green", "blue").index(channel)],
                    row["cliff_slope"],
                )
                generated_bytes = b"".join(struct.pack("<f", value) for value in generated)
                if generated_bytes == captured_bytes:
                    lane_matches.append((row["gain"], channel))
        require(len(lane_matches) == 1, "Bayer LUT does not have one installed-row match")
        matches.append(lane_matches[0])
    require(matches == [(150, "green"), (150, "blue"), (150, "red"), (150, "green")], "LUT lane map")
    source = patch["source_value"]
    candidate = patch["replacement_ax"]
    residual = source - candidate
    x, y = patch["xy"]
    collapse = json.loads((RUN_DIR / "collapse2_worker_unit1_28mm.json").read_text())
    phases = {tuple(item["phase_bits"]) for item in collapse["hits"]}
    require(phases == {(1, 0)}, "28mm hot-pixel phase receipt")
    first, _diagnostic_second = rank_residuals(
        patch["source_window_13x13"], x, y, 1 ^ 0
    )
    require(first[6][6] == residual, "first rank residual")
    require(source - first[6][6] == candidate, "rank candidate replay")
    lane = ((y & 1) << 1) | (x & 1)
    threshold = 4.0 * patch["luts"][lane]["values_1024f"][candidate]
    require(residual > threshold, "accepted candidate does not exceed 4*LUT threshold")
    center = patch["ring_windows"]["r13"]["u16_x_minus8_plus8"][8]
    require(center == (candidate | 0x8000), "candidate marker receipt")

    events = decisions["decisions"]
    require(len(events) == 96, "decision sample count")
    accepted = rejected = 0
    branches = set()
    for event in events:
        actual = bool(event["accept_al"])
        expected = isolation_decision(event)
        require(actual == expected, "isolation decision mismatch")
        branches.add(event["x_parity"] == event["phase_selector"])
        accepted += int(actual)
        rejected += int(not actual)
    require(branches == {False, True}, "missing phase branch")
    require(accepted and rejected, "missing accepted/rejected decisions")
    return accepted, rejected, residual, matches[0][0], "/".join(item[1] for item in matches)


def main() -> None:
    verify_static()
    accepted, rejected, residual, gain_row, lanes = verify_runtime()
    print(
        "guidance_hot_pixel_formula=OK "
        f"libcp={LIBCP_SHA256} rank6_trials=10000 decisions={accepted + rejected} "
        f"accepted={accepted} rejected={rejected} accepted_residual={residual} "
        f"rank_residual={residual} "
        f"lut_gain_row={gain_row} lut_lanes={lanes} lut_bits=4096/4096"
    )


if __name__ == "__main__":
    main()
