#!/usr/bin/env python3
"""Verify public/installed origins for live CNR worker parameter vectors."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RBP, X86_REG_RIP


ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "tools/lldb_probes/denoise_route_census"
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)

LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
CNR_SETUP_SHA256 = "6f7ac1fc4faf18ccc4ef5c9b70dff4336a807ff53194efcb357ba25e467fbf0d"
COLOR_TABLE_JSON_SHA256 = (
    "5e3f94c8b13b11c3c144dc765587479e49e4508d033a4a3603a026e486df104d"
)

SAMPLES = {
    "unit1_28mm": {
        "lri": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        "runtime": ROOT / "runs/denoise_route_census/unit1_28mm_cnr_formula.json",
    },
    "unit1_35mm": {
        "lri": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
        "runtime": ROOT / "runs/denoise_route_census/unit1_35mm_cnr_formula.json",
    },
    "unit1_70mm": {
        "lri": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
        "runtime": ROOT / "runs/denoise_route_census/unit1_70mm_cnr_formula.json",
    },
    "unit1_150mm": {
        "lri": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
        "runtime": ROOT / "runs/denoise_route_census/unit1_150mm_cnr_formula.json",
    },
    "unit2_35mm": {
        "lri": Path("/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"),
        "runtime": ROOT / "runs/denoise_route_census/unit2_35mm_cnr_formula.json",
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_bits(value: float) -> bytes:
    return struct.pack("<f", float(value))


def field_f32(raw: int) -> float:
    return struct.unpack("<f", struct.pack("<I", raw))[0]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def static_helpers():
    return load_module("inspect_cnr_static", PROBE_DIR / "inspect_cnr_static.py")


def lri_helpers():
    return load_module("lri_field_inspect", ROOT / "tools/lri_field_inspect.py")


def parse_lri(path: Path) -> dict[str, object]:
    lri = lri_helpers()
    modules: dict[int, dict[str, object]] = {}
    awb_matches: list[dict[str, object]] = []
    sensor_rows: list[dict[str, object]] = []
    focal = None
    reference = None

    def fields(data: bytes):
        return list(lri.parse_proto_fields(data))

    def append_awb(view_fields, block_index: int, layout: str) -> None:
        gain_messages = [item for item in view_fields if item[0] == 15 and item[1] == 2]
        if len(gain_messages) != 1:
            return
        gains: dict[str, float] = {}
        for number, wire, raw in fields(gain_messages[0][2]):
            if wire != 5:
                continue
            name = {1: "r", 2: "g_r", 3: "g_b", 4: "b"}.get(number)
            if name:
                gains[name] = field_f32(raw)
        if set(gains) == {"r", "g_r", "g_b", "b"}:
            modes = [raw for number, _wire, raw in view_fields if number == 7]
            awb_matches.append(
                {
                    "block": block_index,
                    "layout": layout,
                    "mode": modes[0] if modes else 0,
                    "gains": gains,
                }
            )

    def parse_vst_model(data: bytes) -> dict[str, float]:
        model: dict[str, float] = {}
        for number, wire, raw in fields(data):
            if wire == 5 and number == 1:
                model["a"] = field_f32(raw)
            elif wire == 5 and number == 2:
                model["b"] = field_f32(raw)
        return model

    for block in lri.scan_lri_blocks(str(path)):
        root = fields(block["payload"])
        append_awb(root, block["idx"], "direct_view_preferences")
        for number, wire, value in root:
            if number == 4 and wire == 0:
                focal = value
            elif number == 5 and wire == 0:
                reference = value
            elif number == 12 and wire == 2:
                module: dict[str, object] = {}
                for fn, fw, raw in fields(value):
                    if fn == 2:
                        module["id"] = raw
                    elif fn == 7 and fw == 5:
                        module["sensor_analog_gain"] = field_f32(raw)
                    elif fn == 8 and fw == 0:
                        module["sensor_exposure"] = raw
                if "id" in module:
                    modules[int(module["id"])] = module
            elif number == 16 and wire == 2:
                sensor: dict[str, object] = {"models": []}
                for fn, fw, raw in fields(value):
                    if fn == 1:
                        sensor["type"] = raw
                    elif fn == 2 and fw == 2:
                        characterization = fields(raw)
                        for cfn, cfw, crv in characterization:
                            if cfn == 1 and cfw == 5:
                                sensor["black_level"] = field_f32(crv)
                            elif cfn == 2 and cfw == 5:
                                sensor["white_level"] = field_f32(crv)
                            elif cfn == 3 and cfw == 5:
                                sensor["cliff_slope"] = field_f32(crv)
                            elif cfn == 4 and cfw == 2:
                                row: dict[str, object] = {}
                                for vfn, vfw, vrv in fields(crv):
                                    if vfn == 1:
                                        row["gain"] = vrv
                                    elif vfn == 2 and vfw == 5:
                                        row["threshold"] = field_f32(vrv)
                                    elif vfn == 3 and vfw == 5:
                                        row["scale"] = field_f32(vrv)
                                    elif vfn in (4, 5, 6, 7) and vfw == 2:
                                        name = {
                                            4: "red",
                                            5: "green",
                                            6: "blue",
                                            7: "panchromatic",
                                        }[vfn]
                                        row[name] = parse_vst_model(vrv)
                                sensor["models"].append(row)
                if sensor.get("models"):
                    sensor_rows.append(sensor)
            elif number == 19 and wire == 2:
                append_awb(fields(value), block["idx"], "lightheader_wrapped")

    require(len(awb_matches) == 1, f"{path}: expected one AWB message")
    require(reference in modules, f"{path}: missing reference camera module")
    return {
        "focal": focal,
        "reference_camera": reference,
        "modules": modules,
        "awb": awb_matches[0],
        "sensor_rows": sensor_rows,
    }


def bytes_at(data: bytes, sections, va: int, size: int) -> bytes:
    inspector = static_helpers()
    return inspector.bytes_at(data, sections, va, size)


def decode_installed_color_table(data: bytes, sections) -> list[dict[str, object]]:
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    raw = bytes_at(data, sections, 0xE1210, 0x1000)
    stores: dict[int, int] = {}
    for insn in md.disasm(raw, 0xE1210):
        if insn.mnemonic != "mov" or len(insn.operands) != 2:
            continue
        dst, src = insn.operands
        if (
            dst.type == X86_OP_MEM
            and dst.mem.base == X86_REG_RBP
            and dst.size == 4
            and src.type == X86_OP_IMM
        ):
            offset = -dst.mem.disp if dst.mem.disp < 0 else dst.mem.disp
            # The initializer later reuses stack slots for another table; keep the
            # first materialization, which is the RGB SensorGainVars table.
            stores.setdefault(offset, src.imm & 0xFFFFFFFF)

    shared = struct.unpack("<4f", bytes_at(data, sections, 0x5AD270, 16))
    rows: list[dict[str, object]] = []
    for index, gain in enumerate(range(100, 776, 25)):
        stack_offset = 0x770 - (index * 0x40)
        require(stores.get(stack_offset) == gain, f"installed CNR gain row {gain}")
        if index == 0:
            first_va = 0x5AD260
            last_va = 0x5AD280
        else:
            first_va = 0x5AD290 + ((index - 1) * 0x20)
            last_va = first_va + 0x10
        first = struct.unpack("<4f", bytes_at(data, sections, first_va, 16))
        last = struct.unpack("<4f", bytes_at(data, sections, last_va, 16))
        b = [
            field_f32(stores[stack_offset - (0x34 + lane * 4)])
            for lane in range(3)
        ]
        rows.append(
            {
                "gain": gain,
                "scale": first[0],
                "threshold": first[1],
                "cliff_slope": first[2],
                "black": [first[3], shared[0], shared[1]],
                "white": [shared[2], shared[3], last[0]],
                "red": {"a": last[1], "b": b[0]},
                "green": {"a": last[2], "b": b[1]},
                "blue": {"a": last[3], "b": b[2]},
            }
        )
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    require(digest == COLOR_TABLE_JSON_SHA256, "installed RGB VST table drift")
    return rows


def verify_static() -> tuple[list[dict[str, object]], dict[str, object]]:
    inspector = static_helpers()
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, "libcp SHA drift")
    sections = inspector.macho_sections(data)
    setup_hash = inspector.range_hash(data, sections, 0x34B3F0, 0x34B808)
    require(setup_hash == CNR_SETUP_SHA256, "CNR setup hash drift")
    table = decode_installed_color_table(data, sections)

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    calls: set[tuple[int, int]] = set()
    rip_reads: dict[int, int] = {}
    for start, end in ((0x34B3F0, 0x34B808), (0xEF050, 0xEF0B5), (0x307EE0, 0x308459)):
        for insn in md.disasm(bytes_at(data, sections, start, end - start), start):
            for op in insn.operands:
                if op.type == X86_OP_IMM and insn.mnemonic == "call":
                    calls.add((insn.address, op.imm))
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                    rip_reads[insn.address] = insn.address + insn.size + op.mem.disp
    for pair in (
        (0x34B439, 0xF3340),
        (0x34B445, 0xF32D0),
        (0x34B451, 0xEF050),
        (0x34B460, 0xF0610),
        (0x34B6BB, 0x307EE0),
    ):
        require(pair in calls, f"missing setup call {pair}")
    require(rip_reads.get(0xEF059) == 0x5AE770, "analog-gain x100 constant")
    require(struct.unpack("<f", bytes_at(data, sections, 0x5AE770, 4))[0] == 100.0, "gain multiplier")
    return table, {
        "libcp_sha256": digest,
        "cnr_setup_sha256": setup_hash,
        "installed_rgb_vst_table_json_sha256": COLOR_TABLE_JSON_SHA256,
    }


def selected_row(table: list[dict[str, object]], analog_gain: float) -> tuple[int, dict[str, object]]:
    raw_key = int(f32(f32(analog_gain) * f32(100.0)))
    for row in table:
        if int(row["gain"]) >= raw_key:
            return raw_key, row
    return raw_key, table[-1]


def compare_public_lri_row(lri_packet: dict[str, object], gain: int, row: dict[str, object]) -> dict[str, object]:
    for sensor in lri_packet["sensor_rows"]:
        if sensor.get("type") != 2:
            continue
        models = sensor["models"]
        for public in models:
            if public.get("gain") != gain:
                continue
            public_a = [
                public["red"]["a"],
                public["green"]["a"],
                public["blue"]["a"],
            ]
            public_b = [
                public["red"]["b"],
                public["green"]["b"],
                public["blue"]["b"],
            ]
            installed_a = [row["red"]["a"], row["green"]["a"], row["blue"]["a"]]
            installed_b = [row["red"]["b"], row["green"]["b"], row["blue"]["b"]]
            return {
                "public_type2_row_present": True,
                "public_type2_a": public_a,
                "public_type2_b": public_b,
                "installed_a": installed_a,
                "installed_b": installed_b,
                "public_equals_installed": all(
                    f32_bits(public_a[i]) == f32_bits(installed_a[i])
                    and f32_bits(public_b[i]) == f32_bits(installed_b[i])
                    for i in range(3)
                ),
            }
    return {"public_type2_row_present": False}


def verify_sample(label: str, table: list[dict[str, object]]) -> dict[str, object]:
    meta = SAMPLES[label]
    lri_packet = parse_lri(meta["lri"])
    runtime = json.loads(meta["runtime"].read_text())
    require(not runtime["errors"], f"{label}: runtime errors")
    params = runtime["entry_events"][0]["param_block"]["f32"]

    gains = lri_packet["awb"]["gains"]
    expected_v10 = [
        f32(1.0 / gains["r"]),
        f32(1.0 / gains["g_r"]),
        f32(1.0 / gains["b"]),
        1.0,
    ]
    expected_v20 = [f32(1.0 / f32(value * value)) for value in expected_v10]
    for index, value in enumerate(expected_v10):
        require(f32_bits(params[4 + index]) == f32_bits(value), f"{label}: V10 lane {index}")
    for index, value in enumerate(expected_v20):
        require(f32_bits(params[8 + index]) == f32_bits(value), f"{label}: V20 lane {index}")

    ref = int(lri_packet["reference_camera"])
    ref_gain = float(lri_packet["modules"][ref]["sensor_analog_gain"])
    selector_raw, row = selected_row(table, ref_gain)
    expected_a = [row["red"]["a"], row["green"]["a"], row["blue"]["a"], 0.0]
    expected_b = [row["red"]["b"], row["green"]["b"], row["blue"]["b"], 0.0]
    for index, value in enumerate(expected_a):
        require(f32_bits(params[12 + index]) == f32_bits(value), f"{label}: V30 lane {index}")
    for index, value in enumerate(expected_b):
        require(f32_bits(params[16 + index]) == f32_bits(value), f"{label}: V40 lane {index}")

    public_compare = compare_public_lri_row(lri_packet, int(row["gain"]), row)
    return {
        "label": label,
        "focal": lri_packet["focal"],
        "reference_camera": ref,
        "reference_sensor_analog_gain": ref_gain,
        "selector_raw_int_gain_times_100": selector_raw,
        "installed_selected_gain": row["gain"],
        "awb_public_gains": gains,
        "V10": params[4:8],
        "V20": params[8:12],
        "V30_rgb_a": params[12:15],
        "V40_rgb_b": params[16:19],
        "public_lri_type2_comparison": public_compare,
    }


def main() -> None:
    table, static = verify_static()
    samples = [verify_sample(label, table) for label in SAMPLES]
    out = {
        "static": static,
        "public_paths": {
            "V10": "LightHeader.view_preferences.awb_gains.{r,g_r,b} reciprocal",
            "V20": "derived reciprocal square of V10",
            "V30": "installed RGB SensorGainVars selected by LightHeader.modules[image_reference_camera].sensor_analog_gain: red/green/blue.a",
            "V40": "installed RGB SensorGainVars selected by LightHeader.modules[image_reference_camera].sensor_analog_gain: red/green/blue.b",
        },
        "installed_rgb_vst_table": table,
        "samples": samples,
    }
    out_path = ROOT / "runs/denoise_route_census/cnr_public_origins.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    selected = ",".join(
        f"{item['label']}:{item['installed_selected_gain']}" for item in samples
    )
    print(
        "cnr_public_origins=OK "
        f"libcp={static['libcp_sha256']} "
        f"table={static['installed_rgb_vst_table_json_sha256']} "
        f"selected={selected}"
    )


if __name__ == "__main__":
    main()
