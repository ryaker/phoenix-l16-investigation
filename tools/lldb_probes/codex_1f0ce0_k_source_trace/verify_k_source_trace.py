#!/usr/bin/env python3
"""Verify the 0x1f0ce0 K-source trace packets.

The trace refines the producer-edge boundary proven by
`state_helpers_23c5f0_f33d0_runtime/verify_1f0ce0_producer.py`.

It proves, for the captured four-zoom constructor packets, that:

- the first usable K payload after `0x1f0b00` is an exact public LRI fixed32
  K sequence for the same camera ID;
- helper entry arguments point at public two-record K/scalar vectors from the
  compact intrinsics payload, and the helper output is the expected float32
  linear interpolation/extrapolation of K fields 0,2,4,5;
- the optional helper output copied through `rbp-0x188 -> rbp-0xb8` is the
  K packet later passed to both `0xf33d0` selector calls;
- the `0xf3350` scale window is identity in these runs; and
- B/C packets change from the public input K into zoom-specific non-public K
  before the final selector-bank copies because object+0x54 selects a
  zoom-specific point on the public scalar axis.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(
    0, str(ROOT / "tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime")
)

import lane_b_index5_public_meaning_audit as audit  # noqa: E402
import verify_1f0ce0_producer as producer_verify  # noqa: E402


RUN_DIR = ROOT / "runs/codex_1f0ce0_k_source_trace"

SITES_BY_VA = {
    "0x1f0d36": "after_1f0b00_vectors",
    "0x1f96e0": "helper_entry_1f96e0",
    "0x1f0ee5": "after_optional_helper_k_copy",
    "0x1f0fed": "before_f3350_scale",
    "0x1f1047": "after_f3350_scale",
    "0x1f1328": "selector0_f33d0_call",
    "0x1f134b": "selector1_f33d0_call",
}

EXPECTED_KEYS = {
    "28mm": list(range(0, 10)),
    "35mm": list(range(0, 10)),
    "70mm": list(range(5, 15)),
    "150mm": list(range(5, 15)),
}

EXPECTED_FINAL_PUBLIC_KEYS = {
    "28mm": set(range(0, 5)),
    "35mm": set(range(0, 5)),
    "70mm": set(),
    "150mm": set(),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier: str) -> None:
    hdr = RUN_DIR / f"k_source_trace_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def camera_names(keys) -> str:
    return ",".join(audit.CAMERA_NAMES[key] for key in sorted(keys)) or "none"


def load_report(tier: str) -> dict:
    path = RUN_DIR / f"k_source_trace_{tier}.json"
    require(path.exists(), f"{tier}: missing report {path}")
    return json.loads(path.read_text())


def raw_from_f64(values: list[float]) -> tuple[int, ...]:
    require(len(values) == 9, "expected 9 f64 K values")
    return tuple(struct.unpack("<I", struct.pack("<f", float(value)))[0] for value in values)


def raw_to_f32(raw: int) -> float:
    return struct.unpack("<f", struct.pack("<I", raw & 0xFFFFFFFF))[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_to_raw(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", f32(value)))[0]


def k_stack_raw(event: dict) -> tuple[int, ...]:
    values = event["trace"]["k_stack"]["raw_u32x9"]
    require(isinstance(values, list) and len(values) == 9, "missing K stack raw_u32x9")
    return tuple(value & 0xFFFFFFFF for value in values)


def public_intrinsics_interp_records(tier: str, key: int) -> list[dict]:
    blocks = audit.scan_lri_blocks(audit.TIERS[tier])
    payloads = [block["payload"] for block in blocks if block["payload_size"] == 32832]
    require(len(payloads) == 1, f"{tier}: expected one 32832-byte intrinsics payload")

    for entry in audit.field_values(payloads[0], 13, wire_type=2):
        cam_id = audit.first_field(entry, 1, wire_type=0)
        if cam_id != key:
            continue
        body = audit.first_field(entry, 3, wire_type=2)
        require(isinstance(body, bytes), f"{tier} {key}: missing public field_3 body")
        records = []
        for config_index, config in enumerate(audit.field_values(body, 2, wire_type=2)):
            scalar_raw = audit.first_field(config, 6, wire_type=5)
            k_container = audit.first_field(config, 2, wire_type=2)
            if not isinstance(scalar_raw, int) or not isinstance(k_container, bytes):
                continue
            k_message = audit.first_field(k_container, 1, wire_type=2)
            if not isinstance(k_message, bytes):
                continue
            k_raw = tuple(value & 0xFFFFFFFF for value in audit._fixed32_values(k_message))
            if len(k_raw) != 9:
                continue
            scalar_f32 = raw_to_f32(scalar_raw)
            scalar_i32 = int(round(scalar_f32))
            require(
                abs(scalar_f32 - scalar_i32) < 0.001,
                f"{tier} {audit.CAMERA_NAMES[key]}: public field_6 is not integral",
            )
            records.append(
                {
                    "config_index": config_index,
                    "scalar_raw": scalar_raw & 0xFFFFFFFF,
                    "scalar_f32": scalar_f32,
                    "scalar_i32": scalar_i32,
                    "k_raw": k_raw,
                    "k_f32": tuple(raw_to_f32(raw) for raw in k_raw),
                    "path": (
                        f"32832.field_13[camera={key}].field_3."
                        f"field_2[{config_index}].field_2.field_1"
                    ),
                    "scalar_path": (
                        f"32832.field_13[camera={key}].field_3."
                        f"field_2[{config_index}].field_6"
                    ),
                }
            )
        require(records, f"{tier} {audit.CAMERA_NAMES[key]}: no public K/scalar records")
        return records
    raise AssertionError(f"{tier} {audit.CAMERA_NAMES[key]}: public camera entry not found")


def interp_field(y0: float, y1: float, s0: float, s1: float, x: float) -> float:
    slope = f32(f32(y1 - y0) / f32(s1 - s0))
    intercept = f32(y0 - f32(s0 * slope))
    return f32(f32(x * slope) + intercept)


def formula_raw(records: list[tuple[int, ...]], scalars: list[int], x_scalar: int) -> tuple[int, ...]:
    require(len(records) == len(scalars), "record/scalar count mismatch")
    require(len(records) == 2, "current proof admits only the two-record helper branch")
    require(all(len(record) == 9 for record in records), "K record length mismatch")

    paired = sorted(
        (
            {
                "scalar_i32": scalars[index],
                "scalar_f32": f32(float(scalars[index])),
                "record": records[index],
                "f32": tuple(raw_to_f32(raw) for raw in records[index]),
            }
            for index in range(2)
        ),
        key=lambda item: item["scalar_f32"],
    )
    require(paired[0]["scalar_f32"] != paired[1]["scalar_f32"], "helper scalar axis is degenerate")
    output = list(records[0])
    x = f32(float(x_scalar))
    for field_index in (0, 2, 4, 5):
        value = interp_field(
            paired[0]["f32"][field_index],
            paired[1]["f32"][field_index],
            paired[0]["scalar_f32"],
            paired[1]["scalar_f32"],
            x,
        )
        output[field_index] = f32_to_raw(value)
    return tuple(output)


def validate_static_helper_formula_edges() -> str:
    data = producer_verify.LIBCP_DYLIB.read_bytes()
    segments = producer_verify.macho_segments(data)
    require(
        producer_verify.bytes_at(data, segments, 0x0F3304, 3) == b"\x8b\x47\x54",
        "0xf3300 no longer returns object+0x54",
    )
    expected_byte_windows = {
        0x1F971A: (
            bytes.fromhex("488b5e304c8b7e38"),
            "0x1f96e0 scalar-vector header loads changed",
        ),
        0x1F99F4: (
            bytes.fromhex("488b01488b49084829c14883f948752f"),
            "0x1f96e0 record-vector size branch changed",
        ),
        0x1F9A57: (
            bytes.fromhex("4881f990000000"),
            "0x1f96e0 two-record branch size check changed",
        ),
        0x1F9B19: (
            bytes.fromhex(
                "f3440f5cc2f3440f5ec1f3410f59d8f30f5cd3"
                "f3440f59c5f3440f58c2"
            ),
            "0x1f96e0 field-0 interpolation window changed",
        ),
        0x1F9B5B: (
            bytes.fromhex(
                "f30f5cd1f30f5ed0f30f59faf30f5ccff30f59d5"
                "f30f58d1"
            ),
            "0x1f96e0 field-4 interpolation window changed",
        ),
        0x1F9B98: (
            bytes.fromhex(
                "f30f5cc3f30f5ec649630c24488d0cc9f20f104cc828"
                "f20f5af149634c2404488d0cc9f20f104cc828f20f5ac9"
                "f3440f59d0f3410f5cdaf30f59c5f30f58c3f30f5cce"
                "f30f5eccf3440f59c9f3410f5cf1f30f59cdf30f58ce"
            ),
            "0x1f96e0 field-2/field-5 interpolation window changed",
        ),
    }
    for va, (expected, label) in expected_byte_windows.items():
        actual = producer_verify.bytes_at(data, segments, va, len(expected))
        require(actual == expected, f"{label} at 0x{va:x}")
    return "static_1f96e0_two_record_interp=OK"


def group_events(packet: dict, tier: str) -> dict[int, dict[str, dict]]:
    grouped: dict[int, dict[str, dict]] = {}
    for event in packet.get("events", []):
        site = event.get("site_name")
        trace = event.get("trace") or {}
        obj = trace.get("object") or {}
        key = obj.get("key_i32_0x60")
        require(site in SITES_BY_VA.values(), f"{tier}: unexpected site {site!r}")
        require(isinstance(key, int), f"{tier}: event without integer key")
        require(obj.get("active_u8_0x30") == 1, f"{tier} {key}: object+0x30 not active")
        require(obj.get("stage_i32_0x64") == 0, f"{tier} {key}: object+0x64 not zero")
        require(key not in grouped or site not in grouped[key], f"{tier}: duplicate {key} {site}")
        grouped.setdefault(key, {})[site] = event

    expected_sites = set(SITES_BY_VA.values())
    for key, sites in grouped.items():
        require(set(sites) == expected_sites, f"{tier} {key}: incomplete site set")
    return grouped


def validate_process_window(packet: dict, tier: str) -> str:
    require(not packet.get("errors"), f"{tier}: probe errors present")
    require(packet.get("disabled_after_cap") == [], f"{tier}: breakpoint disabled by hit cap")
    require(packet.get("counts") == {va: 10 for va in SITES_BY_VA}, f"{tier}: site counts mismatch")
    require(len(packet.get("events") or []) == 70, f"{tier}: expected 70 events")

    process = packet.get("process") or {}
    if tier == "150mm":
        if (
            process.get("state") == 10
            and process.get("exit_status") == 0
            and packet.get("drive_hit_step_cap") is False
        ):
            return "probe_window_complete render_complete=yes"
        require(process.get("state") == 5, "150mm: expected known post-window stopped state")
        require(process.get("exit_status") == -1, "150mm: expected known post-window LLDB stop")
        require(packet.get("drive_hit_step_cap") is True, "150mm: expected drive step cap after stop")
        return "probe_window_complete render_complete=no_known_lldb_stop"

    require(process.get("state") == 10, f"{tier}: process did not exit")
    require(process.get("exit_status") == 0, f"{tier}: nonzero process exit")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: unexpected step cap")
    return "probe_window_complete render_complete=yes"


def public_camera_path(seq_index: dict[tuple[int, ...], list[str]], key: int, raw: tuple[int, ...]) -> str:
    paths = seq_index.get(raw) or []
    prefix = f"32832.field_13[camera={key}]"
    for path in paths:
        if path.startswith(prefix):
            return path
    raise AssertionError(
        f"{audit.CAMERA_NAMES[key]}: public K sequence did not map to {prefix}"
    )


def validate_call_arguments(event: dict, selector: int, tier: str, key: int) -> None:
    trace = event["trace"]
    regs = event["registers"]
    rbp = regs["rbp"]
    obj = trace["object"]["object"]
    require(trace["arg_r8d_selector"] == selector, f"{tier} {key}: selector mismatch")
    require(trace["arg_rdi_object"] == obj, f"{tier} {key}: rdi object mismatch")
    require(trace["arg_rsi_k"] == rbp - 0xB8, f"{tier} {key}: K arg is not rbp-0xb8")
    require(trace["arg_rdx_pose"] == rbp - 0x278, f"{tier} {key}: pose arg is not rbp-0x278")
    require(trace["arg_rcx_triple"] == rbp - 0x288, f"{tier} {key}: triple arg is not rbp-0x288")


def helper_record_raws(helper_entry: dict, tier: str, key: int) -> list[tuple[int, ...]]:
    vector = helper_entry["record_vector_source_plus_0x00"]
    header = vector["header"]
    require(header["byte_span"] == 0x90, f"{tier} {audit.CAMERA_NAMES[key]}: helper record span is not 0x90")
    require(header["record_count_0x48"] == 2, f"{tier} {audit.CAMERA_NAMES[key]}: helper record count is not two")
    records = vector["records"]
    require(len(records) == 2, f"{tier} {audit.CAMERA_NAMES[key]}: missing helper records")
    return [raw_from_f64(record["f64x9"]) for record in records]


def helper_scalars(helper_entry: dict, tier: str, key: int) -> list[int]:
    vector = helper_entry["scalar_vector_source_plus_0x30"]
    header = vector["header"]
    require(header["byte_span"] == 8, f"{tier} {audit.CAMERA_NAMES[key]}: helper scalar span is not 8")
    require(header["i32_count"] == 2, f"{tier} {audit.CAMERA_NAMES[key]}: helper scalar count is not two")
    values = vector["i32_values"]
    require(isinstance(values, list) and len(values) == 2, f"{tier} {audit.CAMERA_NAMES[key]}: missing helper scalars")
    return [int(value) for value in values]


def validate_helper_formula(
    tier: str,
    key: int,
    helper_entry_event: dict,
    input_raw: tuple[int, ...],
    helper_raw: tuple[int, ...],
) -> dict:
    name = audit.CAMERA_NAMES[key]
    trace = helper_entry_event["trace"]
    regs = helper_entry_event["registers"]
    rbp = regs["rbp"]
    obj = trace["object"]
    entry = trace["helper_entry"]

    require(entry["arg_rdi_output"] == rbp - 0x188, f"{tier} {name}: helper output arg is not rbp-0x188")
    require(entry["arg_rsi_source"] == rbp - 0x140, f"{tier} {name}: helper source arg is not rbp-0x140")
    require(entry["arg_edx_scalar"] == obj["i32_0x54"], f"{tier} {name}: edx scalar != object+0x54")
    require(obj["u32_0x54"] == (entry["arg_edx_scalar"] & 0xFFFFFFFF), f"{tier} {name}: u32 object+0x54 mismatch")

    public_records = public_intrinsics_interp_records(tier, key)
    require(len(public_records) == 2, f"{tier} {name}: public K/scalar record count is not two")
    public_raws = [record["k_raw"] for record in public_records]
    public_scalars = [record["scalar_i32"] for record in public_records]
    records = helper_record_raws(entry, tier, key)
    scalars = helper_scalars(entry, tier, key)

    require(records == public_raws, f"{tier} {name}: helper K records do not match public field_2 K records")
    require(scalars == public_scalars, f"{tier} {name}: helper scalars do not match public field_6 values")
    require(input_raw == public_raws[0], f"{tier} {name}: first usable K is not public record[0]")

    expected_raw = formula_raw(records, scalars, entry["arg_edx_scalar"])
    require(helper_raw == expected_raw, f"{tier} {name}: helper output does not match public scalar formula")
    return {
        "scalar": entry["arg_edx_scalar"],
        "public_scalars": tuple(public_scalars),
        "public_paths": tuple(record["path"] for record in public_records),
        "scalar_paths": tuple(record["scalar_path"] for record in public_records),
    }


def validate_tier(tier: str) -> dict:
    packet = load_report(tier)
    process_status = validate_process_window(packet, tier)
    if process_status.endswith("render_complete=yes"):
        require_hdr_output(tier)
    grouped = group_events(packet, tier)
    require(sorted(grouped) == EXPECTED_KEYS[tier], f"{tier}: key set mismatch")

    seq_index = audit.public_calibration_fixed32_sequence_index(tier)
    public_input_keys = set()
    final_public_keys = set()
    helper_changed_keys = set()
    formula_keys = set()
    scale_changed_keys = set()
    selector_pair_keys = set()
    records = {}
    public_paths = {}
    formula_records = {}

    for key, sites in grouped.items():
        name = audit.CAMERA_NAMES[key]
        first = sites["after_1f0b00_vectors"]
        helper_entry = sites["helper_entry_1f96e0"]
        helper = sites["after_optional_helper_k_copy"]
        before_scale = sites["before_f3350_scale"]
        after_scale = sites["after_f3350_scale"]
        selector0 = sites["selector0_f33d0_call"]
        selector1 = sites["selector1_f33d0_call"]

        vector_sources = first["trace"]["vector_sources"]
        k_vector = vector_sources["k_vector_rbp_minus_0x30"]
        require(k_vector["byte_span"] >= 72, f"{tier} {name}: K vector too small")
        input_raw = raw_from_f64(vector_sources["first_k_vector_f64x9"])
        public_paths[key] = public_camera_path(seq_index, key, input_raw)
        public_input_keys.add(key)

        helper_raw = raw_from_f64(helper["trace"]["helper_output"]["f64x9"])
        helper_stack = k_stack_raw(helper)
        before_raw = k_stack_raw(before_scale)
        after_raw = k_stack_raw(after_scale)
        selector0_raw = k_stack_raw(selector0)
        selector1_raw = k_stack_raw(selector1)

        require(helper_raw == helper_stack, f"{tier} {name}: helper output not copied to K stack")
        require(helper_raw == before_raw, f"{tier} {name}: pre-scale K differs from helper output")
        formula_records[key] = validate_helper_formula(tier, key, helper_entry, input_raw, helper_raw)
        formula_keys.add(key)
        if helper_raw != input_raw:
            helper_changed_keys.add(key)

        accessor = before_scale["trace"]["object"]["accessor_0x10c"]
        require(accessor["scale_x_f32_0x124"] == 1.0, f"{tier} {name}: scale-x not 1.0")
        require(accessor["scale_y_f32_0x128"] == 1.0, f"{tier} {name}: scale-y not 1.0")
        if after_raw != before_raw:
            scale_changed_keys.add(key)

        require(after_raw == selector0_raw, f"{tier} {name}: selector0 K changed")
        require(after_raw == selector1_raw, f"{tier} {name}: selector1 K changed")
        validate_call_arguments(selector0, 0, tier, key)
        validate_call_arguments(selector1, 1, tier, key)
        selector_pair_keys.add(key)

        if after_raw in seq_index:
            final_public_keys.add(key)
        records[key] = {
            "input_raw": input_raw,
            "helper_raw": helper_raw,
            "final_raw": after_raw,
            "public_path": public_paths[key],
            "formula": formula_records[key],
        }

    expected_helper_changed = {key for key in EXPECTED_KEYS[tier] if key >= 5}
    require(public_input_keys == set(EXPECTED_KEYS[tier]), f"{tier}: public input keys mismatch")
    require(formula_keys == set(EXPECTED_KEYS[tier]), f"{tier}: formula keys mismatch")
    require(helper_changed_keys == expected_helper_changed, f"{tier}: helper-changed keys mismatch")
    require(scale_changed_keys == set(), f"{tier}: scale changed despite identity fields")
    require(selector_pair_keys == set(EXPECTED_KEYS[tier]), f"{tier}: selector pair keys mismatch")
    require(final_public_keys == EXPECTED_FINAL_PUBLIC_KEYS[tier], f"{tier}: final public keys mismatch")

    return {
        "tier": tier,
        "records": records,
        "process_status": process_status,
        "public_input_keys": public_input_keys,
        "formula_keys": formula_keys,
        "helper_changed_keys": helper_changed_keys,
        "final_public_keys": final_public_keys,
    }


def validate_cross_tier(results: dict[str, dict]) -> str:
    b4_input = {results[tier]["records"][8]["input_raw"] for tier in audit.TIERS}
    b4_final = {results[tier]["records"][8]["final_raw"] for tier in audit.TIERS}
    require(len(b4_input) == 1, "B4 public input K should be stable across four tiers")
    require(len(b4_final) == 4, "B4 helper/final K should have four tier variants")

    c5_input = {results[tier]["records"][14]["input_raw"] for tier in ("70mm", "150mm")}
    c5_final = {results[tier]["records"][14]["final_raw"] for tier in ("70mm", "150mm")}
    require(len(c5_input) == 1, "C5 public input K should be stable across tele tiers")
    require(len(c5_final) == 2, "C5 helper/final K should have two tele variants")

    for key in range(0, 5):
        wide_input = {results[tier]["records"][key]["input_raw"] for tier in ("28mm", "35mm")}
        wide_final = {results[tier]["records"][key]["final_raw"] for tier in ("28mm", "35mm")}
        require(len(wide_input) == 1, f"{audit.CAMERA_NAMES[key]} input changed across wide tiers")
        require(len(wide_final) == 1, f"{audit.CAMERA_NAMES[key]} final changed across wide tiers")
        require(wide_input == wide_final, f"{audit.CAMERA_NAMES[key]} formula should preserve public K")

    return (
        "cross_tier=B4_public_input_stable_formula_variants4,"
        "C5_public_input_stable_formula_variants2,A1-A5_wide_formula_preserves_public_K"
    )


def main() -> None:
    print(producer_verify.validate_static_producer_edge())
    print(validate_static_helper_formula_edges())
    results = {}
    for tier in audit.TIERS:
        result = validate_tier(tier)
        results[tier] = result
        print(
            f"{tier}: OK {result['process_status']} "
            f"keys={camera_names(EXPECTED_KEYS[tier])} "
            f"public_input={camera_names(result['public_input_keys'])} "
            f"formula={camera_names(result['formula_keys'])} "
            f"helper_changed={camera_names(result['helper_changed_keys'])} "
            f"final_public={camera_names(result['final_public_keys'])}"
        )
    print(validate_cross_tier(results))


if __name__ == "__main__":
    main()
