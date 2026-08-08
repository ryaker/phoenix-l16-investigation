#!/usr/bin/env python3
"""Verify the installed MonoFusion u16 encoding and FastCollapse pyramid."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np


EXPECTED_LIBCP_SHA256 = (
    "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
)
LUT_OFFSET = 0x5CC080
LUT_ENTRIES = 4096
FACTOR_TABLE_OFFSET = 0x5CBB50
KERNEL2_OFFSET = 0x5CBC30
KERNEL4_OFFSET = 0x5CBC50
LEVEL_DIMS = ((4160, 3120), (2080, 1560), (520, 390), (130, 97), (32, 24))
BODY_HASHES = {
    (0x199140, 0x19918A): "4ff81bdd98374842936f5b700a59524281446fcf37ef5ab8b0891837f1af4543",
    (0x1991D0, 0x1991DA): "c35aafed98719115154e3f41a6900882b6d87a41e240dfffd0622f89f89ad07b",
    (0x1895D0, 0x189CB0): "7ed574bf612846de3b56681c9759ab6b3cb91ec4c40e98f1bf9dc756c6f26722",
}
KERNEL_BITS = {
    2: (0x3C8FB86F, 0x3E04BDBA, 0x3EB46B27, 0x3EB46B27,
        0x3E04BDBA, 0x3C8FB86F, 0x00000000),
    4: (0x3C82EB6D, 0x3D31F03D, 0x3DBC58FC, 0x3E1B4430,
        0x3E475DAE, 0x3E475DAE, 0x3E1B4430, 0x3DBC58FC,
        0x3D31F03D, 0x3C82EB6D, 0x00000000),
}
LUT_SHA256 = "ae826dc2c547e017d9f029f39cdd27901c84a16f1dcfd2fbbdc4de34447e71c1"


def read_exact(path: Path, offset: int, size: int) -> bytes:
    with path.open("rb") as handle:
        handle.seek(offset)
        value = handle.read(size)
    assert len(value) == size, (path, offset, size, len(value))
    return value


def load_u16(path: Path, width: int, height: int) -> np.ndarray:
    value = np.fromfile(path, dtype="<u2")
    assert value.size == width * height, (path, value.size, width * height)
    return value.reshape(height, width)


def verify_capture_custody(stage_dir: Path) -> None:
    report = json.loads((stage_dir / "stages.json").read_text(encoding="ascii"))
    assert not report["errors"] and report["terminated_after_samples"], report
    assert len(report["pyramid_inputs"]) == 1, report["pyramid_inputs"]
    inputs = report["pyramid_inputs"][0]
    for role in ("reference", "source"):
        records = inputs[role]["records"]
        assert len(records) == len(LEVEL_DIMS), (stage_dir, role, len(records))
        for level, (width, height) in enumerate(LEVEL_DIMS):
            record = records[level]
            dump = record["dump"]
            path = stage_dir / f"{role}_level{level}.u16le"
            assert record["size"] == [width, height], (stage_dir, role, level)
            assert dump["read_ok"] and dump["byte_count"] == width * height * 2
            assert Path(dump["path"]).resolve() == path.resolve()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == dump["sha256"]


def collapse(image: np.ndarray, factor: int, kernel: np.ndarray) -> np.ndarray:
    # The installed workers correlate vertically first, then horizontally, at
    # offsets [-radius, +radius]. Coordinates clamp to the image edge and each
    # multiply/add rounds independently to float32 before truncation to u16.
    radius = kernel.size // 2
    # The temporary filtered image carries a shifted rectangle domain. In
    # ordinary zero-based storage this is phase 1 for x2 and phase 2 for x4.
    phase = 1 if factor == 2 else 2
    out_height = image.shape[0] // factor
    out_width = image.shape[1] // factor

    rows = np.pad(image, ((radius, radius), (0, 0)), mode="edge")
    vertical = np.multiply(
        rows[phase:phase + factor * out_height:factor],
        kernel[0],
        dtype=np.float32,
    )
    for tap in range(1, kernel.size):
        term = np.multiply(
            rows[phase + tap:phase + tap + factor * out_height:factor],
            kernel[tap],
            dtype=np.float32,
        )
        np.add(vertical, term, out=vertical)

    columns = np.pad(vertical, ((0, 0), (radius, radius)), mode="edge")
    filtered = np.multiply(
        columns[:, phase:phase + factor * out_width:factor],
        kernel[0],
        dtype=np.float32,
    )
    for tap in range(1, kernel.size):
        term = np.multiply(
            columns[:, phase + tap:phase + tap + factor * out_width:factor],
            kernel[tap],
            dtype=np.float32,
        )
        np.add(filtered, term, out=filtered)
    return np.trunc(filtered).astype("<u2")


def verify_bundle(stage_dir: Path, factors: tuple[int, ...], kernels: dict[int, np.ndarray]) -> None:
    verify_capture_custody(stage_dir)
    for role in ("reference", "source"):
        width, height = LEVEL_DIMS[0]
        current = load_u16(stage_dir / f"{role}_level0.u16le", width, height)
        for level, factor in enumerate(factors, start=1):
            current = collapse(current, factor, kernels[factor])
            width, height = LEVEL_DIMS[level]
            observed = load_u16(stage_dir / f"{role}_level{level}.u16le", width, height)
            equal = current == observed
            if not np.all(equal):
                bad = np.argwhere(~equal)
                examples = [
                    {
                        "xy": [int(x), int(y)],
                        "replay": int(current[y, x]),
                        "observed": int(observed[y, x]),
                    }
                    for y, x in bad[:12]
                ]
                raise AssertionError(
                    f"{stage_dir.name} {role} level {level}: "
                    f"{int(equal.sum())}/{equal.size} exact; {examples}"
                )
            print(
                stage_dir.name,
                role,
                f"level{level}",
                f"{equal.size}/{equal.size} u16 samples exact",
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("libcp", type=Path)
    parser.add_argument("stage_dirs", nargs="+", type=Path)
    args = parser.parse_args()

    libcp = args.libcp.read_bytes()
    digest = hashlib.sha256(libcp).hexdigest()
    assert digest == EXPECTED_LIBCP_SHA256, digest
    for (start, end), expected in BODY_HASHES.items():
        assert hashlib.sha256(libcp[start:end]).hexdigest() == expected

    lut = struct.unpack(
        f"<{LUT_ENTRIES}H",
        libcp[LUT_OFFSET : LUT_OFFSET + LUT_ENTRIES * 2],
    )
    assert hashlib.sha256(
        libcp[LUT_OFFSET : LUT_OFFSET + LUT_ENTRIES * 2]
    ).hexdigest() == LUT_SHA256
    generated = tuple(int(math.sqrt(index * 1023.0)) for index in range(LUT_ENTRIES))
    assert lut == generated

    factors = struct.unpack("<4I", read_exact(args.libcp, FACTOR_TABLE_OFFSET, 16))
    assert factors == (2, 4, 4, 4), factors
    kernels = {
        2: np.array(struct.unpack("<7f", read_exact(args.libcp, KERNEL2_OFFSET, 28)), dtype=np.float32),
        4: np.array(struct.unpack("<11f", read_exact(args.libcp, KERNEL4_OFFSET, 44)), dtype=np.float32),
    }
    for factor, expected_bits in KERNEL_BITS.items():
        assert tuple(kernels[factor].view(np.uint32).tolist()) == expected_bits
    print("LUT 4096/4096 exact as trunc(sqrt(index * 1023))")
    print("factors", factors)
    print("factor-2 kernel", kernels[2].tolist())
    print("factor-4 kernel", kernels[4].tolist())

    for stage_dir in args.stage_dirs:
        verify_bundle(stage_dir, factors, kernels)


if __name__ == "__main__":
    main()
