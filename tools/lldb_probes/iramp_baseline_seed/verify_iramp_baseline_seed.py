#!/usr/bin/env python3
"""Verify the fixed IRAMP src2 baseline numerator and denominator seed."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_OP_MEM, X86_OP_REG, X86_REG_RAX, X86_REG_RBX


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
RUN_ROOT = ROOT / "runs/iramp_accumulator_reconstruction"

CAPTURE_HASHES = {
    "unit1_35mm": {
        "before.bin": "86eedfefed171ea03515cce5e89daa251e61205c5cedfe3b39cca29fb01d352f",
        "after.bin": "49fbf1297b870f5d379be49bc215daa7194428e42945e9722b76cc3b04350fb0",
        "capture.json": "df4d4bcb6ff53b645929c881b2348df689b0967a4d73a4634fe463288517d81c",
    },
    "unit1_35mm_nonbaseline": {
        "before.bin": "d5782c77ebc0bbd3aa08bfb86117ba13132b8762d87152a752a439bae539ef83",
        "after.bin": "0a3bbbf8c773526283777a86e91e246acc0febefb90881d0187121d0809535b6",
        "capture.json": "ad508e53fe944f36fecc785af011597ffbf9f12aa469874bda2cec80330cfe3e",
    },
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


STATIC = load_module("iramp_baseline_static", STATIC_PATH)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def decode(data: bytes, mapping, start: int, end: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    return list(decoder.disasm(STATIC.bytes_at(data, mapping, start, end - start), start))


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    body = STATIC.bytes_at(data, mapping, 0x36B920, 0x36CDD2 - 0x36B920)
    require(
        hashlib.sha256(body).hexdigest()
        == "9996624dc08b8e5a36f026fc4432141d34b6fc697e7d4dbdee14c6e7d1ea1915",
        "0x36b920 body changed",
    )

    table = struct.unpack("<20f", STATIC.bytes_at(data, mapping, 0x5E73C0, 0x50))
    require(
        all(f32_bits(value) == 0x3E4CCCCD for value in table[:4]),
        "0x5e73c0 baseline vec4 changed",
    )
    require(
        any(f32_bits(value) != 0x3E4CCCCD for value in table[4:]),
        "full setup table unexpectedly collapsed to baseline vec4",
    )

    guards = {
        0x36B94A: "488dbb80250000",
        0x36B951: "488d3568ba2700",
        0x36B958: "ba50000000",
        0x36B95D: "e8e2a61e00",
        0x36CC60: "0f280d59a72700",
        0x36CC83: "0f59d1",
        0x36CC86: "0f29940380150000",
        0x36CD98: "0f59c1",
        0x36CD9B: "0f29840370160000",
        0x36CDA3: "488d8800010000",
        0x36CDAA: "4881f900100000",
        0x36CDB1: "0f85b9feffff",
    }
    for va, expected_hex in guards.items():
        expected = bytes.fromhex(expected_hex)
        actual = STATIC.bytes_at(data, mapping, va, len(expected))
        require(actual == expected, f"opcode drift at 0x{va:x}: {actual.hex()}")

    instructions = decode(data, mapping, 0x36CC83, 0x36CDA3)
    pairs = []
    for index, item in enumerate(instructions[:-1]):
        if item.mnemonic != "mulps" or not item.op_str.endswith(", xmm1"):
            continue
        store = instructions[index + 1]
        require(store.mnemonic == "movaps", f"0x{item.address:x}: multiply not followed by store")
        require(
            len(item.operands) == 2
            and item.operands[0].type == X86_OP_REG
            and len(store.operands) == 2
            and store.operands[0].type == X86_OP_MEM
            and store.operands[1].type == X86_OP_REG
            and store.operands[1].reg == item.operands[0].reg,
            f"0x{item.address:x}: numerator register custody changed",
        )
        memory = store.operands[0].mem
        require(
            memory.base == X86_REG_RBX and memory.index == X86_REG_RAX,
            f"0x{store.address:x}: numerator destination base/index changed",
        )
        pairs.append(memory.disp)
    require(pairs == list(range(0x1580, 0x1680, 0x10)), f"coefficient stores changed: {pairs}")

    return digest


def verify_hashes() -> None:
    for capture_name, expected_files in CAPTURE_HASHES.items():
        directory = RUN_ROOT / capture_name
        for filename, expected in expected_files.items():
            path = directory / filename
            require(path.exists(), f"missing retained artifact {path}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            require(actual == expected, f"retained artifact changed: {path}")


def normalizers(raw: bytes) -> tuple[float, ...]:
    values = struct.unpack_from("<20f", raw, 0x2580)
    return tuple(values[index * 4] for index in range(5))


def verify_runtime_capture() -> tuple[float, float]:
    baseline_dir = RUN_ROOT / "unit1_35mm"
    before = (baseline_dir / "before.bin").read_bytes()
    after = (baseline_dir / "after.bin").read_bytes()
    report = json.loads((baseline_dir / "capture.json").read_text())
    require(len(before) == len(after) == 0x2800, "baseline scratch size")
    require(report["return_offset"] == 0x1580, "baseline return offset")
    require(
        all(f32_bits(value) == 0x3E4CCCCD for value in struct.unpack_from("<20f", before, 0x2580)),
        "baseline denominator seed is not five 0.2 vec4 vectors",
    )

    source = struct.unpack_from("<1024f", before, 0x0000)
    reconstructed = struct.unpack_from("<1024f", after, 0x1580)
    errors = [abs(actual - expected) for actual, expected in zip(reconstructed, source)]
    max_error = max(errors)
    mean_error = sum(errors) / len(errors)
    require(max_error <= 2.0e-6, f"baseline src2 reconstruction drift: {max_error}")

    nonbaseline_dir = RUN_ROOT / "unit1_35mm_nonbaseline"
    nonbaseline = (nonbaseline_dir / "before.bin").read_bytes()
    expected = (
        1.06253981590271,
        0.9859229922294617,
        0.6156874895095825,
        0.20000000298023224,
        0.20000000298023224,
    )
    require(
        tuple(f32_bits(value) for value in normalizers(nonbaseline))
        == tuple(f32_bits(value) for value in expected),
        "nonbaseline denominator vector changed",
    )
    return max_error, mean_error


def main() -> None:
    digest = verify_static()
    verify_hashes()
    max_error, mean_error = verify_runtime_capture()
    print(f"iramp_baseline_static=OK libcp={digest}")
    print("numerator_seed=0.2f*forward97(src2_patch_coefficients)")
    print("denominator_seed=five_vec4(0.2f)")
    print(f"baseline_identity_reconstruction=OK max_abs={max_error:.12g} mean_abs={mean_error:.12g}")
    print("nonbaseline_denominators=1.0625398159,0.9859229922,0.6156874895,0.2,0.2")
    print("iramp_baseline_seed=OK")


if __name__ == "__main__":
    main()
