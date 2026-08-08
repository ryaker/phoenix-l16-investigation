#!/usr/bin/env python3
"""Verify the exact 64-phase Catmull-Rom table built by libcp+0x36f800."""

import argparse
import hashlib
import json
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP


LIBCP_DEFAULT = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/"
    "Frameworks/libcp.dylib"
)
BODY_START = 0x36F800
TABLE_START = 0x36F82F
TABLE_END = 0x36FAA3
CALLER_START = 0x3D0650
CALLER_END = 0x3D08EB
EXPECTED_CONSTANTS = {
    0x5ABED4: 0.015625,
    0x5A8128: 1.0,
    0x5AAE80: 9.0,
    0x5D9A0C: -15.0,
    0x5AAE70: 6.0,
    0x5AAE60: struct.unpack("<f", bytes.fromhex("abaa2a3e"))[0],
    0x5A887C: 2.0,
    0x5AAEB0: -3.0,
    0x5AAE9C: 15.0,
    0x5D9A04: -0.375,
    0x5D9A08: -12.0,
    0x5AAE7C: 12.0,
    0x5D9A10: 0.375,
    0x5D9A14: -36.0,
}


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def add(a, b):
    return f32(f32(a) + f32(b))


def sub(a, b):
    return f32(f32(a) - f32(b))


def mul(a, b):
    return f32(f32(a) * f32(b))


def inner(x):
    x2 = mul(x, x)
    x3 = mul(x2, x)
    x3 = mul(x3, 9.0)
    x2 = mul(x2, -15.0)
    acc = add(x2, 6.0)
    acc = add(acc, x3)
    return mul(acc, EXPECTED_CONSTANTS[0x5AAE60])


def outer(x, phase, linear_scale, linear_bias):
    x2 = mul(x, x)
    x3 = mul(x2, x)
    x3 = mul(x3, -3.0)
    x2 = mul(x2, 15.0)
    acc = mul(f32(phase), linear_scale)
    acc = add(acc, linear_bias)
    acc = add(acc, x2)
    acc = add(acc, x3)
    return mul(acc, EXPECTED_CONSTANTS[0x5AAE60])


def phase_weights(phase):
    t = mul(f32(phase), 1.0 / 64.0)
    return (
        outer(add(t, 1.0), phase, -0.375, -12.0),
        inner(t),
        outer(sub(1.0, t), phase, 0.375, -12.0)
        if phase == 0
        else inner(sub(1.0, t)),
        0.0
        if phase == 0
        else outer(sub(2.0, t), phase, 0.375, -36.0),
    )


def expected_table():
    out = bytearray()
    for phase in range(64):
        for weight in phase_weights(phase):
            out.extend(struct.pack("<ffff", weight, weight, weight, weight))
    return bytes(out)


