#!/usr/bin/env python3
"""Verify the public calibration-to-live editor color-correction join."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/editor_render_type_topology"
CAL = ROOT / "runs/editor_color_calibration"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def alpha_for(scene: float, lower: float, upper: float) -> float:
    upper_reciprocal = f32(f32(1.0) / f32(upper))
    lower_reciprocal = f32(f32(1.0) / f32(lower))
    numerator = (1.0 / float(f32(scene))) - float(upper_reciprocal)
    denominator = float(f32(lower_reciprocal - upper_reciprocal))
    return f32(numerator / denominator)


def matrix_alpha_for(scene: float, lower: float, upper: float) -> float:
    scene_mired = f32(f32(1.0) / f32(scene))
    lower_mired = f32(f32(1.0) / f32(lower))
    upper_mired = f32(f32(1.0) / f32(upper))
    return f32(f32(scene_mired - upper_mired) / f32(lower_mired - upper_mired))


def interpolate(upper: bytes, lower: bytes, alpha: float) -> bytes:
    require(len(upper) == len(lower) == 1089 * 16, "endpoint map size")
    one_minus = f32(f32(1.0) - alpha)
    output = []
    for (upper_value,), (lower_value,) in zip(
        struct.iter_unpack("<f", upper), struct.iter_unpack("<f", lower)
    ):
        output.append(
            f32(f32(upper_value * one_minus) + f32(lower_value * alpha))
        )
    return struct.pack("<%df" % len(output), *output)


def main() -> None:
    reference_table = RUN / "macbeth_reference_table_f32.raw"
    optimizer_target = RUN / "macbeth_optimizer_target_f32.raw"
    require(reference_table.stat().st_size == optimizer_target.stat().st_size == 24 * 12, "optimizer table sizes")
    require(sha256(reference_table) == "ec37cf355a4aa2204cdc579be0c2952529a51a47b37e82ed24202bcaa2763c81", "embedded Macbeth table")
    require(sha256(optimizer_target) == "776d05c0ad42aa6d0c557c3037bdc9e1e260995a25bfe9d1b2e054101fb73d86", "converted optimizer target")
    optimizer_roundtrip = RUN / "macbeth_optimizer_roundtrip_xyz_f32.raw"
    require(
        sha256(optimizer_roundtrip)
        == "3fec8ca91fd4710c9311f3f92dc82fd42dbc68832b390e81518032b44296b77e",
        "optimizer round-trip XYZ target",
    )

    owner = (RUN / "color_correction_owner_0x200.raw").read_bytes()
    require(len(owner) == 0x200, "owner snapshot size")
    xy = struct.unpack_from("<2f", owner, 0x0C)
    require(
        tuple(struct.unpack_from("<2I", owner, 0x0C)) == (0x3EB160B2, 0x3EB4BC02),
        "live scene chromaticity words",
    )
    lower_cct, upper_cct = struct.unpack_from("<2f", owner, 0xA8)
    require((lower_cct, upper_cct) == (2855.63232421875, 6502.08203125), "endpoint CCTs")

    cct_report = json.loads((RUN / "color_correction_cct.json").read_text())
    require(cct_report["xy_words"] == ["0x3eb160b2", "0x3eb4bc02"], "CCT xy join")
    require(cct_report["cct_word"] == "0x459acd49", "scene CCT word")
    require(cct_report["converter_0_to_5"] == "0xab940", "selected converter")
    scene_cct = cct_report["cct"]
    alpha = alpha_for(scene_cct, lower_cct, upper_cct)
    alpha_word = struct.unpack("<I", struct.pack("<f", alpha))[0]
    require(alpha_word == 0x3E7AAA6B, "map interpolation alpha")
    matrix_alpha = matrix_alpha_for(scene_cct, lower_cct, upper_cct)
    matrix_alpha_word = struct.unpack("<I", struct.pack("<f", matrix_alpha))[0]
    require(matrix_alpha_word == 0x3E7AAA6D, "matrix interpolation alpha")

    input_config = (RUN / "color_correction_input_config.raw").read_bytes()
    output_config = (RUN / "color_correction_output_config.raw").read_bytes()
    require(len(input_config) == len(output_config) == 52, "color config sizes")
    require(struct.unpack_from("<I", input_config, 0x30)[0] == 0, "input selector")
    require(struct.unpack_from("<I", output_config, 0x30)[0] == 5, "output selector")
    require(input_config[0x24:0x2C] == output_config[0x24:0x2C], "equal D50 whites")
    require(
        struct.unpack_from("<2I", output_config, 0x24) == (0x3EB0FB8D, 0x3EB78CD0),
        "D50 white words",
    )

    map_manifest = json.loads((CAL / "photo_exact_hsv_map_manifest.json").read_text())
    records = {
        (item["body"], item["camera_id"], item["illuminant_type"]): item
        for item in map_manifest["results"]
    }
    lower = records[("unit1", 0, 0)]
    upper = records[("unit1", 0, 2)]
    expected_optimizer_words = [
        "0x3f3690a4", "0x3e9137dd", "0x3e32f2ec",
        "0x3dc9b39a", "0x3f90a205", "0xbef76e1b",
        "0xbeaee203", "0xbf5679ea", "0x40843ad5",
    ]
    require(lower["optimizer_matrix_words"] == expected_optimizer_words, "installed optimizer matrix words")

    cleanroom = json.loads((RUN / "cleanroom_macbeth_optimizer.json").read_text())
    require(cleanroom["matrix_row_major_f32_words"] == expected_optimizer_words, "clean-room optimizer matrix words")
    require(cleanroom["wrapper_matrix_words"] == lower["matrix_words"], "clean-room white-normalized wrapper matrix")
    capture = json.loads((RUN / "ceres_solve_capture.json").read_text())
    require(capture["options"] == {
        "minimizer_type": 0,
        "line_search_direction_type": 3,
        "line_search_type": 1,
        "linear_solver_type": 1,
        "max_num_iterations": 2000,
        "function_tolerance": 1e-10,
        "gradient_tolerance": 1.0000000000000002e-14,
        "parameter_tolerance": 1e-8,
        "num_threads": 1,
    }, "captured Ceres options")
    require(capture["iterations"] == cleanroom["iterations"] == 15, "matching Ceres iteration count")
    require(abs(capture["initial_cost"] - cleanroom["initial_cost"]) < 6e-12, "matching initial cost")
    require(abs(capture["final_cost"] - cleanroom["final_cost"]) < 2e-12, "matching final cost")
    require(
        max(abs(a - b) for a, b in zip(capture["before"], cleanroom["seed_column_major"])) < 1e-13,
        "matching least-squares seed",
    )
    require(
        max(abs(a - b) for a, b in zip(capture["after"], cleanroom["matrix_column_major"])) < 2e-14,
        "matching optimized doubles",
    )
    ciede_installed = json.loads((RUN / "ciede2000_probe.json").read_text())
    require(
        max(
            abs(item["value"] - expected)
            for item, expected in zip(ciede_installed["pairs"], cleanroom["ciede_test_values"])
        ) < 4e-14,
        "clean-room CIEDE2000 helper",
    )
    require(lower["matrix_words"] == [
        "0x%08x" % word for word in struct.unpack_from("<9I", owner, 0x100)
    ], "camera-0 A optimizer matrix")
    require(upper["matrix_words"] == [
        "0x%08x" % word for word in struct.unpack_from("<9I", owner, 0x124)
    ], "camera-0 D65 optimizer matrix")

    endpoint_lower = Path(lower["map_path"]).read_bytes()
    endpoint_upper = Path(upper["map_path"]).read_bytes()
    live_map = (RUN / "color_correction_hsv_map_vec4_f32.raw").read_bytes()
    predicted_map = interpolate(endpoint_upper, endpoint_lower, alpha)
    require(predicted_map == live_map, "public camera-0 map must match live map exactly")
    matching_cameras = []
    for camera_id in sorted({key[1] for key in records if key[0] == "unit1"}):
        candidate = interpolate(
            Path(records[("unit1", camera_id, 2)]["map_path"]).read_bytes(),
            Path(records[("unit1", camera_id, 0)]["map_path"]).read_bytes(),
            alpha,
        )
        if candidate == live_map:
            matching_cameras.append(camera_id)
    require(matching_cameras == [0], f"unique live camera match: {matching_cameras}")

    lower_matrix = struct.unpack_from("<9f", owner, 0x100)
    upper_matrix = struct.unpack_from("<9f", owner, 0x124)
    expected_destination = tuple(
        f32(upper_value + f32(matrix_alpha * f32(lower_value - upper_value)))
        for upper_value, lower_value in zip(upper_matrix, lower_matrix)
    )
    require(
        struct.pack("<9f", *expected_destination) == input_config[:36],
        "public optimizer matrix interpolation to input config",
    )

    macbeth = json.loads((CAL / "photo_exact_macbeth_manifest.json").read_text())
    require(macbeth["schema"] == {
        "field": 6,
        "message": "ltpb.ColorCalibration",
        "name": "macbeth_data",
        "type": "repeated ltpb.Point3F",
    }, "public Macbeth schema")
    require([body["record_count"] for body in macbeth["bodies"]] == [42, 42], "two-body record counts")
    body_records = [
        {(item["camera_id"], item["illuminant_type"]): item for item in body["records"]}
        for body in macbeth["bodies"]
    ]
    cross_body_equal = sum(
        body_records[0][key]["raw_sha256"] == body_records[1][key]["raw_sha256"]
        for key in body_records[0]
    )
    require(cross_body_equal == 0, "body-specific Macbeth calibration")

    replay = subprocess.run(
        [
            str(RUN / "replay_color_correction"),
            str(RUN / "stage_images/display_stage_03_340f70.raw"),
            str(RUN / "color_correction_hsv_map_vec4_f32.raw"),
            str(RUN / "stage_images/display_stage_10_347680.raw"),
            str(RUN / "color_correction_input_config.raw"),
            str(RUN / "color_correction_output_config.raw"),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    require("different_bytes=0" in replay.stdout, "full clean-room replay")
    require(
        sha256(RUN / "stage_images/display_stage_10_347680.raw")
        == "b31fb9f69c40b73d94bc5aade11411f644d61ce7fbc1b7e4c1c8aa9386115927",
        "retained stage-10 hash",
    )

    report = {
        "scope": "Unit-1 28mm default level-4 display index 10",
        "photo_sha256": macbeth["bodies"][0]["calibration_sha256"],
        "public_schema": "ltpb.ColorCalibration.macbeth_data",
        "embedded_reference_sha256": sha256(reference_table),
        "optimizer_target_sha256": sha256(optimizer_target),
        "optimizer_roundtrip_xyz_sha256": sha256(optimizer_roundtrip),
        "optimizer_matrix_words": expected_optimizer_words,
        "optimizer_iterations": cleanroom["iterations"],
        "optimizer_final_cost": cleanroom["final_cost"],
        "optimizer_cleanroom": "9/9 float32 words exact",
        "optimizer_wrapper_cleanroom": "9/9 float32 words exact",
        "public_camera_id": 0,
        "stored_illuminants": {"lower": "A/type0", "upper": "D65/type2"},
        "scene_xy": list(xy),
        "scene_cct": scene_cct,
        "alpha": alpha,
        "alpha_word": "0x%08x" % alpha_word,
        "matrix_alpha": matrix_alpha,
        "matrix_alpha_word": "0x%08x" % matrix_alpha_word,
        "live_map_dimensions": [32, 32, 1],
        "live_map_sha256": hashlib.sha256(live_map).hexdigest(),
        "input_selector": 0,
        "output_selector": 5,
        "converter": "0xab940",
        "stage_input_sha256": sha256(RUN / "stage_images/display_stage_03_340f70.raw"),
        "stage_output_sha256": sha256(RUN / "stage_images/display_stage_10_347680.raw"),
        "replay": "different_bytes=0/5101248",
        "two_body_same_key_macbeth_equal_count": cross_body_equal,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
