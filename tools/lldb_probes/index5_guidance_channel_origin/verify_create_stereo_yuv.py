#!/usr/bin/env python3
"""Bit-verify CreateStereoImage's inlined ConvertToYUV color stage."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

import numpy as np
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
AWB_PATH = ROOT / "tools/lldb_probes/awb_public_origin/verify_awb_public_origin.py"
LRI_ROLES_PATH = (
    ROOT
    / "tools/lldb_probes/lri_consumed_block_roles"
    / "verify_lri_consumed_block_roles.py"
)
CALIBRATION_PATH = ROOT / "tools/validation/verify_new_lri_calibration_corpus.py"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
CONVERT_FUNC_TYPE_VA = 0x5DB7E0
CONVERT_VTABLE = 0x659020
CONVERT_WORKER = 0x27CE60
EXPECTED_TYPE = (
    "NSt3__110__function6__funcIZN2lt9StereoISP12ConvertToYUVERKNS2_5Image"
    "INS2_8vec4x32fEEERKNS2_6MatrixIfLi4ELi4ELb1EEEE3$_0NS_9allocatorISD_EE"
    "FvRKNS2_9RectangleIiEEiEEE"
)
DEFAULT_RUNS = (
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_color_unit1_28mm",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_color_l16_06689",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_color_unit2_28mm",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("create_stereo_yuv_static", STATIC_PATH)
AWB = load_module("create_stereo_yuv_awb", AWB_PATH)
LRI_ROLES = load_module("create_stereo_yuv_lri_roles", LRI_ROLES_PATH)
CALIBRATION = load_module("create_stereo_yuv_calibration", CALIBRATION_PATH)


def f32(value) -> np.float32:
    return np.float32(value)


def f32_from_bits(bits: int) -> np.float32:
    return np.asarray([bits], dtype="<u4").view("<f4")[0]


def bits(value: np.float32) -> int:
    return int(np.asarray([value], dtype="<f4").view("<u4")[0])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def verify_static() -> dict:
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")
    require(
        STATIC.cstring(data, mapping, CONVERT_FUNC_TYPE_VA).decode("ascii")
        == EXPECTED_TYPE,
        "ConvertToYUV function-object RTTI changed",
    )
    require(
        STATIC.u64(STATIC.bytes_at(data, mapping, CONVERT_VTABLE + 0x30, 8))
        == CONVERT_WORKER,
        "CreateStereoImage ConvertToYUV callback worker changed",
    )
    require(
        STATIC.rip_target(STATIC.instruction(data, mapping, 0x27AE49))
        == CONVERT_VTABLE,
        "ConvertToYUV callback vtable construction changed",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x27BFF0))
        == 0x27ADC0,
        "CreateStereoImage ConvertToYUV call changed",
    )
    LRI_ROLES.descriptor_map()

    constants = {
        0x5A81F0: 0x7FFFFFFF,
        0x5A8890: 0x437F0000,
        0x5A8910: 0x007FFFFF,
        0x5A8920: 0x3F800000,
        0x5A8930: 0x3E511AF3,
        0x5A8940: 0xBFA05375,
        0x5A8950: 0xC0800000,
        0x5A8960: 0x40552F75,
        0x5A8970: 0xC0121769,
        0x5A8990: 0xC2FC0000,
        0x5A89A0: 0x43000000,
        0x5A89B0: 0x3D9FCB52,
        0x5A89C0: 0x3E677E26,
        0x5A89D0: 0x3F322226,
        0x5A89E0: 0x3F7FFB19,
        0x5AAF90: 0x3EE8BA2E,
    }
    for va, expected in constants.items():
        actual = STATIC.u32(STATIC.bytes_at(data, mapping, va, 4))
        require(actual == expected, f"constant at 0x{va:x}: 0x{actual:08x}")
    require(
        STATIC.bytes_at(data, mapping, 0x5DB380, 16)
        == struct.pack("<4f", 0.0, 128.0, 128.0, 0.0),
        "YUV offset initializer changed",
    )

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    windows = {
        (0x27B82D, 0x27B987): None,
        (0x27BFDB, 0x27C1E5): None,
        (0x27CE60, 0x27D0C8): None,
    }
    for start, end in windows:
        blob = STATIC.bytes_at(data, mapping, start, end - start)
        require(sum(item.size for item in decoder.disasm(blob, start)) == len(blob),
                f"static window does not disassemble at 0x{start:x}")
        windows[(start, end)] = hashlib.sha256(blob).hexdigest()
    return {"libcp_sha256": digest, "window_sha256": windows}


def build_matrix(sensor_response: np.ndarray, neutral: np.ndarray) -> np.ndarray:
    a, b, c = (f32(value) for value in sensor_response[:3])
    pr, pg, pb = (f32(value) for value in neutral[:3])
    neg_b = f32_from_bits(bits(b) ^ 0x80000000)
    total = f32(c + a)
    neg_b2 = f32(b * neg_b)
    y1 = f32(f32(c - a) * neg_b)
    inv_g = f32(f32(1.0) / pg)
    y1 = f32(y1 * inv_g)
    middle = f32(total * inv_g)
    c_total = f32(total * c)
    a_total = f32(total * a)
    z1 = f32(a_total - neg_b2)
    x1 = f32(neg_b2 - c_total)
    inv_r = f32(f32(1.0) / pr)
    x1 = f32(x1 * inv_r)
    inv_b = f32(f32(1.0) / pb)
    z1 = f32(z1 * inv_b)
    x2 = f32(inv_r * neg_b)
    z2 = f32(inv_b * neg_b)

    norm_w = f32(np.sqrt(f32(f32(a * a) + f32(b * b) + f32(c * c))))
    norm_1 = f32(np.sqrt(f32(f32(x1 * x1) + f32(y1 * y1) + f32(z1 * z1))))
    scale_1 = f32(norm_w / norm_1)
    row_1 = np.asarray(
        [f32(x1 * scale_1), f32(y1 * scale_1), f32(z1 * scale_1), f32(0)],
        dtype="<f4",
    )
    norm_2 = f32(np.sqrt(f32(f32(x2 * x2) + f32(middle * middle) + f32(z2 * z2))))
    scale_2 = f32(norm_w / norm_2)
    row_2 = np.asarray(
        [f32(x2 * scale_2), f32(middle * scale_2), f32(z2 * scale_2), f32(0)],
        dtype="<f4",
    )
    return np.vstack(
        (
            np.asarray([a, b, c, f32(0)], dtype="<f4"),
            row_1,
            row_2,
            np.zeros(4, dtype="<f4"),
        )
    )


def fast_power_yuv(products: np.ndarray, offset: np.ndarray) -> np.ndarray:
    values = np.asarray(products, dtype="<f4")
    value_bits = values.view("<u4")
    doubled = value_bits + np.uint32(value_bits)
    absolute_bits = value_bits & np.uint32(0x7FFFFFFF)
    sign_bits = (value_bits ^ absolute_bits) | np.uint32(0x3F800000)
    sign = sign_bits.view("<f4").copy()
    sign[doubled == 0] = f32(0)

    mantissa_bits = (value_bits & np.uint32(0x007FFFFF)) | np.uint32(0x3F800000)
    mantissa = mantissa_bits.view("<f4")
    poly = f32(mantissa * f32_from_bits(0x3E511AF3))
    poly = f32(poly + f32_from_bits(0xBFA05375))
    exponent_bits = absolute_bits + np.uint32(0xC0800000)
    exponent = (exponent_bits.view("<i4") >> np.int32(23)).astype("<f4")
    poly = f32(poly * mantissa)
    poly = f32(poly + f32_from_bits(0x40552F75))
    poly = f32(poly * mantissa)
    y = f32(exponent + f32_from_bits(0xC0121769))
    y = f32(y + poly)
    y = f32(y * f32_from_bits(0x3EE8BA2E))
    y = np.maximum(y, f32_from_bits(0xC2FC0000)).astype("<f4")
    y = np.minimum(y, f32_from_bits(0x43000000)).astype("<f4")

    truncated = np.trunc(y).astype("<i4")
    floor_i = truncated + (y.view("<i4") >> np.int32(31))
    fraction = f32(y - floor_i.astype("<f4"))
    exp_poly = f32(fraction * f32_from_bits(0x3D9FCB52))
    exp_poly = f32(exp_poly + f32_from_bits(0x3E677E26))
    exp_poly = f32(exp_poly * fraction)
    exp_poly = f32(exp_poly + f32_from_bits(0x3F322226))
    exp_poly = f32(exp_poly * fraction)
    exp_poly = f32(exp_poly + f32_from_bits(0x3F7FFB19))
    power_bits = (floor_i.astype("<u4") << np.uint32(23)) + exp_poly.view("<u4")
    result = f32(sign * f32_from_bits(0x437F0000))
    result = f32(result * power_bits.view("<f4"))
    result = f32(result + offset)
    result[:, 3] = f32(1)
    return result


def convert_chunk(source: np.ndarray, matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    # This order is the exact 0x27cf78..0x27cfbe SSE accumulation order.
    product = f32(source[:, 3:4] * matrix[:, 3])
    product = f32(product + f32(source[:, 2:3] * matrix[:, 2]))
    product = f32(product + f32(source[:, 0:1] * matrix[:, 0]))
    product = f32(product + f32(source[:, 1:2] * matrix[:, 1]))
    return fast_power_yuv(product, offset)


def verify_run(run_dir: Path) -> dict:
    report = json.loads((run_dir / "report.json").read_text(encoding="ascii"))
    require(not report["errors"], f"{run_dir}: capture errors {report['errors']}")
    require(report["terminated_after_capture"], f"{run_dir}: incomplete capture")
    callback = report["color_callback"]
    require(callback["vtable_va"] == CONVERT_VTABLE, f"{run_dir}: callback vtable")
    require(callback["worker_va"] == CONVERT_WORKER, f"{run_dir}: callback worker")
    require(callback["yuv_offset"] == [0.0, 128.0, 128.0, 0.0], f"{run_dir}: offset")
    require(report["entry"]["sensor_type"] == 2, f"{run_dir}: expected SENSOR_AR1335(2)")
    source_lri = Path(report["source_lri"])
    require(source_lri.is_file(), f"{run_dir}: source LRI is unavailable")
    awb_packet = AWB.parse_awb(source_lri)
    gains = awb_packet["gains"]
    require(awb_packet["mode"] == 0, f"{run_dir}: expected AWB_MODE_AUTO")
    require(gains["g_r"] == gains["g_b"], f"{run_dir}: unequal public green gains")
    expected_neutral = np.asarray(
        [f32(1.0 / gains["r"]), f32(1.0 / gains["g_r"]), f32(1.0 / gains["b"])],
        dtype="<f4",
    )
    sensor_packets = [
        CALIBRATION.sensor_characterization(block["payload"])
        for block in CALIBRATION.scan_lri_blocks(str(source_lri))
        if CALIBRATION.calibration_role(block["payload"]) == "sensor_characterization"
    ]
    require(len(sensor_packets) == 1, f"{run_dir}: expected one public SensorData packet")
    require(
        sensor_packets[0]["sensor_type"] == report["entry"]["sensor_type"],
        f"{run_dir}: public SensorData.type join mismatch",
    )

    pre_path = run_dir / "pre_color.rgba32f"
    post_path = run_dir / "post_color.rgba32f"
    packed_path = run_dir / "packed_u8.rgba8"
    require(sha256(pre_path) == report["pre_color"]["artifact"]["sha256"], f"{run_dir}: pre SHA")
    require(sha256(post_path) == report["post_color"]["artifact"]["sha256"], f"{run_dir}: post SHA")
    require(sha256(packed_path) == report["packed_u8"]["artifact"]["sha256"], f"{run_dir}: packed SHA")
    observed_matrix = np.frombuffer(
        bytes.fromhex(report["pre_color"]["matrix_raw"]), dtype="<f4"
    ).reshape(4, 4)
    neutral = np.asarray(report["entry"]["neutral_color"], dtype="<f4")
    require(
        np.array_equal(neutral.view("<u4"), expected_neutral.view("<u4")),
        f"{run_dir}: public AWB reciprocal join mismatch",
    )
    rebuilt_matrix = build_matrix(observed_matrix[0], neutral)
    require(
        np.array_equal(rebuilt_matrix.view("<u4"), observed_matrix.view("<u4")),
        f"{run_dir}: matrix reconstruction mismatch",
    )

    descriptor = report["pre_color"]["descriptor"]
    pixels = int(descriptor["size"][0]) * int(descriptor["size"][1])
    require(pre_path.stat().st_size == pixels * 16, f"{run_dir}: pre size")
    require(post_path.stat().st_size == pixels * 16, f"{run_dir}: post size")
    require(packed_path.stat().st_size == pixels * 4, f"{run_dir}: packed size")
    source = np.memmap(pre_path, mode="r", dtype="<f4", shape=(pixels, 4))
    observed = np.memmap(post_path, mode="r", dtype="<f4", shape=(pixels, 4))
    packed = np.memmap(packed_path, mode="r", dtype="u1", shape=(pixels, 4))
    offset = np.asarray(callback["yuv_offset"], dtype="<f4")
    mismatches = 0
    first_mismatch = None
    packed_mismatches = 0
    first_packed_mismatch = None
    for start in range(0, pixels, 131072):
        end = min(start + 131072, pixels)
        rebuilt = convert_chunk(np.asarray(source[start:end]), observed_matrix, offset)
        unequal = rebuilt.view("<u4") != np.asarray(observed[start:end]).view("<u4")
        count = int(np.count_nonzero(unequal))
        mismatches += count
        if count and first_mismatch is None:
            local = np.argwhere(unequal)[0]
            first_mismatch = [start + int(local[0]), int(local[1])]
        rebuilt_packed = np.clip(np.rint(np.asarray(observed[start:end])), 0, 255).astype("u1")
        packed_unequal = rebuilt_packed != np.asarray(packed[start:end])
        packed_count = int(np.count_nonzero(packed_unequal))
        packed_mismatches += packed_count
        if packed_count and first_packed_mismatch is None:
            local = np.argwhere(packed_unequal)[0]
            first_packed_mismatch = [start + int(local[0]), int(local[1])]
    require(mismatches == 0, f"{run_dir}: {mismatches} word mismatches, first={first_mismatch}")
    require(
        packed_mismatches == 0,
        f"{run_dir}: {packed_mismatches} packed-byte mismatches, first={first_packed_mismatch}",
    )
    return {
        "label": report["label"],
        "sensor_type": report["entry"]["sensor_type"],
        "public_sensor_type": "SENSOR_AR1335(2)",
        "neutral_color": report["entry"]["neutral_color"],
        "public_awb_gains": gains,
        "source_lri": str(source_lri),
        "sensor_response": observed_matrix[0, :3].tolist(),
        "matrix_words_exact": 16,
        "pixel_words_exact": pixels * 4,
        "packed_bytes_exact": pixels * 4,
        "pre_sha256": report["pre_color"]["artifact"]["sha256"],
        "post_sha256": report["post_color"]["artifact"]["sha256"],
        "packed_sha256": report["packed_u8"]["artifact"]["sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dirs", nargs="*", type=Path)
    args = parser.parse_args()
    static = verify_static()
    print(f"static_create_stereo_yuv=OK libcp={static['libcp_sha256']}")
    for run_dir in (args.run_dirs or DEFAULT_RUNS):
        result = verify_run(run_dir)
        print("create_stereo_yuv=OK " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
