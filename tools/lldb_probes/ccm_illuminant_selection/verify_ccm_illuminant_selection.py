#!/usr/bin/env python3
"""Verify public CCM illuminants and the live four-focal selection rule."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/ccm_illuminant_selection"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
SCHEMA_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
LRIS = {
    "28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "35mm": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
    "70mm": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
    "150mm": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
}
PUBLIC_ENUM = {
    0: "A",
    1: "D50",
    2: "D65",
    3: "D75",
    4: "F2",
    5: "F7",
    6: "F11",
    7: "TL84",
    99: "UNKNOWN",
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


STATIC = load_module("ccm_static_helpers", STATIC_PATH)
SCHEMA = load_module("ccm_schema_helpers", SCHEMA_PATH)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def values(fields, number: int):
    return [(wire, value) for field, wire, value in fields if field == number]


def scan_blocks(path: Path) -> list[bytes]:
    data = path.read_bytes()
    blocks = []
    offset = 0
    while offset + 32 <= len(data) and data[offset : offset + 4] == b"LELR":
        total = struct.unpack_from("<Q", data, offset + 4)[0]
        message_offset = struct.unpack_from("<Q", data, offset + 12)[0]
        message_size = struct.unpack_from("<I", data, offset + 20)[0]
        require(total > 0, f"{path}: zero block size")
        blocks.append(
            data[
                offset + message_offset : offset + message_offset + message_size
            ]
        )
        offset += total
    return blocks


def matrix_bytes(message: bytes) -> bytes:
    fields, consumed = SCHEMA.parse_fields(message)
    require(consumed == len(message), "matrix message parse")
    words = [value for _field, wire, value in fields if wire == 5]
    require(len(words) == 9, f"matrix word count {len(words)}")
    return b"".join(words)


def public_color_records(path: Path) -> dict[tuple[int, int], dict[str, bytes]]:
    candidates = []
    for block in scan_blocks(path):
        fields, _consumed = SCHEMA.parse_fields(block)
        records = values(fields, 13)
        if len(records) == 42 and all(wire == 2 for wire, _value in records):
            candidates.append(records)
    require(len(candidates) == 1, f"{path}: ColorCalibration block candidates")

    result = {}
    counts = {}
    for _wire, raw_record in candidates[0]:
        record_fields, consumed = SCHEMA.parse_fields(raw_record)
        require(consumed == len(raw_record), f"{path}: record parse")
        camera = values(record_fields, 1)[0][1]
        inner_raw = values(record_fields, 2)[0][1]
        inner, inner_consumed = SCHEMA.parse_fields(inner_raw)
        require(inner_consumed == len(inner_raw), f"{path}: inner parse")
        illuminant_type = values(inner, 1)[0][1]
        forward = values(inner, 2)[0][1]
        color = values(inner, 3)[0][1]
        result[(camera, illuminant_type)] = {
            "forward_matrix": matrix_bytes(forward),
            "color_matrix": matrix_bytes(color),
        }
        counts[illuminant_type] = counts.get(illuminant_type, 0) + 1
    require(counts == {0: 14, 2: 14, 6: 14}, f"{path}: type counts {counts}")
    require(all((camera, 1) not in result for camera in range(16)), f"{path}: D50 stored")
    return result


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    start = SCHEMA.locate_descriptor(data, "color_calibration.proto")
    descriptor = SCHEMA.decode_file_descriptor(data, start)
    require(
        descriptor["serialized_sha256"]
        == "986015aea1758f57c5fa36e2d29d68eafe81fc5b563a6c28fedae1a18f5f937d",
        "ColorCalibration descriptor changed",
    )
    enum = next(
        item
        for item in descriptor["enums"]
        if item["full_name"] == ".ltpb.ColorCalibration.IlluminantType"
    )
    require(
        {item["number"]: item["name"] for item in enum["values"]} == PUBLIC_ENUM,
        f"IlluminantType changed: {enum}",
    )

    hashes = {
        (0x3504E0, 0x350519): "c04716159e895645dcc71bf40e1bbfe740004050964a6e0a3050528f414eca8a",
        (0x350BC0, 0x350CFB): "f5356e1ebfe27549f6d4581603c6ed83d6261ecb2792d82bdb9c71a5e7ddd77e",
        (0xAB720, 0xAB82E): "f6f81e72713db355dbfe99c9a65fde7d85cc4466ab20ee1facc7b13f2fed6a3b",
        (0xAB2E0, 0xAB4B9): "9f95348485530cdae16845d76713a10d6b2ea7264ffb70666edf04643354ef43",
        (0xAB4C0, 0xAB59F): "59820709e6b070d07cd0fa0c9755909c749e161c6b5804a255efe3d423d51239",
    }
    for (begin, end), expected in hashes.items():
        actual = hashlib.sha256(
            STATIC.bytes_at(data, mapping, begin, end - begin)
        ).hexdigest()
        require(actual == expected, f"static range 0x{begin:x}..0x{end:x} changed")
    print(
        f"static_ccm_illuminant_selection=OK libcp={digest} "
        "public=0:A,1:D50,2:D65,6:F11 live_internal_pair=2:A,7:D65"
    )
    return digest


def predicted_matrix(sample: dict) -> bytes:
    matrix_a = struct.unpack("<9f", bytes.fromhex(sample["matrix_1"]["hex"]))
    matrix_d65 = struct.unpack("<9f", bytes.fromhex(sample["matrix_2"]["hex"]))
    target = sample["target_cct"]
    cct_a = sample["calibration_cct_1"]
    cct_d65 = sample["calibration_cct_2"]
    target_mired = f32(f32(1.0) / target)
    a_mired = f32(f32(1.0) / cct_a)
    d65_mired = f32(f32(1.0) / cct_d65)
    clamped = f32(min(max(target_mired, d65_mired), a_mired))
    alpha = f32(f32(clamped - d65_mired) / f32(a_mired - d65_mired))
    output = [
        f32(d65 + f32(alpha * f32(a - d65)))
        for a, d65 in zip(matrix_a, matrix_d65)
    ]
    return struct.pack("<9f", *output)


def verify_tier(tier: str) -> None:
    report = json.loads((RUN_ROOT / f"{tier}.json").read_text())
    require(report["process_exit_status"] == 0, f"{tier}: process exit")
    require(not report["errors"], f"{tier}: errors {report['errors']}")
    samples = report["samples"]
    require(samples, f"{tier}: no samples")
    records = public_color_records(LRIS[tier])
    matched_cameras = set()
    for index, sample in enumerate(samples):
        require(
            (sample["illuminant_1"], sample["illuminant_2"]) == (2, 7),
            f"{tier}: internal illuminant pair at sample {index}",
        )
        matrix_a = bytes.fromhex(sample["matrix_1"]["hex"])
        matrix_d65 = bytes.fromhex(sample["matrix_2"]["hex"])
        matches = [
            camera
            for camera in range(16)
            if records.get((camera, 0), {}).get("color_matrix") == matrix_a
            and records.get((camera, 2), {}).get("color_matrix") == matrix_d65
        ]
        require(len(matches) == 1, f"{tier}: public matrix pair at sample {index}")
        camera = matches[0]
        matched_cameras.add(camera)
        require(
            records[(camera, 6)]["color_matrix"] not in (matrix_a, matrix_d65),
            f"{tier}: F11 unexpectedly selected at sample {index}",
        )
        if "target_cct" in sample:
            require(
                sample["calibration_cct_1"] == 2855.63232421875,
                f"{tier}: A CCT",
            )
            require(
                sample["calibration_cct_2"] == 6502.08203125,
                f"{tier}: D65 CCT",
            )
            require(
                predicted_matrix(sample)
                == bytes.fromhex(sample["interpolated_matrix"]["hex"]),
                f"{tier}: exact mired interpolation at sample {index}",
            )
    print(
        f"{tier}: OK samples={len(samples)} cameras={','.join(map(str, sorted(matched_cameras)))} "
        "public_pair=A,D65 stored_unselected=F11"
    )


def main() -> None:
    verify_static()
    for tier in LRIS:
        verify_tier(tier)
    print("ccm_illuminant_selection=OK")


if __name__ == "__main__":
    main()
