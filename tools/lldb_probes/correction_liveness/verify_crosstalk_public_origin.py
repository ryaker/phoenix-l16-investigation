#!/usr/bin/env python3
"""Join the selected runtime cross-talk A grid to public LRI calibration bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from lri_field_inspect import parse_proto_fields, scan_lri_blocks  # noqa: E402


LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

STATIC_RANGES = {
    "owner_camera_crosstalk_accessor": (
        0xE7290,
        0xE72F4,
        "6ae396299c8db85d44f2d34f79c2e5630858ee45417ebb98620a61e352ee28cc",
    ),
    "public_crosstalk_decoder": (
        0x135620,
        0x1362BB,
        "d1585d0ab11fd5cc8a878bef219e7cc017f1f4cb55dae7dca0ae4bcde89c1d6d",
    ),
    "matrix4x4_repeated_decoder": (
        0x1362C0,
        0x136384,
        "2979bf6e53b60b3e1458f732004c1d24e0ce2ca62ea2b26c0e18cf294228613d",
    ),
    "selected_scalar_factory": (
        0xFB6A0,
        0xFBD00,
        "68f7970dd651e3a4400e52f1cbb7ec9c59867f4fdb98f6124e6b4f29ba42d229",
    ),
}

DEFAULT_CASES = (
    (
        "unit1_28mm_a1",
        Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        0,
        ROOT / "runs/correction_liveness/formula_unit1_28mm_a1/callback_grid_a_f32.bin",
    ),
    (
        "unit1_28mm_b2",
        Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        6,
        ROOT
        / "runs/correction_liveness/ir_origin_unit1_28mm_b2_direct/public_crosstalk_grid_f32.bin",
    ),
    (
        "unit2_28mm_a1",
        Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
        0,
        ROOT / "runs/correction_liveness/formula_unit2_28mm_a1/callback_grid_a_f32.bin",
    ),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def values(blob: bytes, number: int, wire: int | None = None):
    return [
        value
        for field, wire_type, value in parse_proto_fields(blob)
        if field == number and (wire is None or wire_type == wire)
    ]


def one(blob: bytes, number: int, wire: int | None = None):
    found = values(blob, number, wire)
    require(len(found) == 1, f"field {number}: expected one value, got {len(found)}")
    return found[0]


def f32_word(word: int) -> bytes:
    return struct.pack("<I", word)


def decode_matrix_message(blob: bytes) -> bytes:
    packed = values(blob, 1, 2)
    if len(packed) == 1 and len(packed[0]) == 0x40:
        return packed[0]
    words = values(blob, 1, 5)
    if len(words) == 16:
        return b"".join(f32_word(word) for word in words)
    all_fixed = [
        f32_word(value)
        for _field, wire_type, value in parse_proto_fields(blob)
        if wire_type == 5
    ]
    require(len(all_fixed) == 16, "Matrix4x4F is not sixteen float32 words")
    return b"".join(all_fixed)


def decode_crosstalk(vignetting: bytes) -> tuple[int, int, bytes, str]:
    model = one(vignetting, 1, 2)
    width = int(one(model, 1, 0))
    height = int(one(model, 2, 0))
    packed = values(model, 4, 2)
    repeated = values(model, 3, 2)
    if packed:
        require(len(packed) == 1, "multiple packed crosstalk payloads")
        raw = packed[0]
        encoding = "data_packed"
    else:
        require(repeated, "empty public crosstalk model")
        raw = b"".join(decode_matrix_message(item) for item in repeated)
        encoding = "data"
    require(len(raw) % 0x40 == 0, "crosstalk bytes are not 4x4 matrices")
    require(len(raw) == width * height * 0x40, "crosstalk dimensions mismatch")
    return width, height, raw, encoding


def calibration_blocks(path: Path):
    result = []
    for block in scan_lri_blocks(str(path)):
        modules = values(block["payload"], 13, 2)
        if not modules or not all(values(module, 4, 2) for module in modules):
            continue
        decoded = []
        try:
            for index, module in enumerate(modules):
                camera_id = int(one(module, 1, 0))
                width, height, raw, encoding = decode_crosstalk(one(module, 4, 2))
                decoded.append(
                    {
                        "index": index,
                        "camera_id": camera_id,
                        "width": width,
                        "height": height,
                        "encoding": encoding,
                        "raw": raw,
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
        except AssertionError:
            continue
        result.append(
            {
                "block_index": block["idx"],
                "block_offset": block["block_offset"],
                "payload_size": block["payload_size"],
                "modules": decoded,
            }
        )
    return result


def verify_static() -> dict:
    image = LIBCP.read_bytes()
    require(hashlib.sha256(image).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    hashes = {}
    for name, (start, end, expected) in STATIC_RANGES.items():
        digest = hashlib.sha256(image[start:end]).hexdigest()
        if expected is not None:
            require(digest == expected, f"{name} body hash drift")
        hashes[name] = digest

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder = list(md.disasm(image[0x135620:0x1362BB], 0x135620))
    text = [(ins.address, ins.mnemonic, ins.op_str) for ins in decoder]
    required = {
        (0x1356BB, "shl", "r12, 6"),
        (0x13575B, "mov", "rcx, qword ptr [r14 + 0x38]"),
        (0x1357DA, "call", "0x1362c0"),
        (0x13596E, "shl", "r12, 6"),
        (0x1359CB, "call", "0x137c50"),
        (0x1359EC, "movaps", "xmmword ptr [r13 + rbx + 0x30], xmm3"),
    }
    missing = required - set(text)
    require(not missing, f"public decoder instruction drift: {sorted(missing)}")
    return hashes


def verify_case(label: str, lri: Path, camera_key: int, runtime_path: Path) -> dict:
    require(lri.exists(), f"missing LRI: {lri}")
    require(runtime_path.exists(), f"missing runtime grid: {runtime_path}")
    runtime = runtime_path.read_bytes()
    require(len(runtime) == 17 * 13 * 0x40, f"{label}: runtime grid size")
    runtime_sha = hashlib.sha256(runtime).hexdigest()
    blocks = calibration_blocks(lri)
    require(blocks, f"{label}: no calibration blocks")

    all_matches = []
    camera_id_matches = []
    for block in blocks:
        for module in block["modules"]:
            if module["raw"] == runtime:
                receipt = {
                    "block_index": block["block_index"],
                    "block_offset": block["block_offset"],
                    "module_index": module["index"],
                    "camera_id": module["camera_id"],
                    "encoding": module["encoding"],
                }
                all_matches.append(receipt)
                if module["camera_id"] == camera_key:
                    camera_id_matches.append(receipt)
    require(all_matches, f"{label}: runtime grid has no public byte match")
    require(
        camera_id_matches,
        f"{label}: runtime camera key {camera_key} has no same-ID public match",
    )
    require(len(camera_id_matches) == 1, f"{label}: ambiguous camera-ID public match")
    match = camera_id_matches[0]
    return {
        "label": label,
        "lri": str(lri),
        "camera_key": camera_key,
        "runtime_sha256": runtime_sha,
        "calibration_block_count": len(blocks),
        "calibration_blocks": [
            {
                "block_index": item["block_index"],
                "block_offset": item["block_offset"],
                "payload_size": item["payload_size"],
                "module_count": len(item["modules"]),
            }
            for item in blocks
        ],
        "all_public_matches": all_matches,
        "selected_public_match": match,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    static_hashes = verify_static()
    cases = [verify_case(*case) for case in DEFAULT_CASES]
    output = {
        "status": "PASS",
        "libcp_sha256": LIBCP_SHA256,
        "static_hashes": static_hashes,
        "cases": cases,
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(f"crosstalk_public_static=OK bodies={len(static_hashes)}")
        for case in cases:
            match = case["selected_public_match"]
            print(
                "crosstalk_public=OK "
                f"label={case['label']} key={case['camera_key']} "
                f"block={match['block_index']} camera_id={match['camera_id']} "
                f"encoding={match['encoding']} sha256={case['runtime_sha256']}"
            )


if __name__ == "__main__":
    main()