def verify_static(binary):
    blob = binary.read_bytes()
    if len(blob) <= max(EXPECTED_CONSTANTS):
        raise AssertionError("installed binary is too small")
    for address, expected in EXPECTED_CONSTANTS.items():
        actual = struct.unpack_from("<f", blob, address)[0]
        if struct.pack("<f", actual) != struct.pack("<f", expected):
            raise AssertionError(
                f"constant 0x{address:x}: expected {expected!r}, got {actual!r}"
            )

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    instructions = list(
        md.disasm(blob[TABLE_START:TABLE_END], TABLE_START)
    )
    if not instructions or instructions[-1].address != 0x36FA9D:
        raise AssertionError("table-generator instruction extent changed")
    signatures = {(ins.address, ins.mnemonic, ins.op_str) for ins in instructions}
    required = {
        (0x36F890, "xorps", "xmm13, xmm13"),
        (0x36F894, "cvtsi2ss", "xmm13, ecx"),
        (0x36F899, "movaps", "xmm0, xmm13"),
        (0x36F89D, "mulss", "xmm0, xmm8"),
        (0x36F91B, "movaps", "xmmword ptr [rax - 0x30], xmm6"),
        (0x36F98A, "movaps", "xmmword ptr [rax - 0x20], xmm2"),
        (0x36FA0A, "movaps", "xmmword ptr [rax - 0x10], xmm2"),
        (0x36FA8F, "movaps", "xmmword ptr [rax], xmm2"),
        (0x36FA92, "inc", "rcx"),
        (0x36FA95, "add", "rax, 0x40"),
        (0x36FA99, "cmp", "rcx, 0x40"),
        (0x36FA9D, "jne", "0x36f890"),
    }
    missing = required - signatures
    if missing:
        raise AssertionError(f"missing generator signatures: {sorted(missing)!r}")

    rip_targets = set()
    for ins in instructions:
        for operand in ins.operands:
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                rip_targets.add(ins.address + ins.size + operand.mem.disp)
    missing_constants = set(EXPECTED_CONSTANTS) - rip_targets
    if missing_constants:
        raise AssertionError(
            f"constants not referenced by generator: {sorted(missing_constants)!r}"
        )
    caller = list(md.disasm(blob[CALLER_START:CALLER_END], CALLER_START))
    caller_signatures = {
        (ins.address, ins.mnemonic, ins.op_str) for ins in caller
    }
    required_caller = {
        (0x3D0737, "cvtsi2ss", "xmm0, esi"),
        (0x3D0743, "divss", "xmm4, xmm0"),
        (0x3D074F, "cvtsi2ss", "xmm5, eax"),
        (0x3D0753, "divss", "xmm5, xmm1"),
        (0x3D07A9, "addss", "xmm0, xmm4"),
        (0x3D07B9, "addss", "xmm2, xmm4"),
        (0x3D07C1, "roundss", "xmm0, xmm0, 9"),
        (0x3D07CD, "roundss", "xmm2, xmm2, 0xa"),
        (0x3D0808, "cmovs", "eax, esi"),
        (0x3D0813, "cmovle", "edi, r9d"),
        (0x3D085E, "mulss", "xmm0, xmm3"),
        (0x3D0879, "subss", "xmm0, xmm2"),
        (0x3D08A1, "cvtss2sd", "xmm0, xmm3"),
        (0x3D08CE, "call", "0x36f800"),
    }
    missing_caller = required_caller - caller_signatures
    if missing_caller:
        raise AssertionError(
            f"missing selected-cache caller signatures: {sorted(missing_caller)!r}"
        )
    if struct.unpack_from("<f", blob, 0x5A8874)[0] != -2.0:
        raise AssertionError("selected-cache lower footprint constant changed")
    if struct.unpack_from("<f", blob, 0x5A887C)[0] != 2.0:
        raise AssertionError("selected-cache upper footprint constant changed")

    return {
        "binary_sha256": hashlib.sha256(blob).hexdigest(),
        "instruction_count": len(instructions),
        "selected_cache_caller_instruction_count": len(caller),
        "constant_addresses": [f"0x{x:x}" for x in sorted(EXPECTED_CONSTANTS)],
        "selected_cache_input_formula": {
            "scale": "(selected_level_width / requested_width, "
            "selected_level_height / requested_height), float32",
            "temporary_roi": "clamp(floor(requested_min*scale-2), "
            "ceil(requested_max*scale+2))",
            "offset": "requested_min*scale - temporary_roi_min, float32 "
            "promoted to double",
        },
    }


def verify_runtime(path, expected):
    payload = json.loads(path.read_text())
    table = payload["setup_packet"]["weight_table_complete"]
    actual = bytes.fromhex(table["raw_hex"])
    if table["byte_count"] != 4096 or len(actual) != 4096:
        raise AssertionError("runtime table is not 4096 bytes")
    if hashlib.sha256(actual).hexdigest() != table["sha256"]:
        raise AssertionError("runtime table SHA-256 field is inconsistent")
    if actual != expected:
        for offset, (got, want) in enumerate(zip(actual, expected)):
            if got != want:
                raise AssertionError(
                    f"runtime mismatch at byte {offset}: got 0x{got:02x}, "
                    f"expected 0x{want:02x}"
                )
        raise AssertionError("runtime table length mismatch")
    vectors = table["phase_tap_vec4"]
    if len(vectors) != 64 or any(len(phase) != 4 for phase in vectors):
        raise AssertionError("runtime phase/tap shape is not 64x4")
    if any(len(set(vector)) != 1 for phase in vectors for vector in phase):
        raise AssertionError("runtime vec4 lanes are not replicated")
    return {
        "path": str(path),
        "table_sha256": table["sha256"],
        "phase_0": [vector[0] for vector in vectors[0]],
        "phase_32": [vector[0] for vector in vectors[32]],
        "phase_63": [vector[0] for vector in vectors[63]],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=LIBCP_DEFAULT)
    parser.add_argument("--runtime-json", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    expected = expected_table()
    report = {
        "status": "PASS",
        "kernel": {
            "name": "Catmull-Rom cubic convolution",
            "support": 2,
            "phase_count": 64,
            "taps": ["floor(x)-1", "floor(x)", "floor(x)+1", "floor(x)+2"],
            "phase_fraction": "phase / 64",
            "inner": "(9*d^3 - 15*d^2 + 6) / 6, 0 <= d < 1",
            "outer": "(-3*d^3 + 15*d^2 - 24*d + 12) / 6, 1 <= d < 2",
            "zero": "0, d >= 2",
            "table_sha256": hashlib.sha256(expected).hexdigest(),
        },
        "static": verify_static(args.binary),
    }
    if args.runtime_json:
        report["runtime"] = verify_runtime(args.runtime_json, expected)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
