#!/usr/bin/env python3
"""Verify the admitted mechanical subset of DemosaickLightV1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUNS = ROOT / "runs/demosaic_light_v1"

BODY_HASHES = {
    (0x2EB560, 0x2EB882): "92a21c74b71fad4b0cd661e5bb96e1ba7ab23daae51021bf1de2308b158a27bf",
    (0x2EC2B0, 0x2ECE03): "75e34c1ce746613e3b08211e5e1f25b6d6617ba707d1a4181967c10ad6cda60b",
    (0x2ECE10, 0x2ED4E6): "30a3383e38ae88980129018e87018fd8ad875b646d2f4e65620884fa92a6e851",
    (0x2EE350, 0x2EEA72): "8962f2e587536df0658f0f5fa6718be9f9726baea09db05a97718e6d76220fcf",
    (0x2ED580, 0x2EE06D): "c70de6a4944e6f44f949cea4a069f1fe852218376cccb340f588619c10a076d6",
    (0x2EEB20, 0x2EF606): "5efcdd87d873abd4e24a3f0685b23ebdcc9a43d4af28faf9a7a1b0ac1e9512c2",
    (0x2EF6A0, 0x2F01A6): "75b613812246dc5a77facc28fb454c9a83b2018fce095eb2f13476f520986c0e",
    (0x2F0240, 0x2F0D56): "595cc7b736cb28c804f4987c143d148b597fa6556ed5ecc9553662e192f8ba2b",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def instructions(data: bytes, start: int, end: int) -> dict[int, tuple[str, str]]:
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    return {
        item.address: (item.mnemonic, item.op_str)
        for item in decoder.disasm(data[start:end], start)
    }


def require_instruction(
    decoded: dict[int, tuple[str, str]], address: int, mnemonic: str, operands: str
) -> None:
    expected = (mnemonic, operands)
    require(decoded.get(address) == expected, f"0x{address:x}: {decoded.get(address)} != {expected}")


def verify_static() -> dict:
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(
        digest == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        "libcp SHA-256 drift",
    )
    for (start, end), expected in BODY_HASHES.items():
        require(hashlib.sha256(data[start:end]).hexdigest() == expected, f"body 0x{start:x}")

    variants = {
        "RGGB": (0x65A048, 0x2ED580),
        "GRBG": (0x65A0C8, 0x2EEB20),
        "GBRG": (0x65A148, 0x2EF6A0),
        "BGGR": (0x65A1C8, 0x2F0240),
    }
    for phase, (table, body) in variants.items():
        require(struct.unpack_from("<Q", data, table + 0x30)[0] == body, f"{phase} table")

    driver = instructions(data, 0x2EB560, 0x2EB882)
    for address, mnemonic, operands in (
        (0x2EB5DE, "mov", "eax, dword ptr [r12 + 4]"),
        (0x2EB5E3, "or", "eax, dword ptr [r12]"),
        (0x2EB5E7, "cmp", "eax, 2"),
        (0x2EB601, "mov", "eax, dword ptr [r12]"),
        (0x2EB605, "cmp", "dword ptr [r12 + 4], 0"),
    ):
        require_instruction(driver, address, mnemonic, operands)

    # Each specialization writes the gain vector in raster order for its
    # Bayer quad. Source offsets are R=0, G=4, B=8.
    gain_sequences = {
        "RGGB": (
            0x2ED5F4,
            (("[rax]", "ecx"), ("[rax + 4]", "ecx"), ("[rax + 4]", "ecx"), ("[rax + 8]", "eax")),
        ),
        "GRBG": (
            0x2EEB94,
            (("[rax + 4]", "ecx"), ("[rax]", "ecx"), ("[rax + 8]", "ecx"), ("[rax + 4]", "eax")),
        ),
        "GBRG": (
            0x2EF714,
            (("[rax + 4]", "ecx"), ("[rax + 8]", "ecx"), ("[rax]", "ecx"), ("[rax + 4]", "eax")),
        ),
        "BGGR": (
            0x2F02B4,
            (("[rax + 8]", "ecx"), ("[rax + 4]", "ecx"), ("[rax + 4]", "ecx"), ("[rax]", "eax")),
        ),
    }
    gain_destinations = (0x38, 0x34, 0x30, 0x2C)
    for phase, (start, sequence) in gain_sequences.items():
        decoded = instructions(data, start, start + 0x20)
        ordered = sorted(decoded.items())
        loads = [
            (address, operands)
            for address, (mnemonic, operands) in ordered
            if mnemonic == "mov" and operands.startswith(("ecx, dword ptr", "eax, dword ptr"))
        ]
        stores = [
            (address, operands)
            for address, (mnemonic, operands) in ordered
            if mnemonic == "mov" and operands.startswith("dword ptr [rbp - ")
        ]
        require(len(loads) == len(stores) == 4, f"{phase} gain instruction count")
        for index, ((_, load), (_, store), (source, register)) in enumerate(
            zip(loads, stores, sequence)
        ):
            require(load == f"{register}, dword ptr {source}", f"{phase} gain load {index}")
            require(
                store == f"dword ptr [rbp - 0x{gain_destinations[index]:x}], {register}",
                f"{phase} gain store {index}",
            )

    row = instructions(data, 0x2EC2B0, 0x2ECE03)
    constants = {
        0x5F18C8: 56.0,
        0x5AAE70: 6.0,
        0x5A8878: -4.0,
        0x5A8874: -2.0,
        0x5ABED4: 1.0 / 64.0,
        0x5F18C4: 1.0 / 1024.0,
        0x5F18CC: 5.0 / 512.0,
    }
    for address, expected in constants.items():
        actual = struct.unpack_from("<f", data, address)[0]
        require(actual == expected, f"constant 0x{address:x}: {actual}")

    # The pointer construction maps the 21 reads to center, axial-1,
    # diagonal-1, axial-2, and knight offsets. These checks make that mapping
    # reproducible instead of relying on prose-read disassembly.
    for address, mnemonic, operands in (
        (0x2EC54B, "lea", "rcx, [r12 + r11*4]"),
        (0x2EC591, "lea", "rcx, [rbx + r11*4]"),
        (0x2EC5B1, "lea", "rcx, [rsi + r11*4]"),
        (0x2EC5C3, "lea", "rcx, [rdx + r11*4]"),
        (0x2EC5D1, "lea", "rcx, [r8 + r11*4]"),
        (0x2EC5DF, "lea", "rdi, [rsi + rcx*4]"),
        (0x2EC5EA, "lea", "rdi, [rbx + rcx*4]"),
        (0x2EC5F5, "lea", "rcx, [r12 + rcx*4]"),
        (0x2EC603, "lea", "rdi, [rsi + rcx*4]"),
        (0x2EC60E, "lea", "rdi, [rbx + rcx*4]"),
        (0x2EC619, "lea", "rcx, [r12 + rcx*4]"),
        (0x2EC627, "lea", "r13, [r8 + rcx*4]"),
        (0x2EC62E, "lea", "r8, [rdx + rcx*4]"),
        (0x2EC632, "lea", "r9, [rsi + rcx*4]"),
        (0x2EC636, "lea", "r10, [rbx + rcx*4]"),
        (0x2EC63A, "lea", "r11, [r12 + rcx*4]"),
        (0x2EC641, "lea", "r15, [r14 + rdi*4]"),
        (0x2EC645, "lea", "r14, [rdx + rdi*4]"),
        (0x2EC649, "lea", "rcx, [rsi + rdi*4]"),
        (0x2EC64D, "lea", "rsi, [rbx + rdi*4]"),
        (0x2EC651, "lea", "rdi, [r12 + rdi*4]"),
    ):
        require_instruction(row, address, mnemonic, operands)

    for address, mnemonic, operands in (
        (0x2EC66C, "mulss", "xmm1, xmm8"),
        (0x2EC694, "mulss", "xmm0, xmm5"),
        (0x2EC6AE, "mulss", "xmm2, xmm6"),
        (0x2EC6E2, "mulss", "xmm3, xmm7"),
        (0x2EC73B, "mulss", "xmm0, xmm4"),
        (0x2EC74B, "add", "rbx, 2"),
        (0x2EC4E1, "mov", "esi, dword ptr [r12 + 0x40]"),
        (0x2EC4F0, "add", "esi, ebx"),
        (0x2EC4F9, "and", "esi, 1"),
        (0x2EC809, "xor", "ebx, 1"),
        (0x2ECA27, "subps", "xmm6, xmm7"),
        (0x2ECA2D, "addps", "xmm4, xmm3"),
        (0x2ECA30, "mulps", "xmm4, xmm9"),
        (0x2ECA34, "subps", "xmm2, xmm4"),
        (0x2ECA37, "addps", "xmm6, xmm8"),
        (0x2ECA3B, "addps", "xmm6, xmm5"),
        (0x2ECA3E, "rcpps", "xmm3, xmm6"),
        (0x2ECD4F, "subps", "xmm3, xmm2"),
        (0x2ECD52, "subps", "xmm2, xmm4"),
        (0x2ECD65, "subps", "xmm5, xmm6"),
        (0x2ECD6B, "subss", "xmm4, xmm1"),
        (0x2ECD73, "addps", "xmm4, xmm3"),
        (0x2ECD76, "addps", "xmm2, xmm0"),
        (0x2ECD79, "addps", "xmm2, xmm5"),
        (0x2ECD8A, "mulps", "xmm2, xmm8"),
    ):
        require_instruction(row, address, mnemonic, operands)

    raw_rows = instructions(data, 0x2ECE10, 0x2ED4E6)
    for address, mnemonic, operands in (
        (0x2ECEB3, "cmp", "esi, r14d"),
        (0x2ECEB9, "cmovge", "eax, esi"),
        (0x2ECEBC, "cmp", "eax, edx"),
        (0x2ECEC1, "cmovg", "r9d, edx"),
        (0x2ECF0C, "add", "edx, dword ptr [rbp - 0x34]"),
        (0x2ECF11, "and", "esi, 1"),
        (0x2ECF37, "movss", "xmm0, dword ptr [rdi + rsi*4 + 0x48]"),
        (0x2ECF3D, "movss", "xmm1, dword ptr [rdi + rdx*4 + 0x48]"),
        (0x2ECF9F, "mulss", "xmm2, xmm0"),
        (0x2ECFA9, "mulss", "xmm3, xmm1"),
    ):
        require_instruction(raw_rows, address, mnemonic, operands)

    residual = instructions(data, 0x2EE350, 0x2EEA72)
    for address, mnemonic, operands in (
        (0x2EE5C1, "movss", "xmm0, dword ptr [rax + r8*4]"),
        (0x2EE5CB, "subss", "xmm0, dword ptr [rcx + r8*4]"),
        (0x2EE8B0, "movss", "xmm0, dword ptr [rsi + r9*4]"),
        (0x2EE8B6, "subss", "xmm0, dword ptr [rax + r9*4]"),
        (0x2EE8BC, "movss", "dword ptr [rbx + r9*4], xmm0"),
    ):
        require_instruction(residual, address, mnemonic, operands)

    main = instructions(data, 0x2EEB20, 0x2EF606)
    for address, mnemonic, operands in (
        (0x2EEB45, "movss", "xmm3, dword ptr [rax]"),
        (0x2EEB49, "maxss", "xmm3, dword ptr [rax + 4]"),
        (0x2EEB4E, "maxss", "xmm3, dword ptr [rax + 8]"),
        (0x2EEC3B, "movss", "xmm2, dword ptr [rip + 0x302c81]"),
        (0x2EED89, "movss", "xmm0, dword ptr [rbp - 0x268]"),
        (0x2EED91, "mulss", "xmm0, dword ptr [rip + 0x302b33]"),
        (0x2EEDC6, "mov", "r12, 0xffffffffffffffe0"),
        (0x2EEE8E, "mov", "qword ptr [rbp + r12 - 0x1c0], rax"),
        (0x2EEEA4, "mov", "qword ptr [rbp + r12 - 0x1e0], rax"),
        (0x2EEEAC, "inc", "ebx"),
        (0x2EEEAE, "add", "r12, 8"),
        (0x2EEEB2, "jne", "0x2eedd0"),
        (0x2EEF80, "movss", "xmm2, dword ptr [r10 + rcx]"),
        (0x2EEF90, "andps", "xmm1, xmm12"),
        (0x2EEFA7, "rcpss", "xmm1, xmm1"),
        (0x2EEFC3, "mulss", "xmm5, xmm1"),
        (0x2EEFD1, "mulss", "xmm4, xmm3"),
        (0x2EF039, "mulss", "xmm3, xmm4"),
        (0x2EF049, "mulss", "xmm1, xmm5"),
        (0x2EF04D, "addss", "xmm3, xmm2"),
        (0x2EF051, "addss", "xmm1, xmm2"),
        (0x2EF055, "addss", "xmm2, dword ptr [r11 + rcx]"),
        (0x2EF05E, "movss", "dword ptr [r9 + r13*4], xmm3"),
        (0x2EF098, "mov", "dword ptr [r9 + rax*4], 0x3f800000"),
        (0x2EF487, "add", "r12, 2"),
        (0x2EF48B, "add", "rcx, 8"),
        (0x2EF492, "jl", "0x2eef80"),
    ):
        require_instruction(main, address, mnemonic, operands)

    return {
        "libcp_sha256": digest,
        "body_hashes": {
            f"0x{start:x}..0x{end:x}": expected
            for (start, end), expected in BODY_HASHES.items()
        },
        "variants": {phase: f"0x{body:x}" for phase, (_, body) in variants.items()},
        "stencil": {
            "center": 56.0,
            "axial_1": 6.0,
            "diagonal_1": -4.0,
            "axial_2": -2.0,
            "knight": 1.0,
            "divisor": 64.0,
            "sum": 64.0,
        },
    }


def verify_runtime(path: Path) -> dict:
    report = json.loads(path.read_text())
    require(not report["errors"], f"runtime errors: {report['errors']}")
    require(report["process"]["exit_status"] == 0, "runtime did not exit cleanly")
    captures = {capture["stage"]: capture for capture in report["captures"]}
    require(
        set(captures)
        == {"entry_2eef80", "preadd_2ef04d", "final_2ef05e", "quad_2ef480"},
        "capture stages",
    )
    entry = captures["entry_2eef80"]
    preadd = captures["preadd_2ef04d"]
    final = captures["final_2ef05e"]
    quad = captures["quad_2ef480"]
    require(
        entry["thread_id"]
        == preadd["thread_id"]
        == final["thread_id"]
        == quad["thread_id"],
        "thread continuity",
    )

    center = entry["samples"]["A1"][1]
    epsilon = entry["epsilon"]
    require(preadd["xmm2"][0] == center, "center custody to pre-add")

    a1 = entry["samples"]["A1"]
    b1 = entry["samples"]["B1"]
    wl = 1.0 / (abs(center - a1[0]) + epsilon)
    wr = 1.0 / (abs(center - a1[2]) + epsilon)
    horizontal = (b1[0] * wl + b1[2] * wr) / (wl + wr)
    require(math.isclose(preadd["xmm3"][0], horizontal, rel_tol=5e-4, abs_tol=2e-6), "horizontal formula")

    a0 = entry["samples"]["A0"][1]
    a2 = entry["samples"]["A2"][1]
    b0 = entry["samples"]["B0"][1]
    b2 = entry["samples"]["B2"][1]
    w0 = 1.0 / (abs(center - a0) + epsilon)
    w2 = 1.0 / (abs(center - a2) + epsilon)
    vertical = (b0 * w0 + b2 * w2) / (w0 + w2)
    require(math.isclose(preadd["xmm1"][0], vertical, rel_tol=5e-4, abs_tol=2e-6), "vertical formula")

    require(final["xmm3"][0] == f32(preadd["xmm3"][0] + center), "channel 0 add-back")
    require(final["xmm1"][0] == f32(preadd["xmm1"][0] + center), "channel 2 add-back")
    require(final["xmm2"][0] == f32(center + b1[1]), "channel 1 add-back")

    # Reconstruct the complete GRBG 2x2 output quad. Window indices are
    # x-1, x, x+1, x+2, x+3.
    windows = entry["windows"]

    def weighted(guide_center, guides, candidates):
        weights = [1.0 / (abs(guide_center - value) + epsilon) for value in guides]
        return sum(value * weight for value, weight in zip(candidates, weights)) / sum(weights)

    a0w, a1w, a2w, a3w = (windows[f"A{i}"] for i in range(4))
    b0w, b1w, b2w, b3w = (windows[f"B{i}"] for i in range(4))
    a1x, a1x1 = a1w[1], a1w[2]
    a2x, a2x1 = a2w[1], a2w[2]

    expected_row0 = [
        a1x + weighted(a1x, [a1w[0], a1w[2]], [b1w[0], b1w[2]]),
        a1x + b1w[1],
        a1x + weighted(a1x, [a0w[1], a2w[1]], [b0w[1], b2w[1]]),
        1.0,
        a1x1 + b1w[2],
        a1x1
        + weighted(
            a1x1,
            [a1w[1], a1w[3], a0w[2], a2w[2]],
            [b1w[1], b1w[3], b0w[2], b2w[2]],
        ),
        a1x1
        + weighted(
            a1x1,
            [a0w[1], a0w[3], a2w[1], a2w[3]],
            [b0w[1], b0w[3], b2w[1], b2w[3]],
        ),
        1.0,
    ]
    expected_row1 = [
        a2x
        + weighted(
            a2x,
            [a1w[0], a1w[2], a3w[0], a3w[2]],
            [b1w[0], b1w[2], b3w[0], b3w[2]],
        ),
        a2x
        + weighted(
            a2x,
            [a2w[0], a2w[2], a1w[1], a3w[1]],
            [b2w[0], b2w[2], b1w[1], b3w[1]],
        ),
        a2x + b2w[1],
        1.0,
        a2x1 + weighted(a2x1, [a1w[2], a3w[2]], [b1w[2], b3w[2]]),
        a2x1 + b2w[2],
        a2x1 + weighted(a2x1, [a2w[1], a2w[3]], [b2w[1], b2w[3]]),
        1.0,
    ]
    for label, actual, expected in (
        ("row0", quad["row0_rgba2"], expected_row0),
        ("row1", quad["row1_rgba2"], expected_row1),
    ):
        for index, (got, want) in enumerate(zip(actual, expected)):
            require(
                math.isclose(got, want, rel_tol=8e-4, abs_tol=3e-6),
                f"{label}[{index}] {got} != {want}",
            )
    return report


def verify_guide_runtime(path: Path) -> dict:
    report = json.loads(path.read_text())
    require(not report["errors"], f"guide runtime errors: {report['errors']}")
    require(report["process"]["exit_status"] == 0, "guide runtime did not exit cleanly")
    captures = {capture["stage"]: capture for capture in report["captures"]}
    require(
        set(captures)
        == {
            "stencil_2ec660",
            "stencil_output_2ec746",
            "stage2_input_2eca16",
            "stage2_output_2eca7a",
            "stage3_input_2ecd4f",
            "stage3_output_2ecdbc",
        },
        "guide capture stages",
    )
    thread_ids = {capture["thread_id"] for capture in captures.values()}
    require(len(thread_ids) == 1, "guide thread continuity")

    stencil = captures["stencil_2ec660"]
    stencil_sum = (
        56.0 * stencil["center"][0]
        + 6.0 * sum(stencil["axial1"])
        - 4.0 * sum(stencil["diagonal1"])
        - 2.0 * sum(stencil["axial2"])
        + sum(stencil["knight"])
    )
    stencil_expected = stencil_sum / 64.0
    require(
        math.isclose(
            captures["stencil_output_2ec746"]["output"],
            stencil_expected,
            rel_tol=2e-6,
            abs_tol=2e-7,
        ),
        "21-tap stencil runtime formula",
    )

    stage2 = captures["stage2_input_2eca16"]
    center = stage2["center_s"]
    far = stage2["far_s"]
    mid = stage2["mid_guide"]
    axis_gradient = [abs(mid[0] - mid[1])] * 2 + [abs(mid[2] - mid[3])] * 2
    weights = [
        1.0 / (abs(value - center) + gradient + stage2["epsilon"])
        for value, gradient in zip(far, axis_gradient)
    ]
    corrections = [
        guide - 0.5 * (center + far_value)
        for guide, far_value in zip(mid, far)
    ]
    stage2_expected = center + sum(
        weight * correction for weight, correction in zip(weights, corrections)
    ) / sum(weights)
    require(
        math.isclose(
            captures["stage2_output_2eca7a"]["output"],
            stage2_expected,
            rel_tol=8e-4,
            abs_tol=3e-6,
        ),
        "stage-2 guide runtime formula",
    )

    stage3 = captures["stage3_input_2ecd4f"]
    center_s = stage3["center_s"]
    center_guide = stage3["center_guide"]
    weights = [
        1.0
        / (
            abs(far_s - center_s)
            + abs(adjacent - center_guide)
            + stage3["epsilon"]
        )
        for far_s, adjacent in zip(stage3["far_s"], stage3["adjacent_guide"])
    ]
    corrections = [
        0.5 * ((center_guide - center_s) + (far_guide - far_s))
        for far_guide, far_s in zip(stage3["far_guide"], stage3["far_s"])
    ]
    stage3_expected = center_s + sum(
        weight * correction for weight, correction in zip(weights, corrections)
    ) / sum(weights)
    require(
        math.isclose(
            captures["stage3_output_2ecdbc"]["output"],
            stage3_expected,
            rel_tol=8e-4,
            abs_tol=3e-6,
        ),
        "stage-3 guide runtime formula",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = {"status": "OK", "static": verify_static()}
    runtime_path = RUNS / "runtime_unit1_28mm.json"
    guide_runtime_path = RUNS / "guide_runtime_unit1_28mm.json"
    if runtime_path.is_file():
        result["runtime"] = verify_runtime(runtime_path)
    elif args.require_runtime:
        raise AssertionError(f"missing {runtime_path}")
    if guide_runtime_path.is_file():
        result["guide_runtime"] = verify_guide_runtime(guide_runtime_path)
    elif args.require_runtime:
        raise AssertionError(f"missing {guide_runtime_path}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        "PASS DemosaickLightV1 exact formula "
        f"variants=4 runtime={int('runtime' in result)} "
        f"guide_runtime={int('guide_runtime' in result)}"
    )


if __name__ == "__main__":
    main()
