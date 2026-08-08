#!/usr/bin/env python3
"""Verify canonical float32 RGB to legacy-flat Radiance RGBE output."""

import hashlib
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/"
    "Frameworks/libcp.dylib"
)
EXPECTED_LIBCP_SHA256 = (
    "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
)
HEADER = b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n"
COMPLETE_HDR = (
    ROOT
    / "runs/reference_validation/self_repeats/unit1_28mm/repeat_10.hdr"
)
RUNTIME = ROOT / "runs/output_rgbe_writer/unit1_28mm.json"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def encode_pixel(red, green, blue):
    maximum = max(red, green, blue)
    if not math.isfinite(maximum) or maximum <= 0.0:
        return bytes((0, 0, 0, 0))
    fraction, exponent = math.frexp(f32(maximum))
    scale = f32(f32(fraction * 256.0) / f32(maximum))

    def channel(value):
        scaled = f32(f32(value) * scale)
        return int(min(255.0, max(0.0, scaled)))

    encoded_exponent = exponent + 128
    if not 0 <= encoded_exponent <= 255:
        return bytes((0, 0, 0, 0))
    return bytes(
        (channel(red), channel(green), channel(blue), encoded_exponent)
    )


def verify_static():
    blob = LIBCP.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    require(digest == EXPECTED_LIBCP_SHA256, "installed libcp SHA-256")
    require(HEADER + b"\x00" in blob, "Radiance header bytes missing")
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    signatures = {
        (ins.address, ins.mnemonic, ins.op_str)
        for ins in md.disasm(blob[0x902B0:0x90810], 0x902B0)
    }
    required = {
        (0x90554, "movaps", "xmm3, xmm7"),
        (0x90557, "maxps", "xmm3, xmm4"),
        (0x9055A, "maxps", "xmm3, xmm9"),
        (0x90601, "mulps", "xmm5, xmm15"),
        (0x90605, "divps", "xmm5, xmm3"),
        (0x9060F, "maxps", "xmm0, xmm7"),
        (0x90616, "minps", "xmm1, xmm0"),
        (0x9063A, "cvttps2dq", "xmm0, xmm1"),
        (0x9065A, "movups", "xmmword ptr [r12 + rsi*4], xmm0"),
        (0x90772, "shl", "r8d, 2"),
        (0x9077C, "call", "rax"),
    }
    missing = required - signatures
    require(not missing, f"missing RGBE writer signatures: {sorted(missing)!r}")
    return {
        "binary_sha256": digest,
        "writer_body": "0x902b0",
        "header": HEADER.decode("ascii"),
    }


def verify_runtime():
    report = json.loads(RUNTIME.read_text())
    require(not report["errors"], "runtime capture errors")
    capture = report["capture"]
    values = capture["input_rgb_float32"]
    expected = bytearray()
    for index in range(capture["pixel_count"]):
        expected.extend(encode_pixel(*values[index * 3 : index * 3 + 3]))
    actual = bytes.fromhex(capture["packed_rgbe_hex"])
    require(bytes(expected) == actual, "captured RGBE bytes mismatch")
    return {
        "pixel_count": capture["pixel_count"],
        "row_index": capture["row_index_r15"],
        "width": capture["width_r8"],
        "packed_sha256": hashlib.sha256(actual).hexdigest(),
    }


def verify_complete_file():
    with COMPLETE_HDR.open("rb") as handle:
        header = handle.read(len(HEADER))
        resolution = handle.readline()
        body_offset = handle.tell()
    require(header == HEADER, "complete HDR header mismatch")
    require(resolution == b"-Y 7824 +X 10432\n", "resolution/orientation mismatch")
    expected_size = body_offset + 10432 * 7824 * 4
    require(COMPLETE_HDR.stat().st_size == expected_size, "flat RGBE size mismatch")
    with COMPLETE_HDR.open("rb") as handle:
        handle.seek(body_offset)
        marker = handle.read(4)
    require(
        not (
            marker[:2] == b"\x02\x02"
            and int.from_bytes(marker[2:], "big") == 10432
        ),
        "writer unexpectedly emitted scanline RLE",
    )
    return {
        "path": str(COMPLETE_HDR),
        "width": 10432,
        "height": 7824,
        "orientation": "-Y +X",
        "body": "legacy flat RGBE, four bytes per pixel",
        "file_sha256": hashlib.sha256(COMPLETE_HDR.read_bytes()).hexdigest(),
    }


def main():
    result = {
        "status": "PASS",
        "static": verify_static(),
        "runtime": verify_runtime(),
        "complete_file": verify_complete_file(),
    }
    output = ROOT / "runs/output_rgbe_writer/verification.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
