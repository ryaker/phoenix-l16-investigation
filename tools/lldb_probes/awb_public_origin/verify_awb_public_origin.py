#!/usr/bin/env python3
"""Verify the public LRI origin and renderer policy for AWB gains."""

from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import math
import struct
from collections import Counter
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUNS = ROOT / "runs/awb_public_origin"

LRIS = {
    "unit1_28mm": Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
    "unit1_35mm": Path("/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"),
    "unit1_70mm": Path("/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"),
    "unit1_150mm": Path("/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"),
    "unit2_28mm": Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
    "unit2_35mm": Path("/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"),
    "unit2_70mm": Path("/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"),
    "unit2_150mm": Path("/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri"),
}

RUNTIME_LABELS = (
    "unit1_28mm",
    "unit1_35mm",
    "unit1_70mm",
    "unit1_150mm",
    "unit2_28mm",
)

_LRI_MODULE = None


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def load_schema_module():
    path = (
        ROOT
        / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
        / "verify_embedded_calibration_proto_schema.py"
    )
    spec = importlib.util.spec_from_file_location("embedded_schema", path)
    require(spec is not None and spec.loader is not None, "schema module loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_lri_module():
    global _LRI_MODULE
    if _LRI_MODULE is not None:
        return _LRI_MODULE
    path = ROOT / "tools/lri_field_inspect.py"
    spec = importlib.util.spec_from_file_location("lri_fields", path)
    require(spec is not None and spec.loader is not None, "LRI module loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _LRI_MODULE = module
    return _LRI_MODULE


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
    require(
        hashlib.sha256(data).hexdigest()
        == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        "libcp SHA-256 drift",
    )
    bodies = {
        (0x3510F0, 0x351330): "27a3b92862c79f8f19458f01f60c686ce27a66a0378f724f8eeca4a7553b5e2b",
        (0x3EC960, 0x3ECB10): "515520e36d5338b80d45d9768b2918e81c7008553c0e8efc1c2db99d987feb56",
        (0x2EB560, 0x2EB882): "92a21c74b71fad4b0cd661e5bb96e1ba7ab23daae51021bf1de2308b158a27bf",
    }
    for (start, end), digest in bodies.items():
        require(hashlib.sha256(data[start:end]).hexdigest() == digest, f"body 0x{start:x}")

    awb = instructions(data, 0x3510F0, 0x351330)
    for address, mnemonic, operands in (
        (0x351101, "mov", "rax, qword ptr [rbx]"),
        (0x351104, "movss", "xmm1, dword ptr [rip + 0x25701c]"),
        (0x35110F, "divss", "xmm0, dword ptr [rax]"),
        (0x351116, "divss", "xmm2, dword ptr [rax + 4]"),
        (0x35111E, "divss", "xmm3, dword ptr [rax + 8]"),
        (0x351123, "insertps", "xmm0, xmm2, 0x10"),
        (0x351129, "insertps", "xmm0, xmm3, 0x20"),
        (0x35112F, "insertps", "xmm0, xmm1, 0x30"),
        (0x3511F4, "movaps", "xmmword ptr [rbp - 0x80], xmm0"),
        (0x351212, "call", "0x353e50"),
    ):
        require_instruction(awb, address, mnemonic, operands)
    require(struct.unpack_from("<f", data, 0x5A8128)[0] == 1.0, "AWB numerator")

    post = instructions(data, 0x3EC960, 0x3ECB10)
    for address, mnemonic, operands in (
        (0x3ECA5C, "call", "0x1bea20"),
        (0x3ECA61, "movss", "xmm0, dword ptr [rbp - 0xc0]"),
        (0x3ECA69, "movss", "xmm1, dword ptr [rbp - 0xb8]"),
        (0x3ECA71, "insertps", "xmm0, dword ptr [rbp - 0xbc], 0x10"),
        (0x3ECA7B, "insertps", "xmm0, xmm1, 0x20"),
        (0x3ECA81, "insertps", "xmm0, dword ptr [rip + 0x1bb69d], 0x30"),
        (0x3ECA96, "movaps", "xmmword ptr [rbp - 0xa0], xmm0"),
    ):
        require_instruction(post, address, mnemonic, operands)

    schema = load_schema_module()
    descriptors = schema.locate_all_descriptors(data)
    view = next(item for item in descriptors if item["name"] == "view_preferences.proto")
    require(
        view["serialized_sha256"]
        == "fdc7259f0c4ef618574bfcc1af27a9cc5baeb0dad08636e939228dc52be8a14a",
        "ViewPreferences descriptor drift",
    )
    fields = schema.field_map([view])
    schema.require_field(fields, ".ltpb.ViewPreferences", 7, "awb_mode", "enum")
    schema.require_field(fields, ".ltpb.ViewPreferences", 15, "awb_gains", "message")
    for number, name in enumerate(("r", "g_r", "g_b", "b"), start=1):
        schema.require_field(
            fields, ".ltpb.ViewPreferences.ChannelGain", number, name, "float"
        )
    awb_mode = next(
        enum
        for enum in view["enums"]
        if enum["full_name"] == ".ltpb.ViewPreferences.AWBMode"
    )
    require(
        awb_mode["values"][0] == {"name": "AWB_MODE_AUTO", "number": 0},
        "AWB enum default",
    )
    return {
        "body_hashes": {
            f"0x{start:x}..0x{end:x}": digest
            for (start, end), digest in bodies.items()
        },
        "view_preferences_descriptor_sha256": view["serialized_sha256"],
        "public_path": "LightHeader.view_preferences.awb_gains.{r,g_r,g_b,b}",
        "policy": "float32 reciprocal of r, common green, b; alpha=1",
    }


def parse_awb(path: Path) -> dict:
    lri = load_lri_module()
    matches = []

    def append_view(view_fields, block_index, layout):
        gain_messages = [
            item for item in view_fields if item[0] == 15 and item[1] == 2
        ]
        if len(gain_messages) != 1:
            return
        gain_fields = list(lri.parse_proto_fields(gain_messages[0][2]))
        if {item[0] for item in gain_fields} != {1, 2, 3, 4}:
            return
        if any(item[1] != 5 for item in gain_fields):
            return
        gains = {
            number: struct.unpack("<f", struct.pack("<I", raw))[0]
            for number, _wire_type, raw in gain_fields
        }
        modes = [raw for number, _wire_type, raw in view_fields if number == 7]
        matches.append(
            {
                "block_index": block_index,
                "layout": layout,
                "mode_present": bool(modes),
                "mode": modes[0] if modes else 0,
                "gains": {
                    "r": gains[1],
                    "g_r": gains[2],
                    "g_b": gains[3],
                    "b": gains[4],
                },
            }
        )

    for block in lri.scan_lri_blocks(str(path)):
        root_fields = list(lri.parse_proto_fields(block["payload"]))
        # Legacy LRIs store ViewPreferences directly in its own LELR payload.
        append_view(root_fields, block["idx"], "direct_view_preferences")
        for number, wire_type, value in root_fields:
            if number != 19 or wire_type != 2:
                continue
            view_fields = list(lri.parse_proto_fields(value))
            append_view(view_fields, block["idx"], "lightheader_wrapped")
    require(len(matches) == 1, f"{path}: expected one AWB message, got {len(matches)}")
    return matches[0]


def verify_lris() -> dict:
    result = {}
    for label, path in LRIS.items():
        packet = parse_awb(path)
        gains = packet["gains"]
        require(packet["mode"] == 0, f"{label}: non-AUTO mode")
        require(gains["g_r"] == gains["g_b"], f"{label}: unequal green gains")
        require(all(value > 0 for value in gains.values()), f"{label}: nonpositive gain")
        result[label] = packet
    return result


def verify_runtime(public: dict, require_runtime: bool) -> dict:
    result = {}
    for label in RUNTIME_LABELS:
        path = RUNS / f"{label}.json"
        if not path.is_file():
            if require_runtime:
                raise AssertionError(f"missing runtime report {path}")
            continue
        report = json.loads(path.read_text())
        require(not report["errors"], f"{label}: {report['errors']}")
        captures = {item["stage"]: item for item in report["captures"]}
        require(
            set(captures) == {"demosaic_driver_2eb560", "post_square_3eca61"},
            f"{label}: capture stages",
        )
        driver = captures["demosaic_driver_2eb560"]
        post = captures["post_square_3eca61"]
        require(
            driver["phase"] in ([0, 0], [1, 0], [0, 1], [1, 1]),
            f"{label}: invalid phase",
        )
        gains = public[label]["gains"]
        expected = [
            f32(1.0 / gains["r"]),
            f32(1.0 / gains["g_r"]),
            f32(1.0 / gains["b"]),
        ]
        require(driver["reciprocal_gains"][:3] == expected, f"{label}: driver join")
        require(post["reciprocal_gains"][:3] == expected, f"{label}: post-square join")
        require(post["reciprocal_gains"][3] == 0.0, f"{label}: post-square staging lane")
        result[label] = {
            "public": gains,
            "expected_reciprocal_rgb": expected,
            "driver_phase": driver["phase"],
            "driver_thread": driver["thread_id"],
            "post_square_thread": post["thread_id"],
        }
    return result


def lightheader_summary(path: Path) -> dict:
    lri = load_lri_module()
    blocks = lri.scan_lri_blocks(str(path))
    if not blocks:
        return {
            "focal": None,
            "device_fw_version": "<unreadable>",
            "device_asic_fw_version": "<unreadable>",
            "block_count": 0,
            "container_closed": False,
        }
    fields = list(lri.parse_proto_fields(blocks[0]["payload"]))
    by_number = {number: value for number, _wire_type, value in fields}
    return {
        "focal": by_number.get(4),
        "device_fw_version": (
            by_number.get(9, b"").decode("utf-8", errors="replace")
            if isinstance(by_number.get(9, b""), bytes)
            else ""
        ),
        "device_asic_fw_version": (
            by_number.get(10, b"").decode("utf-8", errors="replace")
            if isinstance(by_number.get(10, b""), bytes)
            else ""
        ),
        "block_count": len(blocks),
        "container_closed": (
            sum(block["total_size"] for block in blocks) == path.stat().st_size
        ),
    }


def verify_corpus(root: Path) -> dict:
    paths = sorted(Path(item) for item in glob.glob(str(root / "**/*.lri"), recursive=True))
    require(paths, f"no LRI files under {root}")
    modes = Counter()
    blocks = Counter()
    layouts = Counter()
    missing = []
    unequal_green = []
    missing_dates = Counter()
    missing_focals = Counter()
    missing_device_fw = Counter()
    missing_asic_fw = Counter()
    missing_block_counts = Counter()
    missing_container_closed = Counter()
    green_pairs = Counter()
    for index, path in enumerate(paths, start=1):
        try:
            packet = parse_awb(path)
        except AssertionError:
            missing.append(str(path))
            missing_dates[path.parent.name] += 1
            header = lightheader_summary(path)
            missing_focals[header["focal"]] += 1
            missing_device_fw[header["device_fw_version"]] += 1
            missing_asic_fw[header["device_asic_fw_version"]] += 1
            missing_block_counts[header["block_count"]] += 1
            missing_container_closed[header["container_closed"]] += 1
            continue
        modes[(packet["mode_present"], packet["mode"])] += 1
        blocks[packet["block_index"]] += 1
        layouts[packet["layout"]] += 1
        green_pairs[
            (
                struct.pack("<f", packet["gains"]["g_r"]).hex(),
                struct.pack("<f", packet["gains"]["g_b"]).hex(),
            )
        ] += 1
        if packet["gains"]["g_r"] != packet["gains"]["g_b"]:
            unequal_green.append(str(path))
        if index % 1000 == 0:
            print(f"AWB_CORPUS_PROGRESS {index}/{len(paths)}")
    require(
        not any(
            closed and count
            for closed, count in missing_container_closed.items()
        ),
        "structurally complete LRI missing AWB message",
    )
    require(not unequal_green, "complete LRI corpus contains unequal green gains")
    require(
        set(modes) == {(False, 0)},
        f"unexpected AWB mode corpus distribution: {modes}",
    )
    return {
        "lri_count": len(paths),
        "awb_message_count": len(paths) - len(missing),
        "missing_awb_message_count": len(missing),
        "missing_awb_message_samples": missing[:24],
        "missing_date_counts": dict(sorted(missing_dates.items())),
        "missing_focal_counts": {
            str(key): value
            for key, value in sorted(missing_focals.items(), key=lambda item: str(item[0]))
        },
        "missing_device_fw_counts": dict(sorted(missing_device_fw.items())),
        "missing_asic_fw_counts": dict(sorted(missing_asic_fw.items())),
        "missing_block_counts": {
            str(key): value for key, value in sorted(missing_block_counts.items())
        },
        "missing_container_closed_counts": {
            str(key): value
            for key, value in sorted(missing_container_closed.items())
        },
        "mode_counts": {
            f"present={present},value={value}": count
            for (present, value), count in sorted(modes.items())
        },
        "block_index_counts": {str(key): value for key, value in sorted(blocks.items())},
        "layout_counts": dict(sorted(layouts.items())),
        "green_pair_bit_counts": {
            f"{left},{right}": count
            for (left, right), count in sorted(green_pairs.items())
        },
        "unequal_green_count": len(unequal_green),
        "unequal_green_samples": unequal_green[:24],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--corpus-root", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = {
        "status": "OK",
        "static": verify_static(),
        "public_lris": verify_lris(),
    }
    result["runtime"] = verify_runtime(result["public_lris"], args.require_runtime)
    if args.corpus_root:
        result["corpus"] = verify_corpus(args.corpus_root)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        "PASS AWB public origin "
        f"lris={len(result['public_lris'])} runtime={len(result['runtime'])} "
        f"corpus={result.get('corpus', {}).get('lri_count', 0)}"
    )


if __name__ == "__main__":
    main()
