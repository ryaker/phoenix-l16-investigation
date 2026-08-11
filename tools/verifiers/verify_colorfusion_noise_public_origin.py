#!/usr/bin/env python3
"""Replay ColorFusion's target signal/noise provider from public LRI inputs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import argparse
import struct
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LIBCP = Path("/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib")
CASES = {
    "u1_28": {
        "lri": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        "lri_sha256": "2ac51af5c219639638ba34bb98975b62ee922331214043a938a7c37052700ff5",
        "camera_key": 0,
        "run": ROOT / "runs/colorfusion_f_runtime/u1_28_noise_signal_plane",
        "factor": ROOT / "runs/colorfusion_f_runtime/u1_28_transform/capture.json",
        "highlight": ROOT / "runs/colorfusion_f_runtime/u1_28_highlight_join",
    },
    "u2_70": {
        "lri": Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
        "lri_sha256": "780157dd7542c175554a4b1f024cc0f9eef98ef4172467c579143d02c0f89179",
        "camera_key": 8,
        "run": ROOT / "runs/colorfusion_f_runtime/u2_70_noise_signal_plane",
        "factor": ROOT / "runs/colorfusion_f_runtime/u2_70_transform/capture.json",
        "highlight": ROOT / "runs/colorfusion_f_runtime/u2_70_highlight_join",
        "hotpixel": ROOT / "runs/colorfusion_f_runtime/u2_70_hotpixel_lut",
    },
}
FLOW_PATH = ROOT / "tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_reference_public_origin.py"
HOT_PATH = ROOT / "tools/lldb_probes/prefusion_monofusion_flow_origin/diagnose_flow_source_hotpixel.py"
HOT_LUT_PATH = ROOT / "tools/lldb_probes/index5_guidance_channel_origin/verify_hot_pixel_formula.py"
CNR_PATH = ROOT / "tools/lldb_probes/denoise_route_census/verify_cnr_public_origins.py"
CCM_ORIGIN_PATH = ROOT / "tools/lldb_probes/ccm_chromaticity_origin/verify_ccm_chromaticity_origin.py"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
BODY_HASHES = {
    (0x1AA9A0, 0x1AAACB): "8d4c4019b32e9181feda30d7f54fcb69d0c4efd1bd5ec707f7039a58d21bbb40",
    (0x1AC010, 0x1AC3A3): "50e20e9a0d33bfeaf30ffcb9bbebe801f5338ef6b4066c474e9c0837811a99aa",
    (0x18E150, 0x18E56F): "65b6a41bccc5595dd99fb647f68343fa384d16a8a02eb00d55946d801f98e7ad",
    (0x18E5D0, 0x18E684): "4704b4d58a0947e84e0909854c8581f44ea597f63652c8544484c4cb4ba4a64e",
    (0x18E690, 0x18E763): "8756ccbfdd664751051ed7bc295b373777462306fb46ff05b8cc5b85bbdfd5f6",
    (0x1AC6C0, 0x1AC768): "3e5d70c7eb2aec18b66009d42ed2b23bca82cd5ef332ba92a8e5a77f534b8798",
    (0x350820, 0x35090B): "262c1a44e0c0b64b15ac1ee501b6dbe1728a2bee96c10373d4af9d1fad1678f3",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FLOW = load_module("cf_noise_flow", FLOW_PATH)
HOT = load_module("cf_noise_hot", HOT_PATH)
HOT_LUT = load_module("cf_noise_hot_lut", HOT_LUT_PATH)
CNR = load_module("cf_noise_cnr", CNR_PATH)
CCM_ORIGIN = load_module("cf_noise_ccm_origin", CCM_ORIGIN_PATH)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def f32(value) -> np.float32:
    return np.float32(value)


def x86_rcp(values: np.ndarray) -> np.ndarray:
    source = np.asarray(values, dtype=np.float32)
    words = source.view(np.uint32)
    sign = words & np.uint32(0x80000000)
    exponent = (words >> np.uint32(23)) & np.uint32(0xFF)
    fraction = words & np.uint32(0x007FFFFF)
    index = fraction >> np.uint32(12)
    denominator = np.uint64(4097) + np.uint64(2) * index.astype(np.uint64)
    quotient = (np.uint64(1 << 25) + denominator // np.uint64(2)) // denominator
    output_exponent = np.uint32(253) - exponent
    output_fraction = (quotient - np.uint64(4096)).astype(np.uint32) << np.uint32(11)
    output = sign | (output_exponent << np.uint32(23)) | output_fraction
    return output.view(np.float32)


def reduce_signal(source: np.ndarray) -> np.ndarray:
    reciprocal = x86_rcp(np.maximum(f32(0.1), source))
    # This is a fixed spatial order, not a semantic RGBG reorder. B4/BGGR is
    # the discriminator: its four captured planes remain TR, TL, BL, BR.
    lane_views = (
        reciprocal[0::2, 1::2],
        reciprocal[0::2, 0::2],
        reciprocal[1::2, 0::2],
        reciprocal[1::2, 1::2],
    )
    output = np.empty((195, 260, 4), dtype=np.float32)
    for lane, view in enumerate(lane_views):
        ordered = view.reshape(195, 8, 260, 8).transpose(0, 2, 1, 3).reshape(195, 260, 64)
        accumulator = np.zeros((195, 260), dtype=np.float32)
        for index in range(64):
            accumulator = np.add(accumulator, ordered[:, :, index], dtype=np.float32)
        output[:, :, lane] = np.multiply(accumulator, f32(1.0 / 256.0), dtype=np.float32)
    return output


def public_shading_plane(profile: np.ndarray, width: int, height: int) -> np.ndarray:
    step_x = f32(f32(width) / f32(profile.shape[1] - 1))
    step_y = f32(f32(height) / f32(profile.shape[0] - 1))
    floor_x = int(np.floor(step_x))
    floor_y = int(np.floor(step_y))
    inverse_x = f32(f32(1.0) / f32(floor_x))
    inverse_y = f32(f32(1.0) / f32(floor_y))
    boundaries_x = [int(np.floor(f32(gx) * step_x)) for gx in range(profile.shape[1])]
    boundaries_y = [int(np.floor(f32(gy) * step_y)) for gy in range(profile.shape[0])]
    output = np.empty((height, width), dtype=np.float32)
    for gy in range(profile.shape[0] - 1):
        y_end = boundaries_y[gy + 1] if gy + 1 < profile.shape[0] - 1 else height
        for y in range(boundaries_y[gy], y_end):
            local_y = f32(f32(y) - f32(f32(gy) * step_y))
            ty = f32(local_y * inverse_y)
            for gx in range(profile.shape[1] - 1):
                x_end = boundaries_x[gx + 1] if gx + 1 < profile.shape[1] - 1 else width
                tl = profile[gy, gx]
                tr = profile[gy, gx + 1]
                left = f32(f32(ty * f32(profile[gy + 1, gx] - tl)) + tl)
                right = f32(f32(ty * f32(profile[gy + 1, gx + 1] - tr)) + tr)
                slope = f32(f32(right - left) * inverse_x)
                for x in range(boundaries_x[gx], x_end):
                    local_x = f32(f32(x) - f32(f32(gx) * step_x))
                    # Installed x interpolation performs its visible multiply/add in binary64.
                    output[y, x] = f32(float(local_x) * float(slope) + float(left))
    return output


def sequential_mean(values: list[np.ndarray | np.float32]):
    require(bool(values), "empty provider neighborhood")
    total = f32(values[0])
    for value in values[1:]:
        total = np.add(total, value, dtype=np.float32)
    return np.divide(total, f32(len(values)), dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=sorted(CASES), default="u1_28")
    args = parser.parse_args()
    case = CASES[args.case]
    lri = case["lri"]
    run = case["run"]
    factor_capture = case["factor"]
    camera_key = case["camera_key"]
    data = LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == LIBCP_SHA256, "libcp drift")
    require(sha256(lri) == case["lri_sha256"], "LRI drift")
    for (start, end), expected in BODY_HASHES.items():
        require(hashlib.sha256(data[start:end]).hexdigest() == expected, f"body 0x{start:x} drift")
    require(struct.unpack("<f", data[0x5CBF70:0x5CBF74])[0] == f32(0.1), "signal floor")
    require(struct.unpack("<f", data[0x5AE780:0x5AE784])[0] == f32(1e-5), "variance floor")

    capture = json.loads((run / "capture.json").read_text(encoding="ascii"))
    require(capture["camera_key"] == camera_key, "target camera")
    source = np.memmap(run / capture["source"]["dump"]["file"], dtype="<f4", mode="r", shape=(3120, 4160))
    observed_signal = np.memmap(run / capture["output"]["dump"]["file"], dtype="<f4", mode="r", shape=(195, 260, 4))

    surface, packed, context = FLOW.find_surface(lri, camera_key)
    raw = FLOW.PUBLIC.unpack_raw10(packed, surface["row_stride"])
    red_phase = tuple(surface["sensor_bayer_red_override"])
    parsed = CNR.parse_lri(lri)
    gain = f32(parsed["modules"][camera_key]["sensor_analog_gain"])
    sections = CNR.static_helpers().macho_sections(data)
    rows = CNR.decode_installed_color_table(data, sections)
    selector = int(f32(gain * f32(100.0)))
    row = next(item for item in rows if item["gain"] >= selector)
    red_x, red_y = red_phase
    channels = tuple(
        "red" if (x, y) == (red_x, red_y)
        else "blue" if (x, y) == (1 - red_x, 1 - red_y)
        else "green"
        for x, y in ((0, 0), (1, 0), (0, 1), (1, 1))
    )
    luts = np.asarray([
        HOT_LUT.noise_lut(row[channel]["a"], row[channel]["b"],
                          row["black"][("red", "green", "blue").index(channel)],
                          row["white"][("red", "green", "blue").index(channel)],
                          row["cliff_slope"])
        for channel in channels
    ], dtype=np.float32)
    padded = HOT.bayer_median_halo(raw)
    phase_xor = red_x ^ red_y
    residual = HOT.residual_pass(padded, phase_xor, 2)
    corrected, markers = HOT.apply_isolated_bayer_halo(padded, raw, residual, luts, phase_xor, f32(4.0), 6)
    black = f32(42.0)
    highlight_capture = json.loads((case["highlight"] / "capture.json").read_text(encoding="ascii"))
    require(highlight_capture["phase"] == list(red_phase), "highlight phase")
    require(highlight_capture["black"] == 42.0 and highlight_capture["white"] == 1023.0,
            "highlight levels")
    color_records = CCM_ORIGIN.CCM.public_color_records(lri)
    awb = CCM_ORIGIN.AWB.parse_awb(lri)["gains"]
    color_arguments = [
        2855.63232421875,
        6502.08203125,
        *struct.unpack("<9f", color_records[(camera_key, 0)]["color_matrix"]),
        *struct.unpack("<9f", color_records[(camera_key, 2)]["color_matrix"]),
        awb["r"],
        awb["g_r"],
        awb["b"],
    ]
    public_color = CCM_ORIGIN.run_public_case(color_arguments)
    expected_highlight_bits = [
        int(public_color[f"scene_neutral_{channel}_bits"], 16)
        for channel in ("r", "g", "b")
    ]
    observed_highlight_bits = [
        int(word, 16) for word in highlight_capture["gain_vector_bits"][:3]
    ]
    require(expected_highlight_bits == observed_highlight_bits,
            "public AUTO temp/tint -> HighlightRestore gain")
    post_hotpixel = np.memmap(
        case["highlight"] / highlight_capture["source"]["dump"]["file"],
        dtype="<u2", mode="r", shape=(3120, 4160),
    )
    hotpixel_equal = corrected == post_hotpixel
    require(np.all(hotpixel_equal),
            f"public hot-pixel plane {int(hotpixel_equal.sum())}/{hotpixel_equal.size}")
    post_highlight = np.memmap(
        case["highlight"] / highlight_capture["destination"]["dump"]["file"],
        dtype="<u2", mode="r", shape=(3120, 4160),
    )
    expected_source = np.subtract(post_highlight.astype(np.float32), black, dtype=np.float32)
    source_equal = expected_source.view(np.uint32) == source.view(np.uint32)
    require(np.all(source_equal), f"public target plane {int(source_equal.sum())}/{source_equal.size}")

    if "hotpixel" in case:
        hotpixel_capture = json.loads((case["hotpixel"] / "capture.json").read_text(encoding="ascii"))
        require(hotpixel_capture["camera_key"] == camera_key, "hot-pixel target")
        require(hotpixel_capture["phase"] == list(red_phase), "hot-pixel phase")
        require(hotpixel_capture["threshold_multiplier"] == 1.0, "hot-pixel closure scale")
        for lane, item in enumerate(hotpixel_capture["luts"]):
            observed_lut = np.fromfile(case["hotpixel"] / item["file"], dtype="<f4")
            require(np.array_equal(luts[lane].view(np.uint32), observed_lut.view(np.uint32)),
                    f"hot-pixel LUT lane {lane}")

    rebuilt_signal = reduce_signal(source)
    signal_equal = rebuilt_signal.view(np.uint32) == observed_signal.view(np.uint32)
    require(np.all(signal_equal), f"signal reduction {int(signal_equal.sum())}/{signal_equal.size}")

    factor = json.loads(factor_capture.read_text(encoding="ascii"))
    provider = factor["noise_provider"]
    expected_a = np.asarray([row["red"]["a"], row["green"]["a"], row["blue"]["a"], row["green"]["a"]], dtype=np.float32)
    expected_b = np.asarray([row["red"]["b"], row["green"]["b"], row["blue"]["b"], row["green"]["b"]], dtype=np.float32)
    require(np.array_equal(expected_a.view(np.uint32), np.asarray(provider["model_a"]["float"], dtype=np.float32).view(np.uint32)), "model a")
    require(np.array_equal(expected_b.view(np.uint32), np.asarray(provider["model_b"]["float"], dtype=np.float32).view(np.uint32)), "model b")

    px, py = provider["patch_coordinate"]
    profile = FLOW.PUBLIC.selected_profile(lri, camera_key, surface["lens_position"])
    rebuilt_shading = public_shading_plane(profile, 260, 195)
    observed_shading = np.memmap(
        factor_capture.parent / provider["shading_descriptor_0xd0"]["dump"]["file"],
        dtype="<f4", mode="r", shape=(195, 260),
    )
    shading_equal = rebuilt_shading.view(np.uint32) == observed_shading.view(np.uint32)
    require(np.all(shading_equal), f"public shading plane {int(shading_equal.sum())}/{shading_equal.size}")
    coordinates = [
        (x, y) for y in (py, py + 1) for x in (px, px + 1)
        if 0 <= x < 260 and 0 <= y < 195
    ]
    shading_values = [rebuilt_shading[y, x] for x, y in coordinates]
    captured_shading = provider["shading_descriptor_0xd0"]["patch_neighborhood"]
    require([int(item["bits"][0], 16) for item in captured_shading] == [int(value.view(np.uint32)) for value in shading_values], "public shading neighborhood")
    h = sequential_mean(shading_values)
    d = sequential_mean([rebuilt_signal[y, x] for x, y in coordinates])
    inv_d = np.divide(f32(1.0), d, dtype=np.float32)
    variance = np.add(inv_d, black, dtype=np.float32)
    variance = np.multiply(variance, expected_a, dtype=np.float32)
    variance = np.multiply(variance, f32(1.0 / 1023.0), dtype=np.float32)
    variance = np.add(variance, expected_b, dtype=np.float32)
    variance = np.maximum(f32(1e-5), variance)
    noise = np.multiply(f32(h * h), variance, dtype=np.float32)
    noise = np.multiply(noise, f32(1023.0 * 1023.0), dtype=np.float32)
    observed_noise = np.asarray(factor["noise_factor_52c0"]["float"], dtype=np.float32)
    require(np.array_equal(noise.view(np.uint32), observed_noise.view(np.uint32)), "provider noise vector")
    product = np.multiply(noise, f32(8.0), dtype=np.float32)
    observed_product = np.asarray(factor["noise_product"]["float"], dtype=np.float32)
    require(np.array_equal(product.view(np.uint32), observed_product.view(np.uint32)), "core x8")

    print(f"colorfusion_noise_public_origin=PASS case={args.case} camera={camera_key} "
          f"source_words={source_equal.size} signal_words={signal_equal.size} "
          f"shading_words={shading_equal.size} "
          f"hot_pixels={int(np.count_nonzero(corrected != raw))} "
          f"highlight_pixels={int(np.count_nonzero(post_highlight != post_hotpixel))} "
          f"highlight_gain_bits={[hex(word) for word in expected_highlight_bits]} "
          f"patch=({px},{py}) "
          f"noise_bits={[hex(int(v)) for v in noise.view(np.uint32)]}")


if __name__ == "__main__":
    main()
