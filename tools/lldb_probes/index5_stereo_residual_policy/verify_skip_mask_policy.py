#!/usr/bin/env python3
"""Verify the selected index-5 Skip-mask policy and reproduce its full bytes."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/lldb_probes/index5_public_field_names"))

from verify_index5_public_field_names import (  # noqa: E402
    LIBCP,
    LIBCP_SHA256,
    bytes_at,
    direct_call_target,
    instruction,
    segments,
)


WIDTH = 2080
HEIGHT = 1560
STEP = 2
SEED = 5489
MASK_SHA256 = "1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def range_hash(data: bytes, mapping, start: int, end: int) -> str:
    return hashlib.sha256(bytes_at(data, mapping, start, end - start)).hexdigest()


def verify_static() -> None:
    data = LIBCP.read_bytes()
    mapping = segments(data)
    require(hashlib.sha256(data).hexdigest() == LIBCP_SHA256, "libcp digest changed")

    hashes = {
        (0x26DB40, 0x26DCB7): "d6f171c9d041a71dcdf1f8cc3d1e7d918f67ba3114c71e5064ab15806ed8229a",
        (0x26FB70, 0x26FBF5): "e7286270c0ec491ec80742f1d18a111ccfa931902751a9633ab572806febb9dd",
        (0x28FBA0, 0x28FCD0): "4966fb95bc9ddab96332d7c479d88c5640dd758c213124cfebea57981fe348b7",
        (0x28FED0, 0x29002A): "a6cd2641356df3ab99855bff2ce12c3ac46ef1f193d48ae00a3decabe5bd927b",
        (0x21CA90, 0x21CC18): "4c3f6a4c92fb0444ebb7d13662f66a7d0e27b6a99af95f60b7bfe39569f58aea",
    }
    for (start, end), expected in hashes.items():
        require(
            range_hash(data, mapping, start, end) == expected,
            f"installed body 0x{start:x}..0x{end:x} changed",
        )

    jump_offsets = struct.unpack("<4i", bytes_at(data, mapping, 0x26DD24, 16))
    require(jump_offsets == (-154, -433, -405, -377), "sampling-pattern jump table changed")
    require(
        tuple(0x26DD24 + offset for offset in jump_offsets)
        == (0x26DC8A, 0x26DB73, 0x26DB8F, 0x26DBAB),
        "sampling-pattern targets changed",
    )
    require(direct_call_target(instruction(data, mapping, 0x26DBA1)) == 0x28FBA0, "pattern-2 call changed")
    require(bytes_at(data, mapping, 0x26DB96, 5) == bytes.fromhex("ba02000000"), "pattern-2 step changed")
    require(bytes_at(data, mapping, 0x28FBC9, 4) == bytes.fromhex("c6458fff"), "mask fill value changed")
    require(bytes_at(data, mapping, 0x28FBE0, 14) == bytes.fromhex("c7458040000000c7458440000000"), "task tile changed")
    require(bytes_at(data, mapping, 0x28FEE7, 10) == bytes.fromhex("c78510f6ffff71150000"), "MT19937 seed changed")
    require(bytes_at(data, mapping, 0x28FF07, 8) == bytes.fromhex("69c26589076c01c8"), "MT19937 initialization changed")
    require(bytes_at(data, mapping, 0x28FF19, 7) == bytes.fromhex("4881f970020000"), "MT19937 state size changed")
    require(direct_call_target(instruction(data, mapping, 0x28FF99)) == 0x21CA90, "x-offset draw changed")
    require(direct_call_target(instruction(data, mapping, 0x28FFAC)) == 0x21CA90, "y-offset draw changed")
    require(bytes_at(data, mapping, 0x28FFDB, 4) == bytes.fromhex("c6040100"), "zero write changed")


class MT19937:
    """Minimal std::mt19937-compatible 32-bit engine."""

    def __init__(self, seed: int):
        self.state = [seed & 0xFFFFFFFF]
        for index in range(1, 624):
            prior = self.state[index - 1]
            value = 0x6C078965 * (prior ^ (prior >> 30)) + index
            self.state.append(value & 0xFFFFFFFF)
        self.index = 624

    def _twist(self) -> None:
        for index in range(624):
            joined = (self.state[index] & 0x80000000) | (self.state[(index + 1) % 624] & 0x7FFFFFFF)
            value = self.state[(index + 397) % 624] ^ (joined >> 1)
            if joined & 1:
                value ^= 0x9908B0DF
            self.state[index] = value & 0xFFFFFFFF
        self.index = 0

    def draw(self) -> int:
        if self.index >= 624:
            self._twist()
        value = self.state[self.index]
        self.index += 1
        value ^= value >> 11
        value ^= (value << 7) & 0x9D2C5680
        value ^= (value << 15) & 0xEFC60000
        value ^= value >> 18
        return value & 0xFFFFFFFF


def expected_rectangles() -> set[tuple[int, int, int, int]]:
    x_ranges = [(x, x + 64) for x in range(0, 1984, 64)] + [(1984, WIDTH)]
    y_ranges = [(y, y + 64) for y in range(0, 1472, 64)] + [(1472, HEIGHT)]
    return {(x0, y0, x1, y1) for y0, y1 in y_ranges for x0, x1 in x_ranges}


def verify_runtime_receipt() -> None:
    path = ROOT / "runs/stereolayer_depth_writer/depth_writer_28mm.json"
    packet = json.loads(path.read_text())
    require(packet["process"]["exit_status"] == 0, "depth-writer render did not complete")
    require(not packet["errors"], "depth-writer probe errors")
    entries = [sample["object"] for sample in packet["samples"] if sample["site"] == "mask_build_entry_0x26db40"]
    require(len(entries) == 11, f"unexpected mask-builder count: {len(entries)}")
    expected = {
        0: (0, 65, 49, 1),
        1: (0, 130, 98, 2),
        2: (0, 260, 195, 2),
        3: (0, 520, 390, 2),
        4: (2, 1040, 780, 2),
        5: (2, WIDTH, HEIGHT, 2),
    }
    for index, (pattern, width, height, count) in expected.items():
        selected = [entry for entry in entries if entry["index_0x8"] == index]
        require(len(selected) == count, f"index {index}: entry count changed")
        require(
            all(
                entry["sampling_pattern_0x50"] == pattern
                and entry["depth_width_0x2a0"] == width
                and entry["depth_height_0x2a4"] == height
                for entry in selected
            ),
            f"index {index}: runtime pattern/dimensions changed",
        )


def load_task_rectangles() -> set[tuple[int, int, int, int]]:
    path = ROOT / "runs/index5_stereo_residual_policy/skip_mask_tasks_28mm.json"
    packet = json.loads(path.read_text())
    require(packet["terminated_after_capture"], "task capture did not reach its terminal condition")
    require(packet["process"]["exit_status"] == 9, "task capture was not intentionally killed")
    require(not packet["errors"], "task probe errors")
    tasks = packet["worker_tasks"]
    require(len(tasks) == 768, f"unexpected task count: {len(tasks)}")
    require({task["step"] for task in tasks} == {STEP}, "worker step changed")
    require(len({task["destination_descriptor"] for task in tasks}) == 1, "destination descriptor changed")
    rectangles = {tuple(task["rect"]) for task in tasks}
    require(len(rectangles) == len(tasks), "duplicate task rectangles captured")
    require(rectangles == expected_rectangles(), "task rectangle grid changed")
    return rectangles


def reproduce_mask(rectangles: set[tuple[int, int, int, int]]) -> bytes:
    result = bytearray([0xFF]) * (WIDTH * HEIGHT)
    for x0, y0, x1, y1 in rectangles:
        engine = MT19937(SEED)
        for y in range(y0, y1, STEP):
            for x in range(x0, x1, STEP):
                dx = engine.draw() & 1
                dy = engine.draw() & 1
                result[(y + dy) * WIDTH + x + dx] = 0
    return bytes(result)


def verify_four_focal_masks(expected: bytes) -> None:
    digest = hashlib.sha256(expected).hexdigest()
    require(digest == MASK_SHA256, f"reproduced mask digest changed: {digest}")
    require(expected.count(0) == 811200, "zero count changed")
    require(expected.count(0xFF) == 2433600, "0xff count changed")
    run_dir = ROOT / "runs/codex_29a140_source_local_producer"
    for focal in ("28mm", "35mm", "70mm", "150mm"):
        actual = (run_dir / f"source_local_{focal}_full_mask_descriptor.bin").read_bytes()
        require(actual == expected, f"{focal}: full Skip mask differs from clean-room replay")
        print(f"{focal}=OK bytes={len(actual)} sha256={MASK_SHA256}")


def main() -> None:
    verify_static()
    verify_runtime_receipt()
    rectangles = load_task_rectangles()
    expected = reproduce_mask(rectangles)
    verify_four_focal_masks(expected)
    print(
        "index5_skip_mask_policy=OK pattern=2 step=2 tasks=768 "
        "tile=64x64 seed=5489 zeros=811200 nonzero=2433600"
    )


if __name__ == "__main__":
    main()
