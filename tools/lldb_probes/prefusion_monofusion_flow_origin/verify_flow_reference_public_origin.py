#!/usr/bin/env python3
"""Verify MonoFusion's A1 flow reference from public LRI inputs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
DEFAULT_LRI = Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri")
DEFAULT_RUN = ROOT / "runs/prefusion_monofusion_flow_origin/unit1_28mm_reference_operand"
PUBLIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_guidance_channel_origin"
    / "verify_create_stereo_mono_public_reconstruction.py"
)
MONO_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_monofusion_worker"
    / "verify_monofusion_worker.py"
)
DEMOSAIC_PATH = (
    ROOT
    / "tools/lldb_probes/demosaic_light_v1"
    / "verify_demosaic_light_v1.py"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
WIDTH = 4160
HEIGHT = 3120
REFERENCE_KEY = 0
SOURCE_KEY = 1
RESPONSE = np.float32(2.3183400630950928)
RCP_981_BITS = 0x3A859800
LUT_VA = 0x5CC080
LUT_SHA256 = "ae826dc2c547e017d9f029f39cdd27901c84a16f1dcfd2fbbdc4de34447e71c1"
BODY_HASHES = {
    (0x1B17C0, 0x1B2730): "110546b1cb4417ed765e49562531481db1719479af577980f9cc3ade02710f23",
    (0x1ACBF0, 0x1AD370): "c6e3372baa424b6f54efda936c950b96991242294e862024bed7ef74055dcade",
    (0x1B5660, 0x1B5CE0): "354d7e2f6e70a471ac133fe24fb784f74a04c5ffb3796af7c43d6e0f54efef56",
    (0x1B5F60, 0x1B6330): "b0a00dd47c675684144c8f1c271ab14cc405bf570f4c6cf39ea50bce99e5698a",
    (0x18DD00, 0x18E050): "28ffb4a479ddad2924859a6f7420f48373b407a43fe8a45ce89bd5215ff20f8c",
    (0x1B6340, 0x1B6400): "1cb54973102208bb8de71f7cc380a8d7f37a4a44cc85a121f20555427cb4e079",
    (0xFC2F0, 0xFC450): "f18a50a3c483e05a5c861858709fa6a971088b3c6e16b856c7dbe45fbb07f913",
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


PUBLIC = load_module("flow_reference_public", PUBLIC_PATH)
MONO = load_module("flow_reference_mono", MONO_PATH)
DEMOSAIC = load_module("flow_reference_demosaic", DEMOSAIC_PATH)


def f32(value) -> np.float32:
    return np.float32(value)


def find_surface(path: Path, camera_key: int) -> tuple[dict, bytes, dict]:
    blocks = PUBLIC.RAW.lri.scan_lri_blocks(str(path))
    matches = []
    for block in blocks:
        for slot, module in enumerate(PUBLIC.fields(block["payload"], 12, 2)):
            if PUBLIC.RAW.one(module, 2, 0) != camera_key:
                continue
            surface = PUBLIC.RAW.one(module, 9, 2)
            size = PUBLIC.RAW.one(surface, 2, 2)
            red = PUBLIC.RAW.point2i(PUBLIC.RAW.one(module, 13, 2))
            matches.append(
                {
                    "block": block,
                    "slot": slot,
                    "module": module,
                    "camera_key": camera_key,
                    "lens_position": PUBLIC.RAW.one(module, 5, 0),
                    "sensor_bayer_red_override": list(red),
                    "width": PUBLIC.RAW.one(size, 1, 0),
                    "height": PUBLIC.RAW.one(size, 2, 0),
                    "format": PUBLIC.RAW.one(surface, 3, 0),
                    "row_stride": PUBLIC.RAW.one(surface, 4, 0),
                    "data_offset": PUBLIC.RAW.one(surface, 5, 0),
                }
            )
    require(len(matches) == 1, f"expected one camera-{camera_key} surface, got {len(matches)}")
    row = matches[0]
    require((row["width"], row["height"]) == (WIDTH, HEIGHT), "surface dimensions")
    require(row["format"] == 7 and row["row_stride"] == WIDTH * 5 // 4, "RAW10 layout")
    byte_count = row["row_stride"] * HEIGHT
    with path.open("rb") as handle:
        handle.seek(row["block"]["block_offset"] + row["data_offset"])
        packed = handle.read(byte_count)
    require(len(packed) == byte_count, "truncated public RAW10 surface")
    return row, packed, {"blocks": blocks}


def exact_words(actual: np.ndarray, expected: np.ndarray, label: str) -> int:
    require(actual.shape == expected.shape, f"{label}: shape mismatch")
    equal = actual.view(np.uint32) == expected.view(np.uint32)
    count = int(np.count_nonzero(equal))
    require(count == equal.size, f"{label}: {count}/{equal.size} exact float32 words")
    return count


def verify_static(data: bytes) -> tuple[np.ndarray, str]:
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"unexpected libcp SHA-256 {digest}")
    for (start, end), expected in BODY_HASHES.items():
        actual = hashlib.sha256(data[start:end]).hexdigest()
        require(actual == expected, f"installed body 0x{start:x}..0x{end:x} drift")
    # This independently pins every DemosaickLightV1 phase body and dispatch edge.
    DEMOSAIC.verify_static()
    raw_lut = data[LUT_VA : LUT_VA + 8192]
    require(hashlib.sha256(raw_lut).hexdigest() == LUT_SHA256, "sqrt LUT drift")
    lut = np.frombuffer(raw_lut, dtype="<u2")
    generated = np.asarray(
        [int(math.sqrt(index * 1023.0)) for index in range(4096)], dtype=np.uint16
    )
    require(np.array_equal(lut, generated), "sqrt LUT formula drift")
    return lut, digest


def verify(args) -> dict:
    data = args.libcp.read_bytes()
    lut, libcp_digest = verify_static(data)
    report = json.loads((args.run_dir / "report.json").read_text(encoding="ascii"))
    require(not report["errors"], f"runtime errors: {report['errors']}")
    require(report["demosaic_entry"] is not None, "missing DemosaickLightV1 entry")

    surface, packed, context = find_surface(args.lri, REFERENCE_KEY)
    raw = PUBLIC.unpack_raw10(packed, surface["row_stride"])
    black, white = PUBLIC.sensor_levels(context["blocks"])
    require((black, white) == (f32(42.0), f32(1023.0)), "public sensor levels")
    require(surface["sensor_bayer_red_override"] == [1, 0], "public A1 Bayer phase")

    demosaic = report["demosaic_entry"]
    require(demosaic["phase"] == surface["sensor_bayer_red_override"], "runtime/public phase")
    require(demosaic["gains"] == [1.0, 1.0, 1.0], "reference demosaic gains")
    require(
        demosaic["output"] == report["entries"][0]["source"]["address"],
        "DemosaickLightV1 output did not directly feed the luma helper",
    )
    observed_input = np.memmap(
        demosaic["source_dump"]["path"], dtype="<f4", mode="r", shape=(HEIGHT, WIDTH)
    )
    reciprocal = np.asarray([RCP_981_BITS], dtype=np.uint32).view(np.float32)[0]
    normalized = np.multiply(
        np.subtract(raw.astype(np.float32), black, dtype=np.float32),
        reciprocal,
        dtype=np.float32,
    )
    normalized_exact = exact_words(normalized, observed_input, "public A1 RAW normalization")

    source = np.memmap(
        report["entries"][0]["source_dump"]["path"],
        dtype="<f4",
        mode="r",
        shape=(HEIGHT, WIDTH, 4),
    )
    observed_scalar = np.memmap(
        report["returns"][0]["output_dump"]["path"],
        dtype="<f4",
        mode="r",
        shape=(HEIGHT, WIDTH),
    )
    weights = np.asarray(report["entries"][0]["weights"], dtype=np.float32)
    expected_weights = np.asarray(
        [0.2155500054359436, 0.43230700492858887, 0.35214298963546753, 0.0],
        dtype=np.float32,
    )
    require(np.array_equal(weights.view(np.uint32), expected_weights.view(np.uint32)), "response weights")
    dynamic_range = f32(white - black)
    require(f32(report["entries"][0]["scalar"]) == dynamic_range, "luma scalar")
    scalar_exact = 0
    scalar_hash = hashlib.sha256()
    for y0 in range(0, HEIGHT, 64):
        y1 = min(y0 + 64, HEIGHT)
        rb = np.add(
            np.multiply(source[y0:y1, :, 0], weights[0], dtype=np.float32),
            np.multiply(source[y0:y1, :, 2], weights[2], dtype=np.float32),
            dtype=np.float32,
        )
        ga = np.add(
            np.multiply(source[y0:y1, :, 1], weights[1], dtype=np.float32),
            np.multiply(source[y0:y1, :, 3], weights[3], dtype=np.float32),
            dtype=np.float32,
        )
        rebuilt = np.multiply(np.add(rb, ga, dtype=np.float32), dynamic_range, dtype=np.float32)
        scalar_exact += int(
            np.count_nonzero(rebuilt.view(np.uint32) == observed_scalar[y0:y1].view(np.uint32))
        )
        scalar_hash.update(rebuilt.tobytes())
    require(scalar_exact == WIDTH * HEIGHT, f"luma projection: {scalar_exact} exact")
    require(
        scalar_hash.hexdigest() == report["returns"][0]["output_dump"]["sha256"],
        "luma projection SHA",
    )

    public = MONO.decode_lri(args.lri)
    target = public["target"]
    source_capture = public["source"]
    target_energy = f32(f32(float(target["sensor_exposure"])) * f32(target["sensor_analog_gain"]))
    source_energy = f32(
        f32(float(source_capture["sensor_exposure"]))
        * f32(source_capture["sensor_analog_gain"])
    )
    exposure_ratio = f32(target_energy / source_energy)
    reference_scale = f32(RESPONSE / exposure_ratio)
    observed_scale = f32(report["affine_entries"][0]["scale"])
    require(reference_scale.view(np.uint32) == observed_scale.view(np.uint32), "reference scale origin")
    require(f32(report["affine_entries"][0]["cap"]) == dynamic_range, "affine cap")
    observed_affine = np.memmap(
        report["affine_returns"][0]["output_dump"]["path"],
        dtype="<f4",
        mode="r",
        shape=(HEIGHT, WIDTH),
    )
    rebuilt_affine = np.minimum(
        np.multiply(observed_scalar, reference_scale, dtype=np.float32), dynamic_range
    )
    affine_exact = exact_words(rebuilt_affine, observed_affine, "reference affine")

    profile = PUBLIC.selected_profile(args.lri, REFERENCE_KEY, surface["lens_position"])
    shading = PUBLIC.vignetting_plane(profile)
    vignetted = np.multiply(observed_affine, shading, dtype=np.float32)
    indices = np.trunc(np.add(vignetted, f32(0.5), dtype=np.float32)).astype(np.int32)
    np.clip(indices, 1, 4095, out=indices)
    rebuilt_u16 = lut[indices]
    observed_u16 = np.memmap(
        report["final_reference"]["level0_dump"]["path"],
        dtype="<u2",
        mode="r",
        shape=(HEIGHT, WIDTH),
    )
    final_exact = int(np.count_nonzero(rebuilt_u16 == observed_u16))
    require(final_exact == WIDTH * HEIGHT, f"final reference: {final_exact} exact")
    final_sha = hashlib.sha256(rebuilt_u16.tobytes()).hexdigest()
    require(final_sha == report["final_reference"]["level0_dump"]["sha256"], "final reference SHA")

    calibration_order = list(PUBLIC.VIGNETTING.decode_modules(args.lri))
    require(len(calibration_order) > REFERENCE_KEY, "missing A1 calibration vector slot")
    return {
        "libcp_sha256": libcp_digest,
        "source_lri": str(args.lri),
        "public_camera": "A1",
        "public_fields": [
            "CameraModule.sensor_data_surface",
            "CameraModule.sensor_bayer_red_override",
            "CameraModule.lens_position",
            "CameraModule.sensor_exposure",
            "CameraModule.sensor_analog_gain",
            "SensorCharacterization.black_level",
            "SensorCharacterization.white_level",
            "VignettingCharacterization.vignetting",
        ],
        "raw10_sha256": hashlib.sha256(packed).hexdigest(),
        "raw_normalization_reciprocal_bits": f"0x{RCP_981_BITS:08x}",
        "raw_normalization_exact": normalized_exact,
        "demosaic": "DemosaickLightV1 GRBG, gains=(1,1,1)",
        "demosaic_output_sha256": report["entries"][0]["source_dump"]["sha256"],
        "luma_weights": weights.tolist(),
        "luma_exact": scalar_exact,
        "exposure_ratio": float(exposure_ratio),
        "reference_scale": float(reference_scale),
        "reference_scale_bits": f"0x{int(reference_scale.view(np.uint32)):08x}",
        "affine_exact": affine_exact,
        "vignetting_calibration_index": REFERENCE_KEY,
        "vignetting_camera_id": calibration_order[REFERENCE_KEY],
        "vignetting_grid_sha256": hashlib.sha256(profile.tobytes()).hexdigest(),
        "sqrt_lut_sha256": LUT_SHA256,
        "final_exact": final_exact,
        "final_sha256": final_sha,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=LIBCP)
    parser.add_argument("--lri", type=Path, default=DEFAULT_LRI)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = verify(args)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        "flow_reference_public_origin=OK",
        f"raw={result['raw_normalization_exact']}/{WIDTH * HEIGHT}",
        f"luma={result['luma_exact']}/{WIDTH * HEIGHT}",
        f"affine={result['affine_exact']}/{WIDTH * HEIGHT}",
        f"final={result['final_exact']}/{WIDTH * HEIGHT}",
        f"phase={result['demosaic']}",
        f"scale={result['reference_scale']}",
        f"sha256={result['final_sha256']}",
    )


if __name__ == "__main__":
    main()
