#!/usr/bin/env python3
"""Verify public raw-surface layout and installed RAW10 unpack arithmetic."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
SCHEMA_TOOL = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
sys.path.insert(0, str(ROOT / "tools"))

import lri_field_inspect as lri  # noqa: E402


UNIT1_SIG = "722a6e721636c9c4"
UNIT2_SIG = "223961c6bce6153e"
WIDTH = 4160
HEIGHT = 3120
ROW_STRIDE = 5200
IMAGE_BYTES = ROW_STRIDE * HEIGHT
SLOT_BYTES = 0xF7A000
SLOT_GAP = SLOT_BYTES - IMAGE_BYTES

WIDE_PARTITIONS = [[0, 4, 6, 8, 9], [1, 2, 3, 5, 7]]
TELE_PARTITIONS = [[6, 8, 9, 14], [5, 7, 11], [10, 12, 13, 15]]

SEEDS = (
    ("Unit-1", "28mm", "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri", 28, UNIT1_SIG, WIDE_PARTITIONS),
    ("Unit-1", "35mm", "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri", 35, UNIT1_SIG, WIDE_PARTITIONS),
    ("Unit-1", "70mm", "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri", 70, UNIT1_SIG, TELE_PARTITIONS),
    ("Unit-1", "150mm", "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri", 149, UNIT1_SIG, TELE_PARTITIONS),
    ("Unit-2", "28mm", "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri", 28, UNIT2_SIG, WIDE_PARTITIONS),
    ("Unit-2", "35mm", "/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri", 35, UNIT2_SIG, WIDE_PARTITIONS),
    ("Unit-2", "70mm", "/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri", 70, UNIT2_SIG, TELE_PARTITIONS),
    ("Unit-2", "150mm", "/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri", 149, UNIT2_SIG, TELE_PARTITIONS),
)

CAMERA_NAMES = {
    **{index: f"A{index + 1}" for index in range(5)},
    **{index: f"B{index - 4}" for index in range(5, 10)},
    **{index: f"C{index - 9}" for index in range(10, 16)},
}
PHASE_BY_RED = {
    (0, 0): "RGGB",
    (1, 0): "GRBG",
    (0, 1): "GBRG",
    (1, 1): "BGGR",
    (-1, -1): "MONO",
}

BODY_HASHES = {
    (0xF4D90, 0xF53C1): "5ecf39316b3efdeb5a2b795f8b6b94a8a46d25eca2860114895ddb6f62eb629e",
    (0xF6CF0, 0xF72A1): "36dfeb7980bc88c21ff0ce4141e86f2828826a960af51bf45b270c0cd7d1df8c",
    (0xF7B10, 0xF7C3A): "ea66e4af68cad2d792ce99e661592a1afa7a537a73ca2211f95dd24b46bb10cf",
    (0xF7C40, 0xF7D29): "eb71578ba62ac530d249be8badb88bafa1c4158d757c29129613a9e91919ff33",
    (0xF7D30, 0xF7EA8): "77aeaab90c1a869d65fd37344af4c43aa1dd82cfed58221e40d75e372dc2fdf0",
    (0xF7EB0, 0xF7FCB): "1df4a55308e19a6b1227f76d58cc3b36e60c51298cd1096a7b0fe1ff37d7df22",
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


SCHEMA = load_module("raw_layout_schema", SCHEMA_TOOL)


def fields(data: bytes) -> dict[int, list[tuple[int, object]]]:
    result: dict[int, list[tuple[int, object]]] = {}
    for number, wire_type, value in lri.parse_proto_fields(data):
        result.setdefault(number, []).append((wire_type, value))
    return result


def one(message: bytes, number: int, wire_type: int, default=None):
    values = fields(message).get(number, [])
    if not values:
        return default
    require(len(values) == 1 and values[0][0] == wire_type, f"field {number} shape {values}")
    return values[0][1]


def signed_int32(value: int) -> int:
    return struct.unpack("<i", struct.pack("<I", value & 0xFFFFFFFF))[0]


def point2i(message: bytes) -> tuple[int, int]:
    return (
        signed_int32(one(message, 1, 0)),
        signed_int32(one(message, 2, 0)),
    )


def decode_surface(module: bytes) -> dict:
    surface = one(module, 9, 2)
    require(isinstance(surface, bytes), "missing sensor_data_surface")
    size = one(surface, 2, 2)
    red = one(module, 13, 2)
    require(isinstance(size, bytes) and isinstance(red, bytes), "missing size/red override")
    red_xy = point2i(red)
    require(red_xy in PHASE_BY_RED, f"unexpected red coordinate {red_xy}")
    return {
        "camera_id": one(module, 2, 0),
        "camera_name": CAMERA_NAMES[one(module, 2, 0)],
        "width": one(size, 1, 0),
        "height": one(size, 2, 0),
        "format": one(surface, 3, 0),
        "row_stride": one(surface, 4, 0),
        "data_offset": one(surface, 5, 0),
        "red_coordinate": list(red_xy),
        "bayer_phase": PHASE_BY_RED[red_xy],
        "horizontal_flip": bool(one(module, 11, 0, 0)),
        "vertical_flip": bool(one(module, 12, 0, 0)),
    }


def intrinsics_signature(blocks: list[dict]) -> str:
    candidates = [
        block for block in blocks
        if 32000 <= block["payload_size"] <= 34000
    ]
    require(len(candidates) == 1, f"intrinsics candidates {len(candidates)}")
    return hashlib.sha256(candidates[0]["payload"]).hexdigest()[:16]


def verify_seed(seed: tuple) -> dict:
    body, tier, raw_path, focal, unit_sig, expected_partitions = seed
    path = Path(raw_path)
    require(path.is_file(), f"missing {path}")
    blocks = lri.scan_lri_blocks(str(path))
    require(len(blocks) == (11 if len(expected_partitions) == 2 else 12), f"{tier}: block count")
    require(intrinsics_signature(blocks) == unit_sig, f"{tier}: unit signature")

    raw_rows = []
    observed_partitions = []
    phase_rows = []
    with path.open("rb") as handle:
        for block in blocks:
            modules = [
                value for wire_type, value in fields(block["payload"]).get(12, [])
                if wire_type == 2
            ]
            if not modules:
                continue
            surfaces = [decode_surface(module) for module in modules]
            require(block["msg_type"] == 0, f"{tier} block {block['idx']}: raw msg type")
            require(block["msg_offset"] == len(surfaces) * SLOT_BYTES, f"{tier}: msg offset")
            observed_partitions.append([row["camera_id"] for row in surfaces])
            for slot, row in enumerate(surfaces):
                require((row["width"], row["height"]) == (WIDTH, HEIGHT), f"{tier}: dimensions")
                require(row["format"] == 7, f"{tier}: format {row['format']}")
                require(row["row_stride"] == ROW_STRIDE, f"{tier}: row stride")
                require(row["data_offset"] == 32 + slot * SLOT_BYTES, f"{tier}: data offset")
                require(not row["horizontal_flip"] and not row["vertical_flip"], f"{tier}: flip")
                require(row["data_offset"] + IMAGE_BYTES <= block["msg_offset"], f"{tier}: raw span")
                handle.seek(block["block_offset"] + row["data_offset"])
                first_ten = handle.read(10)
                require(len(first_ten) == 10, f"{tier}: raw sample")
                row["block_index"] = block["idx"]
                row["slot"] = slot
                row["first_10_bytes"] = first_ten.hex()
                row["first_8_pixels"] = unpack10(first_ten)
                raw_rows.append(row)
                phase_rows.append((row["camera_id"], row["bayer_phase"]))

    require(observed_partitions == expected_partitions, f"{tier}: partitions {observed_partitions}")
    require(len(raw_rows) == (10 if len(expected_partitions) == 2 else 11), f"{tier}: raw count")
    return {
        "body": body,
        "tier": tier,
        "path": str(path),
        "focal": focal,
        "unit_signature": unit_sig,
        "block_inventory": [
            {
                "index": block["idx"],
                "msg_type": block["msg_type"],
                "total_size": block["total_size"],
                "message_offset": block["msg_offset"],
                "message_size": block["payload_size"],
                "tail_size": block["total_size"] - block["msg_offset"] - block["payload_size"],
            }
            for block in blocks
        ],
        "raw_partitions": observed_partitions,
        "raw_surfaces": raw_rows,
        "phase_rows": phase_rows,
    }


def unpack10(raw: bytes) -> list[int]:
    require(len(raw) == 10, "RAW10 group must contain 10 bytes")
    packed = int.from_bytes(raw, "little")
    return [(packed >> (10 * index)) & 0x3FF for index in range(8)]


def explicit_unpack10(raw: bytes) -> list[int]:
    b = raw
    return [
        b[0] | ((b[1] & 0x03) << 8),
        (b[1] >> 2) | ((b[2] & 0x0F) << 6),
        (b[2] >> 4) | ((b[3] & 0x3F) << 4),
        (b[3] >> 6) | (b[4] << 2),
        b[5] | ((b[6] & 0x03) << 8),
        (b[6] >> 2) | ((b[7] & 0x0F) << 6),
        (b[7] >> 4) | ((b[8] & 0x3F) << 4),
        (b[8] >> 6) | (b[9] << 2),
    ]


def disassemble(data: bytes, start: int, end: int) -> dict[int, tuple[str, str]]:
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in decoder.disasm(data[start:end], start)
    }


def require_instructions(
    instructions: dict[int, tuple[str, str]], expected: dict[int, tuple[str, str]]
) -> None:
    for address, instruction in expected.items():
        require(
            instructions.get(address) == instruction,
            f"instruction 0x{address:x}: {instructions.get(address)} != {instruction}",
        )


def verify_installed() -> dict:
    data = LIBCP.read_bytes()
    require(
        hashlib.sha256(data).hexdigest()
        == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        "libcp SHA-256 drift",
    )
    for (start, end), expected in BODY_HASHES.items():
        actual = hashlib.sha256(data[start:end]).hexdigest()
        require(actual == expected, f"body 0x{start:x}..0x{end:x} drift")

    packed_path = disassemble(data, 0xF4D90, 0xF53C1)
    require(
        [address for address, instruction in packed_path.items() if instruction == ("call", "0xf6cf0")]
        == [0xF52C3, 0xF5309],
        "packed path to unpack dispatcher edges",
    )
    dispatch = disassemble(data, 0xF6CF0, 0xF72A1)
    dispatch_targets = {
        int(operand, 16)
        for mnemonic, operand in dispatch.values()
        if mnemonic == "call" and operand.startswith("0xf7")
    }
    require(
        dispatch_targets == {0xF7B10, 0xF7C40, 0xF7D30, 0xF7EB0},
        f"unpack dispatch targets {dispatch_targets}",
    )

    # Forward row worker: one complete 10-byte -> eight uint16 group.
    forward = disassemble(data, 0xF7C40, 0xF7D29)
    require_instructions(
        forward,
        {
            0xF7C60: ("movzx", "eax, byte ptr [rsi - 8]"),
            0xF7C64: ("movzx", "r9d, byte ptr [rsi - 9]"),
            0xF7C6B: ("and", "edx, 3"),
            0xF7C6E: ("shl", "edx, 8"),
            0xF7C71: ("or", "edx, r9d"),
            0xF7C74: ("movzx", "ecx, byte ptr [rsi - 7]"),
            0xF7C78: ("shr", "eax, 2"),
            0xF7C7B: ("and", "ecx, 0xf"),
            0xF7C7E: ("shl", "ecx, 6"),
            0xF7C81: ("or", "ecx, eax"),
            0xF7C83: ("mov", "word ptr [rdi + r10*2], dx"),
            0xF7C88: ("mov", "word ptr [rdi + r10*2 + 2], cx"),
            0xF7C8E: ("movzx", "eax, byte ptr [rsi - 6]"),
            0xF7C92: ("movzx", "ecx, byte ptr [rsi - 7]"),
            0xF7C96: ("shr", "ecx, 4"),
            0xF7C99: ("and", "eax, 0x3f"),
            0xF7C9C: ("shl", "eax, 4"),
            0xF7C9F: ("or", "eax, ecx"),
            0xF7CA1: ("mov", "word ptr [rdi + r10*2 + 4], ax"),
            0xF7CA7: ("movzx", "eax, byte ptr [rsi - 5]"),
            0xF7CAB: ("movzx", "ecx, byte ptr [rsi - 6]"),
            0xF7CAF: ("shr", "ecx, 6"),
            0xF7CB2: ("lea", "eax, [rcx + rax*4]"),
            0xF7CB5: ("mov", "word ptr [rdi + r10*2 + 6], ax"),
            0xF7CBB: ("movzx", "eax, byte ptr [rsi - 3]"),
            0xF7CBF: ("movzx", "ecx, byte ptr [rsi - 4]"),
            0xF7CC3: ("and", "eax, 3"),
            0xF7CC6: ("shl", "eax, 8"),
            0xF7CC9: ("or", "eax, ecx"),
            0xF7CCB: ("mov", "word ptr [rdi + r10*2 + 8], ax"),
            0xF7CD1: ("movzx", "eax, byte ptr [rsi - 2]"),
            0xF7CD5: ("movzx", "ecx, byte ptr [rsi - 3]"),
            0xF7CD9: ("shr", "ecx, 2"),
            0xF7CDC: ("and", "eax, 0xf"),
            0xF7CDF: ("shl", "eax, 6"),
            0xF7CE2: ("or", "eax, ecx"),
            0xF7CE4: ("mov", "word ptr [rdi + r10*2 + 0xa], ax"),
            0xF7CEA: ("movzx", "eax, byte ptr [rsi - 1]"),
            0xF7CEE: ("movzx", "ecx, byte ptr [rsi - 2]"),
            0xF7CF2: ("shr", "ecx, 4"),
            0xF7CF5: ("and", "eax, 0x3f"),
            0xF7CF8: ("shl", "eax, 4"),
            0xF7CFB: ("or", "eax, ecx"),
            0xF7CFD: ("mov", "word ptr [rdi + r10*2 + 0xc], ax"),
            0xF7D03: ("movzx", "eax, byte ptr [rsi]"),
            0xF7D06: ("movzx", "ecx, byte ptr [rsi - 1]"),
            0xF7D0A: ("shr", "ecx, 6"),
            0xF7D0D: ("lea", "eax, [rcx + rax*4]"),
            0xF7D10: ("mov", "word ptr [rdi + r10*2 + 0xe], ax"),
            0xF7D16: ("add", "r10, 8"),
            0xF7D1A: ("add", "rsi, 0xa"),
        },
    )

    descriptor = SCHEMA.decode_file_descriptor(
        data, SCHEMA.locate_descriptor(data, "camera_module.proto")
    )
    format_enum = next(
        enum for enum in descriptor["enums"]
        if enum["full_name"] == ".ltpb.CameraModule.Surface.FormatType"
    )
    values = {row["number"]: row["name"] for row in format_enum["values"]}
    require(values[7] == "RAW_PACKED_10BPP", f"format 7 is {values[7]}")

    probes = (
        bytes(range(10)),
        bytes.fromhex("ffffffffffffffffffff"),
        bytes.fromhex("0055aa33cc0ff05aa596"),
    )
    for raw in probes:
        require(unpack10(raw) == explicit_unpack10(raw), f"unpack mismatch {raw.hex()}")
    return {
        "libcp_sha256": hashlib.sha256(data).hexdigest(),
        "camera_module_descriptor_sha256": descriptor["serialized_sha256"],
        "format_7": values[7],
        "body_hashes": {
            f"0x{start:x}..0x{end:x}": digest
            for (start, end), digest in BODY_HASHES.items()
        },
        "formula": "pixel[i] = (little_endian_80bit_group >> (10*i)) & 0x3ff",
    }


def verify_runtime_reports() -> list[dict]:
    report_dir = ROOT / "runs/raw_sensor_layout"
    reports = []
    for path in sorted(report_dir.glob("runtime_*.json")):
        report = json.loads(path.read_text())
        expected = report["expected_planes"]
        require(not report["errors"], f"{path}: {report['errors']}")
        require(report["packed_handler_calls"] == expected, f"{path}: packed count")
        for event in report["packed_events"]:
            require(event["requested_size"] == [WIDTH, HEIGHT], f"{path}: dimensions")
            require(event["row_stride"] == ROW_STRIDE, f"{path}: row stride")
        reports.append(report)
    return reports


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--require-runtime", action="store_true")
    args = parser.parse_args()

    installed = verify_installed()
    seeds = [verify_seed(seed) for seed in SEEDS]

    phase_sets: dict[int, set[str]] = {}
    for seed in seeds:
        for camera_id, phase in seed["phase_rows"]:
            phase_sets.setdefault(camera_id, set()).add(phase)
    require(all(len(values) == 1 for values in phase_sets.values()), f"phase drift {phase_sets}")

    runtime = verify_runtime_reports()
    if args.require_runtime:
        require(runtime, "expected at least one runtime report")

    result = {
        "status": "OK",
        "installed": installed,
        "constants": {
            "width": WIDTH,
            "height": HEIGHT,
            "row_stride": ROW_STRIDE,
            "image_bytes": IMAGE_BYTES,
            "slot_bytes": SLOT_BYTES,
            "slot_gap": SLOT_GAP,
        },
        "camera_phases": {
            CAMERA_NAMES[camera_id]: next(iter(values))
            for camera_id, values in sorted(phase_sets.items())
        },
        "seeds": seeds,
        "runtime_reports": runtime,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        "PASS raw sensor layout "
        f"lris={len(seeds)} raw_surfaces={sum(len(seed['raw_surfaces']) for seed in seeds)} "
        f"format={installed['format_7']} runtime_reports={len(runtime)}"
    )


if __name__ == "__main__":
    main()
