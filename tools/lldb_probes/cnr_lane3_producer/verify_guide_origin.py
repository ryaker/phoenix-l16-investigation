#!/usr/bin/env python3
"""Verify the installed CNR guide LUT and captured one-plane runtime replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path


TABLE_VA = 0x5D2390
TABLE_COUNT = 256
BINARY_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
BODY_HASHES = {
    (0x1BCE50, 0x1BCF90): "7ff46cde57c13901e7775d038bf39b2f54bbe3639dfda6f6904bddb178d9c04a",
    (0x1BCF90, 0x1BD0A0): "110c89bc52190c62af077607c322f791b10df2e757def0e3a2dcf71c0ada6a82",
    (0x1BD0A0, 0x1BD1E0): "a1a0f1e030df6d094d3ea0ad29dedafe2658f438a4e1f2f1386df2c4bc90e95a",
    (0x4064C0, 0x406970): "ec7375cd88b1242a64ec08c5e188e7c686bacd5c7c394f346a15bbc27ebecfbf",
    (0x406A10, 0x407650): "574f76af20a102c22dda604c157eb08cae986bf095298e42e52b09a5c702de96",
    (0x308F50, 0x309270): "0fdc42e8c541ec6c7777ab8abd2817ba660b63ea9529ba607ef707a87c670541",
}
RTTI_ADDRESS_POINTS = {
    0x6600C0: "N2lt16FusionCacheBayerE",
    0x66B240: "NSt3__120__shared_ptr_emplaceIN2lt9TileCacheIfEENS_9allocatorIS3_EEEE",
    0x66B298: "NSt3__120__shared_ptr_emplaceIN2lt9TileCacheIhEENS_9allocatorIS3_EEEE",
    0x660188: (
        "NSt3__110__function6__funcIZN2lt16FusionCacheBayerC1ERKNS_10shared_ptr"
        "INS2_15RawImageFactoryEEERKNS2_21RendererProfileConfigEE3$_1NS_9allocator"
        "ISC_EEFvRKNS4_INS2_4TileIhEEEEEEE"
    ),
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> bytes:
    return struct.pack("<f", value)


def u64(blob: bytes, address: int) -> int:
    return struct.unpack_from("<Q", blob, address)[0]


def cstring(blob: bytes, address: int) -> str:
    return blob[address : blob.index(b"\0", address)].decode("utf-8")


def verify_installed_identity(blob: bytes) -> None:
    actual_binary_sha = hashlib.sha256(blob).hexdigest()
    if actual_binary_sha != BINARY_SHA256:
        raise AssertionError(f"installed binary SHA changed: {actual_binary_sha}")
    for (start, end), expected_sha in BODY_HASHES.items():
        actual_sha = hashlib.sha256(blob[start:end]).hexdigest()
        if actual_sha != expected_sha:
            raise AssertionError(
                f"body 0x{start:x}..0x{end:x} changed: {actual_sha}"
            )
    for address_point, expected_name in RTTI_ADDRESS_POINTS.items():
        typeinfo = u64(blob, address_point - 8)
        actual_name = cstring(blob, u64(blob, typeinfo + 8))
        if actual_name != expected_name:
            raise AssertionError(
                f"RTTI 0x{address_point:x} changed: {actual_name!r}"
            )


def expected_table() -> bytes:
    values = [0.0]
    values.extend(f32(math.sqrt((index + 1) / 256.0)) for index in range(1, 256))
    return b"".join(f32_bits(value) for value in values)


def verify_runtime(report: dict, table: list[float]) -> tuple[int, int, list[str]]:
    checked = 0
    skipped = 0
    errors: list[str] = []
    finals = report.get("final_events", [])
    for event_index, event in enumerate(report.get("helper_events", []), start=1):
        if event.get("name") != "one_plane":
            continue
        dst = event["dst"]
        src = event["src1"]
        scalar = event["scalar_xmm0"]["f32"][0]
        match = next(
            (
                item["guide_r9"]
                for item in finals
                if item["guide_r9"]["data_ptr"] >= dst["data_ptr"]
                and item["guide_r9"]["data_ptr"]
                < dst["data_ptr"] + dst["height"] * dst["stride"] * 4
            ),
            None,
        )
        if match is None:
            skipped += 1
            continue
        float_offset = (match["data_ptr"] - dst["data_ptr"]) // 4
        row_offset, col_offset = divmod(float_offset, dst["stride"])
        source_row = src.get("row0_u8", [])
        output_row = match.get("row0_f32", [])
        if row_offset != 0 or col_offset >= len(source_row):
            skipped += 1
            continue
        count = min(len(output_row), len(source_row) - col_offset)
        for i in range(count):
            source_byte = source_row[col_offset + i]
            predicted = f32(table[source_byte] * scalar)
            observed = output_row[i]
            checked += 1
            if f32_bits(predicted) != f32_bits(observed):
                errors.append(
                    f"event {event_index} sample {i}: byte={source_byte} "
                    f"pred={predicted.hex()} got={observed.hex()}"
                )
    return checked, skipped, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path(
            "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("runs/cnr_lane3_producer/unit1_70mm_guide_origin.json"),
    )
    args = parser.parse_args()

    blob = args.binary.read_bytes()
    verify_installed_identity(blob)
    installed = blob[TABLE_VA : TABLE_VA + TABLE_COUNT * 4]
    generated = expected_table()
    if installed != generated:
        mismatch = next(i for i, (a, b) in enumerate(zip(installed, generated)) if a != b)
        raise AssertionError(f"installed LUT differs from generator at byte {mismatch}")
    table = list(struct.unpack("<256f", installed))

    square_mismatches = []
    lane3_values = []
    for index, value in enumerate(table):
        observed = f32(value * value)
        lane3_values.append(observed)
        expected = 0.0 if index == 0 else f32((index + 1) / 256.0)
        if f32_bits(observed) != f32_bits(expected):
            square_mismatches.append(index)
    if not square_mismatches:
        raise AssertionError("expected rounded-sqrt square to differ from rational shortcut")
    lane3_bytes = b"".join(f32_bits(value) for value in lane3_values)

    report = json.loads(args.report.read_text(encoding="utf-8"))
    checked, skipped, errors = verify_runtime(report, table)
    if errors:
        raise AssertionError("runtime replay failed:\n" + "\n".join(errors[:20]))
    if checked == 0:
        raise AssertionError("runtime replay checked zero samples")

    print(f"binary_sha256={BINARY_SHA256}")
    print("source_cache_rtti=lt::TileCache<unsigned char>")
    print("owner_rtti=lt::FusionCacheBayer")
    print(f"lut_sha256={hashlib.sha256(installed).hexdigest()}")
    print("lut_formula=index0:0; index1..255:float32(sqrt((index+1)/256))")
    print(f"lane3_sha256={hashlib.sha256(lane3_bytes).hexdigest()}")
    print("lane3_after_square=float32(lut[index]*lut[index])")
    print(f"rational_shortcut_mismatches={len(square_mismatches)}")
    print(f"runtime_one_plane_samples={checked} skipped_events={skipped}")
    print("result=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
