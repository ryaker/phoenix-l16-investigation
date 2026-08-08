#!/usr/bin/env python3
"""Verify CreateStereoImage's public exposure normalization and tile multiply."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import numpy as np
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = ROOT / "tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py"
RAW_PATH = ROOT / "tools/lldb_probes/raw_sensor_layout/verify_raw_sensor_layout.py"
SCHEMA_PATH = ROOT / "tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_embedded_calibration_proto_schema.py"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
DEFAULT_RUNS = (
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_exposure_unit1_28mm",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_exposure_new_06689",
    ROOT / "runs/index5_guidance_channel_origin/create_stereo_exposure_unit2_28mm",
)


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


STATIC = load_module("create_stereo_exposure_static", STATIC_PATH)
RAW = load_module("create_stereo_exposure_raw", RAW_PATH)
SCHEMA = load_module("create_stereo_exposure_schema", SCHEMA_PATH)


def f32(value) -> np.float32:
    return np.float32(value)


def bits(value) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def verify_static() -> str:
    data = STATIC.LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")
    mapping = STATIC.segments(data)
    body = STATIC.bytes_at(data, mapping, 0x19E7D0, 0x19EB60 - 0x19E7D0)
    require(
        hashlib.sha256(body).hexdigest()
        == "ac0cc397bfc831f6eb1e582529493006fd3d4a8120d42f282b3098ca3a264bca",
        "0x19e7d0 body changed",
    )
    expected_calls = {
        0x27D7C2: 0xF3330,
        0x27D7CE: 0xF2720,
        0x27D7E3: 0xE67C0,
        0x27D803: 0x19E7D0,
        0x27DAF0: 0x31B470,
        0x27DB05: 0xF3330,
        0x27DB11: 0xF2720,
        0x27DB26: 0xE67C0,
        0x27DB43: 0x27EE40,
    }
    for site, target in expected_calls.items():
        require(
            STATIC.direct_call_target(STATIC.instruction(data, mapping, site)) == target,
            f"call 0x{site:x} changed",
        )
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = list(decoder.disasm(body, 0x19E7D0))
    require(sum(item.size for item in instructions) == len(body), "scalar body disassembly gap")
    arithmetic = [item.mnemonic for item in instructions if item.mnemonic in {"mulss", "mulps", "addss", "addps", "subss", "subps", "divss", "divps"}]
    require(arithmetic and set(arithmetic) <= {"mulss", "mulps"}, f"unexpected arithmetic {set(arithmetic)}")
    require(STATIC.instruction(data, mapping, 0x19E8DF).mnemonic == "movaps", "scale-vector load changed")
    require(
        [STATIC.instruction(data, mapping, va).mnemonic for va in (0x19E910, 0x19E914, 0x19E917)]
        == ["movaps", "mulps", "movaps"],
        "vec4 SIMD transaction changed",
    )
    mono_body = STATIC.bytes_at(data, mapping, 0x27EE40, 0x27F51D - 0x27EE40)
    require(
        hashlib.sha256(mono_body).hexdigest()
        == "e6fc5e43c1331c494b0116ffdf5cd56d55a6ab9e0c111f9d4433142da4e4ac51",
        "0x27ee40 body changed",
    )
    require(
        [STATIC.instruction(data, mapping, va).mnemonic for va in (0x27F084, 0x27F08A, 0x27F092)]
        == ["movss", "mulss", "movss"],
        "mono scalar transaction changed",
    )
    exposure_body = STATIC.bytes_at(data, mapping, 0xE67C0, 0xE6AD4 - 0xE67C0)
    require(
        hashlib.sha256(exposure_body).hexdigest()
        == "35340dd189966c98250bc435264e27cba69d74cba5feaec633e8451be6a96ae8",
        "0xe67c0 body changed",
    )
    descriptors = SCHEMA.locate_all_descriptors(data)
    schema_fields = SCHEMA.field_map(descriptors)
    relative_brightness = schema_fields[".ltpb.VignettingCharacterization"][3]
    require(
        (relative_brightness["name"], relative_brightness["type"])
        == ("relative_brightness", "float"),
        "relative-brightness public schema changed",
    )
    return digest


def public_modules(path: Path) -> dict[int, dict]:
    result = {}
    for block in RAW.lri.scan_lri_blocks(str(path)):
        for wire_type, raw in RAW.fields(block["payload"]).get(12, []):
            if wire_type != 2:
                continue
            module = RAW.fields(raw)
            camera_id = RAW.one(raw, 2, 0)
            analog_bits = RAW.one(raw, 7, 5)
            exposure = RAW.one(raw, 8, 0)
            analog = struct.unpack("<f", struct.pack("<I", analog_bits))[0]
            row = {"sensor_exposure": exposure, "sensor_analog_gain": analog}
            require(camera_id not in result or result[camera_id] == row, f"{path}: duplicate camera {camera_id}")
            result[camera_id] = row
    return result


def public_relative_brightness(path: Path) -> dict[int, np.float32]:
    candidates = []
    for block in RAW.lri.scan_lri_blocks(str(path)):
        records = [
            raw for wire_type, raw in RAW.fields(block["payload"]).get(13, [])
            if wire_type == 2 and isinstance(raw, bytes)
        ]
        if len(records) != 16 or not all(RAW.fields(record).get(4) for record in records):
            continue
        result = {}
        for record in records:
            camera_id = RAW.one(record, 1, 0)
            vignetting = RAW.one(record, 4, 2)
            raw_bits = RAW.one(vignetting, 3, 5)
            result[camera_id] = f32(struct.unpack("<f", struct.pack("<I", raw_bits))[0])
        candidates.append(result)
    require(len(candidates) == 1, f"{path}: expected one module-calibration payload")
    return candidates[0]


def expected_ratio(
    target: dict,
    source: dict,
    target_brightness: np.float32,
    source_brightness: np.float32,
    apply_relative_brightness: bool,
) -> np.float32:
    target_energy = f32(f32(target["sensor_exposure"]) * f32(target["sensor_analog_gain"]))
    source_energy = f32(f32(source["sensor_exposure"]) * f32(source["sensor_analog_gain"]))
    exposure_ratio = f32(target_energy / source_energy)
    if not apply_relative_brightness:
        return exposure_ratio
    brightness_ratio = f32(f32(source_brightness) / f32(target_brightness))
    return f32(exposure_ratio * brightness_ratio)


def verify_run(run_dir: Path) -> dict:
    report = json.loads((run_dir / "report.json").read_text(encoding="ascii"))
    require(not report["errors"], f"{run_dir}: {report['errors']}")
    require(report["terminated_after_capture"], f"{run_dir}: incomplete capture")
    require(sorted(map(int, report["packets"])) == report["expected_keys"], f"{run_dir}: keys")
    source_lri = Path(report["source_lri"])
    modules = public_modules(source_lri)
    brightness = public_relative_brightness(source_lri)
    words = 0
    rows = []
    for key in report["expected_keys"]:
        packet = report["packets"][str(key)]
        target_key = packet["target_key"]
        require(key in modules and target_key in modules, f"{run_dir}: missing public module")
        for role, runtime_key in (("source", key), ("target", target_key)):
            runtime = packet[role]
            public = modules[runtime_key]
            require(runtime["camera_key"] == runtime_key, f"{run_dir}/{key}: {role} key")
            require(runtime["sensor_exposure"] == public["sensor_exposure"], f"{run_dir}/{key}: {role} exposure")
            require(bits(runtime["sensor_analog_gain"]) == bits(public["sensor_analog_gain"]), f"{run_dir}/{key}: {role} analog")
        correction = packet["relative_brightness_correction"]
        require(correction["source_key"] == key, f"{run_dir}/{key}: correction source key")
        require(correction["target_key"] == target_key, f"{run_dir}/{key}: correction target key")
        if correction["applied"]:
            require(packet["path"] == "vec4", f"{run_dir}/{key}: correction path")
            require(
                correction["source_relative_brightness_bits"] == bits(brightness[key]),
                f"{run_dir}/{key}: source relative_brightness",
            )
            require(
                correction["target_relative_brightness_bits"] == bits(brightness[target_key]),
                f"{run_dir}/{key}: target relative_brightness",
            )
        else:
            require(packet["path"] == "mono", f"{run_dir}/{key}: uncorrected path")
            require(
                any(value < 0 for value in correction["gate_pair"]),
                f"{run_dir}/{key}: relative-brightness gate not sentinel-invalid",
            )
        ratio = expected_ratio(
            modules[target_key],
            modules[key],
            brightness[target_key],
            brightness[key],
            correction["applied"],
        )
        require(packet["scalar_bits"] == bits(ratio), f"{run_dir}/{key}: scalar {packet['scalar']} != {ratio}")
        pre_path = Path(packet["pre_path"])
        post_path = Path(packet["post_path"])
        require(hashlib.sha256(pre_path.read_bytes()).hexdigest() == packet["pre_sha256"], f"{run_dir}/{key}: pre SHA")
        require(hashlib.sha256(post_path.read_bytes()).hexdigest() == packet["post_sha256"], f"{run_dir}/{key}: post SHA")
        pre = np.fromfile(pre_path, dtype="<f4")
        post = np.fromfile(post_path, dtype="<f4")
        require(
            pre.size == post.size == packet["logical_bytes"] // 4,
            f"{run_dir}/{key}: artifact size",
        )
        mono_tile_words_exact = 0
        if packet["path"] == "mono" and run_dir.name.endswith("unit1_28mm"):
            rebuilt_tile = np.asarray(pre * ratio, dtype="<f4")
            require(
                np.array_equal(rebuilt_tile.view("<u4"), post.view("<u4")),
                f"{run_dir}/{key}: mono tile multiply differs",
            )
            words += int(pre.size)
            mono_tile_words_exact = int(pre.size)
        expected_words = 4 if packet["path"] == "vec4" else 1
        if "worker_vector" in packet:
            worker = packet["worker_vector"]
            source_vector = np.frombuffer(
                bytes.fromhex(worker["source_hex"]), dtype="<f4"
            )
            destination_vector = np.frombuffer(
                bytes.fromhex(worker["destination_hex"]), dtype="<f4"
            )
            rebuilt = np.asarray(source_vector * ratio, dtype="<f4")
            require(
                np.array_equal(rebuilt.view("<u4"), destination_vector.view("<u4")),
                f"{run_dir}/{key}: worker SIMD transaction differs",
            )
            require(source_vector.size == expected_words, f"{run_dir}/{key}: worker width")
            words += expected_words
        row = {
            "source": key,
            "target": target_key,
            "source_relative_brightness": float(brightness[key]),
            "target_relative_brightness": float(brightness[target_key]),
            "relative_brightness_applied": correction["applied"],
            "scalar": packet["scalar"],
            "path": packet["path"],
        }
        if mono_tile_words_exact:
            row["mono_tile_words_exact"] = mono_tile_words_exact
        if "worker_vector" in packet:
            row["worker_vector_words_exact"] = expected_words
        rows.append(row)
    return {
        "run": run_dir.name,
        "source_lri": str(source_lri),
        "public_scalars_exact": len(rows),
        "retained_tile_words_exact": words,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dirs", nargs="*", type=Path)
    args = parser.parse_args()
    digest = verify_static()
    print(f"static_create_stereo_exposure_scale=OK libcp={digest}")
    total = 0
    for run_dir in (args.run_dirs or DEFAULT_RUNS):
        result = verify_run(run_dir)
        total += result["retained_tile_words_exact"]
        print("create_stereo_exposure_scale=OK " + json.dumps(result, sort_keys=True))
    print(f"create_stereo_exposure_scale_all=OK retained_tile_float_words={total}")


if __name__ == "__main__":
    main()
