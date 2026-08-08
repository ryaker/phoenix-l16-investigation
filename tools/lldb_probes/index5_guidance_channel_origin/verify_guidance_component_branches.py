#!/usr/bin/env python3
"""Verify CreateStereoImage component routes without inventing channel names."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path

from capstone.x86_const import X86_OP_IMM


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
REPORT = (
    ROOT
    / "runs/index5_guidance_channel_origin"
    / "guidance_component_branch_unit1_28mm.json"
)
CUSTODY_REPORT = ROOT / "runs/index5_guidance_channel_origin/guidance_origin_28mm.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("guidance_component_branch_static", STATIC_PATH)


def immediate(item) -> int:
    values = [operand.imm for operand in item.operands if operand.type == X86_OP_IMM]
    require(len(values) == 1, f"0x{item.address:x}: expected one immediate")
    return values[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> bytes:
    return struct.pack("<f", value)


def lower_cholesky3(matrix: list[list[float]]) -> list[list[float]]:
    """Replay the installed three-by-three lower Cholesky in double."""
    result = [[0.0] * 3 for _ in range(3)]
    result[0][0] = math.sqrt(matrix[0][0])
    result[1][0] = matrix[1][0] / result[0][0]
    result[2][0] = matrix[2][0] / result[0][0]
    result[1][1] = math.sqrt(
        matrix[1][1] - result[1][0] * result[1][0]
    )
    result[2][1] = (
        matrix[2][1] - result[2][0] * result[1][0]
    ) / result[1][1]
    result[2][2] = math.sqrt(
        (matrix[2][2] - result[2][0] * result[2][0])
        - result[2][1] * result[2][1]
    )
    return result


def inverse3(matrix: list[list[float]]) -> list[list[float]]:
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    determinant = (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )
    return [
        [(e * i - f * h) / determinant,
         (c * h - b * i) / determinant,
         (b * f - c * e) / determinant],
        [(f * g - d * i) / determinant,
         (a * i - c * g) / determinant,
         (c * d - a * f) / determinant],
        [(d * h - e * g) / determinant,
         (b * g - a * h) / determinant,
         (a * e - b * d) / determinant],
    ]


def multiply3(
    left: list[list[float]], right: list[list[float]]
) -> list[list[float]]:
    return [
        [
            sum(left[row][index] * right[index][column] for index in range(3))
            for column in range(3)
        ]
        for row in range(3)
    ]


def covariance3(
    diagonal_m2: tuple[float, ...],
    cross_m2: tuple[float, ...],
    count: float,
) -> list[list[float]]:
    # The installed body rounds the reciprocal and each multiply to float32
    # before promoting the covariance to double.
    reciprocal = f32(1.0 / count)
    diagonal = [f32(value * reciprocal) for value in diagonal_m2[:3]]
    cross = [f32(value * reciprocal) for value in cross_m2[:3]]
    return [
        [diagonal[0] + 0.001, cross[0], cross[2]],
        [cross[0], diagonal[1] + 0.001, cross[1]],
        [cross[2], cross[1], diagonal[2] + 0.001],
    ]


def replay_fitted_affine(raw: bytes) -> list[list[float]]:
    source_mean = struct.unpack_from("<3f", raw, 0x50)
    source_covariance = covariance3(
        struct.unpack_from("<3f", raw, 0x60),
        struct.unpack_from("<3f", raw, 0x70),
        struct.unpack_from("<f", raw, 0x80)[0],
    )
    target_mean = struct.unpack_from("<3f", raw, 0x90)
    target_covariance = covariance3(
        struct.unpack_from("<3f", raw, 0xA0),
        struct.unpack_from("<3f", raw, 0xB0),
        struct.unpack_from("<f", raw, 0xC0)[0],
    )
    source_factor = lower_cholesky3(source_covariance)
    target_factor = lower_cholesky3(target_covariance)
    linear = multiply3(target_factor, inverse3(source_factor))
    translation = [
        target_mean[row]
        - sum(linear[row][column] * source_mean[column] for column in range(3))
        for row in range(3)
    ]
    return [
        [f32(linear[row][column]) for column in range(3)]
        + [f32(translation[row])]
        for row in range(3)
    ] + [[0.0, 0.0, 0.0, 1.0]]


def verify_static() -> str:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    # This is a separate global property schema. It does not identify the
    # camera-key operands compared by the CreateStereoImage caller below.
    color_map = (
        ("none", 0x631BE7, 0x3283EF, 1),
        ("srgb", 0x632C9C, 0x32842C, 2),
        ("linear_srgb", 0x633839, 0x328469, 4),
        ("adobe_rgb", 0x633845, 0x3284A6, 3),
        ("linear_adobe_rgb", 0x63384F, 0x3284E3, 6),
        ("linear_prophoto_rgb", 0x633860, 0x32851D, 5),
    )
    for name, string_va, write_va, selector in color_map:
        require(
            STATIC.cstring(data, mapping, string_va).decode("ascii") == name,
            f"color-space label drift at 0x{string_va:x}",
        )
        require(
            immediate(STATIC.instruction(data, mapping, write_va)) == selector,
            f"{name} selector drift",
        )
    require(
        STATIC.cstring(data, mapping, 0x633826).decode("ascii")
        == "output color-space",
        "output color-space property label drift",
    )

    key_lineage = {
        0x3FC768: ("mov", "rdi, qword ptr [r12 + 0xe0]"),
        0x3FC770: ("call", "0x1bea00"),
        0x3FC775: ("mov", "dword ptr [rbp - 0x2c], eax"),
        0x3FC783: ("mov", "rcx, qword ptr [rax]"),
        0x3FC78A: ("lea", "rdx, [rbp - 0x2c]"),
        0x3FC798: ("call", "0x3f4b90"),
        0x3FC821: ("add", "rbx, 4"),
        0x3F4BA7: ("mov", "qword ptr [rbp - 0x4b0], rcx"),
        0x3F4BAE: ("mov", "rbx, rdx"),
        0x3F4BBF: ("mov", "rsi, qword ptr [r12 + 0xe0]"),
        0x3F4BC7: ("mov", "edx, dword ptr [rbx]"),
        0x3F4BD0: ("call", "0x1be970"),
        0x3F4C52: ("mov", "rsi, qword ptr [r12 + 0xe0]"),
        0x3F4C61: ("mov", "edx, dword ptr [rax]"),
        0x3F4C6A: ("call", "0x1be970"),
        0x3F5025: ("mov", "rsi, qword ptr [rbp - 0x4b0]"),
        0x3F502E: ("mov", "rdi, qword ptr [rbp - 0x4c0]"),
        0x3F5035: ("cmp", "esi, dword ptr [rdi]"),
        0x3F5037: ("sete", "bl"),
        0x3F5086: ("call", "0x27b7a0"),
    }
    for va, expected in key_lineage.items():
        item = STATIC.instruction(data, mapping, va)
        require(
            (item.mnemonic, item.op_str) == expected,
            f"camera-key lineage drift at 0x{va:x}: "
            f"{item.mnemonic} {item.op_str}",
        )

    calls = (
        (0x27C68B, 0x3775F0),
        (0x27C6CD, 0x377930),
        (0x27C322, 0x376D80),
        (0x27C355, 0x376D30),
        (0x376F61, 0x377A50),
        (0x37704D, 0x377A50),
        (0x3770C9, 0x9D970),
        (0x37729F, 0x25EC70),
        (0x37734B, 0x25EC70),
        (0x3773E9, 0x25EC70),
        (0x377483, 0x25EC70),
        (0x377B53, 0x377B70),
    )
    for call_va, target in calls:
        require(
            STATIC.direct_call_target(STATIC.instruction(data, mapping, call_va))
            == target,
            f"component-route call 0x{call_va:x} drift",
        )
    require(
        STATIC.instruction(data, mapping, 0x377A24).mnemonic == "blendps"
        and immediate(STATIC.instruction(data, mapping, 0x377A24)) == 8,
        "lane-3 pass-through blend drift",
    )
    require(
        STATIC.instruction(data, mapping, 0x27C140).mnemonic == "cvtps2dq",
        "direct float-to-int pack path drift",
    )
    require(
        STATIC.instruction(data, mapping, 0x27C7B0).mnemonic == "cvtps2dq",
        "matched float-to-int pack path drift",
    )
    require(
        struct.unpack("<f", STATIC.bytes_at(data, mapping, 0x5A8128, 4))[0]
        == 1.0,
        "covariance reciprocal numerator drift",
    )
    require(
        immediate(STATIC.instruction(data, mapping, 0x376F3E))
        == 0x3F50624DD2F1A9FC,
        "covariance regularizer drift",
    )
    require(
        struct.unpack("<d", struct.pack("<Q", 0x3F50624DD2F1A9FC))[0]
        == 0.001,
        "covariance regularizer decode drift",
    )
    require(
        immediate(STATIC.instruction(data, mapping, 0x376E6D)) == 100
        and immediate(STATIC.instruction(data, mapping, 0x376E7E)) == 99,
        "affine-fit sample thresholds drift",
    )
    require(
        immediate(STATIC.instruction(data, mapping, 0x27C33D)) == 0x3F800000,
        "CreateStereoImage affine identity setup drift",
    )

    windows = {
        (0x27B7A0, 0x27CDC0): (
            "4bdb42332ca7b6cf240cdc1f224b1f4af0e0de01c93e6362f4542725caff0aca"
        ),
        (0x3775F0, 0x377930): (
            "7e85383ab8049e7d7749fbf6048052e561c8113e0f0fc832d353c445d3fa9903"
        ),
        (0x377930, 0x377A50): (
            "1c80add2f1ed9e2c017ff3e493d732268ee0ceeb330d3caa3828c8d424d6bdc5"
        ),
        (0x376E50, 0x3775F0): (
            "5a6b878d04311b83e6f050652f3ca5e3570fed94fca0329b756f7f887141b04c"
        ),
        (0x377A50, 0x377B70): (
            "da11e2ac8990d595b424b56ea55eda82e091e072a8540464e1696609a04f1378"
        ),
        (0x9D970, 0x9DB20): (
            "3b18fe52b033431d93166691fa9fc08d0c9c3fb9b8d5780f4b276f5773e98ce2"
        ),
        (0x3F500D, 0x3F5096): (
            "d5200d312ccd98ba1f5f63c6bc983a2a782e9b20687f8ed5e2c073b4ba6fc29f"
        ),
        (0x3FC750, 0x3FC857): (
            "f4929a18f56305d86ae4d4097fe10578a664f3100cdbbda67f2c7f7219acdf56"
        ),
        (0x3F4B90, 0x3F4CD0): (
            "e1d8901f9ca21b6745b9645507a560312886b54a6be5052c70defd2d37168e00"
        ),
        (0x328392, 0x328608): (
            "1ca138c185b8015ecbb08d859dad3c6baec6a31f8cc6f0dcf32ea19d8987717e"
        ),
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(
            STATIC.bytes_at(data, mapping, start, end - start)
        ).hexdigest()
        require(actual == expected, f"window 0x{start:x}..0x{end:x} drift")
    return digest


def image_samples(image: dict) -> dict[str, list[float]]:
    require(image["read_ok"], "image descriptor unreadable")
    require(image["size"] == [2080, 1560], "image dimensions changed")
    return {
        name: packet["vec4f"] for name, packet in image["samples"].items()
    }


def verify_runtime() -> tuple[list[list[float]], list[list[float]]]:
    report = json.loads(REPORT.read_text())
    require(report["capture_complete"], "runtime capture incomplete")
    require(report["terminated_after_capture"], "runtime did not terminate")
    require(report["process"]["exit_status"] == 9, "unexpected exit status")
    require(not report["errors"], f"runtime errors: {report['errors']}")

    custody = json.loads(CUSTODY_REPORT.read_text())
    require(custody["event"]["node"]["key_0x20"] == 0, "custody key is not zero")
    require(
        custody["event"]["create_stereo_completed_count"] == 1,
        "key-0 insertion did not follow the first completed producer call",
    )
    require(
        custody["event"]["matching_create_stereo_event_indexes"] == [0],
        "key-0 payload does not match producer call 0",
    )

    raw_pairs = report.get("camera_key_pairs", report.get("color_selectors", []))
    camera_keys = [
        [
            item.get("source_camera_key_esi", item.get("selector_1_esi")),
            item.get(
                "anchor_camera_key_rdi_pointee",
                item.get("selector_2_rdi_pointee"),
            ),
        ]
        for item in raw_pairs
    ]
    require(
        camera_keys == [[0, 0], [4, 0]],
        f"camera-key routes changed: {camera_keys}",
    )

    entries = report["entries"]
    require(len(entries) == 2, f"expected two producer calls, got {len(entries)}")
    require(
        [[item["bool_1_stack"], item["bool_2_stack"]] for item in entries]
        == [[1, 1], [0, 1]],
        "producer route booleans changed",
    )
    require(
        entries[0]["output_vec4f_stack"] == entries[1]["output_vec4f_stack"],
        "producer calls do not share the public float output",
    )

    direct = report["direct_pack_sources"]
    require(len(direct) == 1, "unexpected direct-pack source count")
    require(direct[0]["matched_entry_index"] == 0, "direct route is not call 0")
    require(
        direct[0]["source_vec4f_rbx"]["addr"]
        == entries[0]["output_vec4f_stack"],
        "direct route is not the public Image<vec4x32f> output",
    )
    direct_samples = image_samples(direct[0]["source_vec4f_rbx"])
    for name, values in direct_samples.items():
        require(values[3] == 1.0, f"direct {name}: lane 3 is not 1")
        require(all(math.isfinite(value) for value in values), f"direct {name}: NaN")

    post = report["post_softisp"]
    require(post["matched_entry_index"] == 1, "matched route is not call 1")
    require(
        [post["bool_1_rbp_0x38"], post["bool_2_rbp_0x40"]] == [0, 1],
        "matched route branch values changed",
    )

    transform = report["post_guidance_transform"]
    source_samples = image_samples(transform["input_vec4f_rbp_minus_0x2a0"])
    output_samples = image_samples(
        transform["transformed_vec4f_rbp_minus_0x5d0"]
    )
    raw = bytes.fromhex(transform["transform_object_raw_0x00_0x110"])
    matrix = [
        list(struct.unpack_from("<4f", raw, 0xD0 + row * 0x10))
        for row in range(4)
    ]
    require(matrix[3] == [0.0, 0.0, 0.0, 1.0], "affine row 3 changed")
    fitted = replay_fitted_affine(raw)
    for row in range(4):
        for column in range(4):
            require(
                f32_bits(fitted[row][column]) == f32_bits(matrix[row][column]),
                f"affine-fit word mismatch at [{row},{column}]",
            )

    for name, source in source_samples.items():
        output = output_samples[name]
        expected = [
            sum(matrix[row][column] * source[column] for column in range(4))
            for row in range(3)
        ]
        for lane in range(3):
            require(
                math.isclose(output[lane], expected[lane], abs_tol=2e-5),
                f"{name} lane {lane}: affine formula mismatch",
            )
        require(source[3] == 1.0, f"{name}: source lane 3 is not 1")
        require(output[3] == source[3], f"{name}: lane 3 was not preserved")
    return matrix, list(direct_samples.values())


def main() -> None:
    digest = verify_static()
    matrix, direct_samples = verify_runtime()
    print(f"static_guidance_component_branches=OK libcp={digest}")
    print("installed_output_color_space_map=1:none,2:srgb,3:adobe_rgb,"
          "4:linear_srgb,5:linear_prophoto_rgb,6:linear_adobe_rgb")
    print("camera_key_lineage=state+0xe0 anchor; iterator source; "
          "same-map lookups; equality drives CreateStereoImage bool")
    print("runtime_routes=call0 source/anchor=A1/A1 direct; "
          "call1 source/anchor=A5/A1 affine-match")
    print(
        "guidance_components=call0 C0/C1/C2 direct rounded color components; "
        "C3=1 pass-through"
    )
    print(
        "call1_affine_rows="
        + ";".join(",".join(f"{value:.9g}" for value in row) for row in matrix)
    )
    print(
        "call1_affine_fit=population_covariance_float32_reciprocal;"
        "double_cholesky(target)*inverse(cholesky(source));epsilon=0.001;"
        "translation=target_mean-A*source_mean;all_16_words_exact"
    )
    print(f"direct_sample_count={len(direct_samples)} all_C3=1")
    print("guidance_component_branches=OK")


if __name__ == "__main__":
    main()
