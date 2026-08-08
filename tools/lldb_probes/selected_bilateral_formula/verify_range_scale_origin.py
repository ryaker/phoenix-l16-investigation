#!/usr/bin/env python3
"""Verify the selected bilateral range-scale construction and public origins."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

BODY_HASHES = {
    (0x342B80, 0x342BA0): "884a6614e45f493a18299740689042602c390df598d463226de0b655b1cd021b",
    (0x342CA0, 0x3430E0): "97ab7a1b955c73e727cfc4a266ed70e85390b49fb3616576ce7da559e3da3583",
    (0x344470, 0x344E40): "43c5ecbcfb26d8f10881b864ba486ceedd5243beed4513d9de841e54f8332344",
    (0x345920, 0x34594F): "408189c9c0f69a70072931ab469ecf8ad4bdeb0a445b5fa5e4f2e87f1af1d580",
    (0x0EF050, 0x0EF0B5): "db9d1952623599ee03402d43b4bfab268336336c6773f07a4cfffadc8a8db9c3",
    (0x0EF890, 0x0EF992): "24a30de2ada43246d751fb95dce7a9592ecd948ca7c214bdbd6d1802f3b3ecf3",
    (0x0EFA50, 0x0EFBF6): "84ea904f5398e15a6b82713ffdef5835eccd6fe1bb46b816b6a7339dcda37a57",
    (0x2F4470, 0x2F4630): "bf3e11b03ebbd6f311e69c33e98db88ff82bb87825feb5241579bce413a09ef4",
    (0x2F53D0, 0x2F5EF0): "14bf861649acec9c7e0375499a05a3b232104f74f1e496df853502fa96d61474",
    (0x2F5FA0, 0x2F6202): "bdcca8a3092ac5bc7dae6737a48fba8e458ae2db4ab830bf84c45558eb3c2ab9",
    (0x2F63F0, 0x2F6420): "fb23649604311cceea47d16b957627c54b6f550206e93ff5ace4417d9244c096",
}

FOCAL_REPORTS = {
    "unit1_28mm": ROOT / "runs/2f53d0_downstream_helpers/helper_liveness_28mm.json",
    "unit1_35mm": ROOT / "runs/2f53d0_downstream_helpers/helper_liveness_35mm.json",
    "unit1_70mm": ROOT / "runs/2f53d0_downstream_helpers/helper_liveness_70mm_lazy.json",
    "unit1_150mm": ROOT / "runs/2f53d0_downstream_helpers/helper_liveness_150mm.json",
}

DENOISE_REPORTS = {
    label: ROOT / f"runs/denoise_route_census/{label}_denoise_algo.json"
    for label in (
        "unit1_28mm",
        "unit1_35mm",
        "unit1_70mm",
        "unit1_150mm",
        "unit2_35mm",
    )
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


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


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


def verify_static() -> dict[str, object]:
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, "installed libcp SHA-256 drift")
    for (start, end), expected in BODY_HASHES.items():
        actual = hashlib.sha256(data[start:end]).hexdigest()
        require(actual == expected, f"body 0x{start:x}..0x{end:x} drift")

    for offset, text in (
        (0x5F7BE0, b"setDenoisingENS3_12PipelineBase9DenoisingEE4$_51"),
        (0x5F7DE0, b"setDenoisingENS3_12PipelineBase9DenoisingEE4$_53"),
        (0x5F7FC0, b"setDenoisingENS3_12PipelineBase9DenoisingEE4$_55"),
    ):
        require(text in data[offset : offset + 0x120], f"RTTI at 0x{offset:x}")
    require(b"BayerFloatPipelinePayload" in data[0x5F7DE0 : 0x5F7E80], "BayerFloat RTTI")
    require(b"ColorPipelinePayload" in data[0x5F7FC0 : 0x5F8060], "Color RTTI")

    decoded: dict[int, tuple[str, str]] = {}
    for start, end in BODY_HASHES:
        decoded.update(instructions(data, start, end))
    decoded.update(instructions(data, 0x0F32D0, 0x0F32DA))
    expected_instructions = (
        # The demosaic closure names payload[0] operationally as neutral RGB.
        (0x342CB0, "mov", "rbx, rsi"),
        (0x342D85, "mov", "r8, qword ptr [rbx]"),
        (0x342D99, "call", "r9"),
        (0x342B84, "mov", "rdi, rsi"),
        (0x342B87, "mov", "rsi, rdx"),
        (0x342B8A, "mov", "rdx, rcx"),
        (0x342B8D, "mov", "rcx, r8"),
        (0x342B91, "jmp", "0x2eb560"),
        # The denoise closure reuses payload[0] and the CapturedImage at +0x08.
        (0x344484, "mov", "r12, rsi"),
        (0x3446BF, "mov", "rax, qword ptr [r12]"),
        (0x3446C3, "mov", "rdi, qword ptr [r12 + 8]"),
        (0x3446C8, "mov", "rbx, qword ptr [rax + 0x198]"),
        (0x3446CF, "call", "0xf32d0"),
        (0x3446D4, "movss", "xmm0, dword ptr [rax]"),
        (0x3446D8, "mov", "rcx, qword ptr [r12]"),
        (0x3446EA, "mov", "rdi, rbx"),
        (0x3446ED, "mov", "rsi, r15"),
        (0x3446F0, "call", "0xef890"),
        (0x0F32D4, "lea", "rax, [rdi + 0x40]"),
        # 0xef890 selects the installed row and builds the 0xefa50 callback.
        (0x0EF8BC, "call", "0xef050"),
        (0x0EF8ED, "mov", "qword ptr [rax + 8], r13"),
        (0x0EF8F1, "mov", "qword ptr [rax + 0x10], r12"),
        (0x0EF8F9, "mov", "qword ptr [rax + 0x18], rcx"),
        (0x0EF8FD, "mov", "qword ptr [rax + 0x20], rbx"),
        (0x0EF901, "mov", "qword ptr [rax + 0x28], r15"),
        # RGB slope/intercept packing and the exact first-stage operation order.
        (0x0EFA7F, "movss", "xmm0, dword ptr [rax + 0x38]"),
        (0x0EFA84, "movss", "xmm1, dword ptr [rax + 0x3c]"),
        (0x0EFA89, "insertps", "xmm0, dword ptr [rax + 0x70], 0x10"),
        (0x0EFA90, "insertps", "xmm0, dword ptr [rax + 0xa8], 0x20"),
        (0x0EFAA8, "insertps", "xmm1, dword ptr [rax + 0x74], 0x10"),
        (0x0EFAAF, "insertps", "xmm1, dword ptr [rax + 0xac], 0x20"),
        (0x0EFABF, "movss", "xmm4, dword ptr [rdx + 4]"),
        (0x0EFAC4, "movss", "xmm3, dword ptr [rdx + 8]"),
        (0x0EFAC9, "mov", "rax, qword ptr [rdi + 0x18]"),
        (0x0EFACD, "movss", "xmm5, dword ptr [rax]"),
        (0x0EFAD1, "insertps", "xmm5, dword ptr [rax + 4], 0x10"),
        (0x0EFAD8, "insertps", "xmm5, dword ptr [rax + 8], 0x20"),
        (0x0EFAE5, "divss", "xmm2, xmm3"),
        (0x0EFAE9, "subss", "xmm3, xmm4"),
        (0x0EFAED, "mulss", "xmm3, xmm2"),
        (0x0EFAF5, "mulps", "xmm3, xmm5"),
        (0x0EFAF8, "mulss", "xmm2, xmm4"),
        (0x0EFB52, "movaps", "xmm5, xmmword ptr [rax]"),
        (0x0EFB55, "mulps", "xmm5, xmm3"),
        (0x0EFB58, "addps", "xmm5, xmm2"),
        (0x0EFB5B, "mulps", "xmm5, xmm0"),
        (0x0EFB5E, "addps", "xmm5, xmm1"),
        (0x0EFB64, "maxps", "xmm6, xmm5"),
        (0x0EFB67, "sqrtps", "xmm5, xmm6"),
        (0x0EFB6A, "movaps", "xmmword ptr [rcx], xmm5"),
        # Fixed Ohta matrix and config+0x18 floor enter 0x2f4470.
        (0x2F5654, "movss", "xmm0, dword ptr [r13 + 0x18]"),
        (0x2F565A, "movaps", "xmmword ptr [rbp - 0x190], xmm0"),
        (0x2F566F, "lea", "rcx, [rbp - 0x190]"),
        (0x2F5679, "call", "0x2f4470"),
        (0x2F4580, "mov", "qword ptr [rax + 8], r12"),
        (0x2F4584, "mov", "qword ptr [rax + 0x10], r15"),
        (0x2F4588, "mov", "qword ptr [rax + 0x18], r14"),
        # Second-stage variance propagation and floor.
        (0x2F6170, "movaps", "xmm0, xmmword ptr [rdx]"),
        (0x2F6173, "mulps", "xmm0, xmm0"),
        (0x2F6185, "mulps", "xmm1, xmmword ptr [rbx]"),
        (0x2F6193, "mulps", "xmm2, xmmword ptr [rbx]"),
        (0x2F6196, "addps", "xmm2, xmm1"),
        (0x2F61A1, "mulps", "xmm0, xmmword ptr [rbx]"),
        (0x2F61A4, "addps", "xmm0, xmm2"),
        (0x2F61A7, "sqrtps", "xmm0, xmm0"),
        (0x2F61AA, "movaps", "xmm1, xmmword ptr [rax]"),
        (0x2F61AD, "maxps", "xmm1, xmm0"),
        (0x2F61B0, "movaps", "xmmword ptr [rcx], xmm1"),
        (0x2F6410, "mov", "dword ptr [rip + 0x37a6d6], 0x3ed10625"),
    )
    for address, mnemonic, operands in expected_instructions:
        require_instruction(decoded, address, mnemonic, operands)

    require(struct.unpack_from("<4I", data, 0x5AE780) == (0x3727C5AC,) * 4, "1e-5 floor bits")
    require(struct.unpack_from("<f", data, 0x5AE770)[0] == 100.0, "gain selector multiplier")
    first = struct.unpack_from("<4f", data, 0x5F2380)
    second = struct.unpack_from("<4f", data, 0x5F2390)
    # 0x2f6410 stores immediate bits 0x3ed10625 to matrix element 8.
    tail = struct.unpack("<f", struct.pack("<I", 0x3ED10625))[0]
    matrix = [
        [first[0], first[1], first[2]],
        [first[3], second[0], second[1]],
        [second[2], second[3], tail],
    ]
    expected_matrix_bits = (
        (0x3F13CD36, 0x3F13CD36, 0x3F13CD36),
        (0x3F350529, 0x00000000, 0xBF350529),
        (0x3ED10625, 0xBF510625, 0x3ED10625),
    )
    require(
        tuple(tuple(f32_bits(value) for value in row) for row in matrix)
        == expected_matrix_bits,
        "Ohta matrix bits",
    )

    cnr = load_module(
        "verify_cnr_public_origins_for_range_scale",
        ROOT / "tools/lldb_probes/denoise_route_census/verify_cnr_public_origins.py",
    )
    table, table_static = cnr.verify_static()
    require([row["gain"] for row in table] == list(range(100, 776, 25)), "installed gain rows")
    require(
        all(row["black"] == [42.0] * 3 and row["white"] == [1023.0] * 3 for row in table),
        "installed RGB black/white levels",
    )
    return {
        "libcp_sha256": digest,
        "body_hashes": {f"0x{start:x}..0x{end:x}": value for (start, end), value in BODY_HASHES.items()},
        "variance_floor": struct.unpack_from("<f", data, 0x5AE780)[0],
        "ohta_matrix": matrix,
        "installed_rgb_vst_table_sha256": table_static["installed_rgb_vst_table_json_sha256"],
        "installed_rgb_vst_rows": len(table),
    }


def verify_public_origins() -> dict[str, object]:
    awb = load_module(
        "verify_awb_public_origin_for_range_scale",
        ROOT / "tools/lldb_probes/awb_public_origin/verify_awb_public_origin.py",
    )
    awb.verify_static()
    public = awb.verify_lris()
    runtime = awb.verify_runtime(public, require_runtime=True)
    require(
        {"unit1_28mm", "unit1_35mm", "unit1_70mm", "unit1_150mm"} <= set(runtime),
        "four-focal reciprocal AWB runtime join",
    )

    captured = load_module(
        "verify_captured_public_fields_for_range_scale",
        ROOT / "tools/lldb_probes/capturedimage_f2770_origin/verify_public_capture_fields.py",
    )
    # This rechecks the direct CameraModule.sensor_analog_gain -> CapturedImage+0x40 join.
    captured.main()
    return {
        "neutral_rgb": "float32 reciprocal LightHeader.view_preferences.awb_gains.{r,g_r,b}",
        "gain_selector": "CapturedImage+0x40 = CameraModule.sensor_analog_gain",
        "awb_runtime_labels": sorted(runtime),
    }


def verify_runtime_scope() -> dict[str, object]:
    focal_counts = {}
    for label, path in FOCAL_REPORTS.items():
        report = json.loads(path.read_text())
        require(not report.get("errors"), f"{label}: helper liveness errors")
        require(report["process"]["exit_status"] == 0, f"{label}: helper run failed")
        count = report["counts"].get("call_0x2f4470_prebranch", 0)
        require(count >= 128, f"{label}: no accepted 0x2f4470 liveness window")
        focal_counts[label] = count

    config_floor_bits = f32_bits(0.0025)
    config_samples = {}
    for label, path in DENOISE_REPORTS.items():
        report = json.loads(path.read_text())
        require(not report.get("errors"), f"{label}: denoise route errors")
        samples = [item for item in report["samples"] if item["site"] == "helper_chain_0x2f53d0"]
        require(samples, f"{label}: missing 0x2f53d0 samples")
        for sample in samples:
            rcx_words = sample["packet"]["descriptors"]["rcx"]["i32"]
            require((rcx_words[6] & 0xFFFFFFFF) == config_floor_bits, f"{label}: config+0x18 floor")
        config_samples[label] = len(samples)

    selected = load_module(
        "verify_selected_bilateral_for_range_scale",
        ROOT / "tools/lldb_probes/selected_bilateral_formula/verify_selected_bilateral_formula.py",
    )
    selected.verify_static()
    final_samples = {}
    for label in ("unit1_35mm", "unit2_35mm"):
        report = json.loads((ROOT / f"runs/selected_bilateral_formula/{label}.json").read_text())
        results = selected.verify_report(label, report)
        require(results, f"{label}: missing selected bilateral samples")
        for sample in report["samples"]:
            vector = sample["range_scale_vec4"]["f32"]
            require(vector[0] >= f32(0.0025), f"{label}: I1 floor")
            require(vector[3] == 0.0, f"{label}: range-scale lane 3")
        final_samples[label] = len(results)
    return {
        "four_focal_0x2f4470_capped_counts": focal_counts,
        "config_floor": f32(0.0025),
        "config_sample_counts": config_samples,
        "selected_bilateral_samples": final_samples,
    }


def formula_record() -> dict[str, object]:
    return {
        "stage_1_rgb_sigma": [
            "inv_white = float32(1 / white)",
            "scale = neutral_rgb1 * float32(float32(white - black) * inv_white)",
            "offset = float32(black * inv_white)",
            "u = float32(source * scale + offset)",
            "sigma_rgb = sqrt(max(float32(1e-5), float32(u * installed_rgb_a + installed_rgb_b)))",
        ],
        "stage_2_ohta_sigma": [
            "variance[j] = sum_c(float32(sigma_rgb[c]^2) * float32(M[j][c]^2)) in installed SSE order",
            "range_scale = max((float32(0.0025),0,0,0), sqrt(variance))",
        ],
        "do_not_collapse": "Preserve the two sqrt/square stages and float32 operation order for parity.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = {
        "static": verify_static(),
        "public_origins": verify_public_origins(),
        "runtime_scope": verify_runtime_scope(),
        "formula": formula_record(),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        "selected_bilateral_range_scale=OK "
        f"libcp={result['static']['libcp_sha256']} "
        f"vst_rows={result['static']['installed_rgb_vst_rows']} "
        "scope=unit1_four_focal+unit2_35mm"
    )


if __name__ == "__main__":
    main()
