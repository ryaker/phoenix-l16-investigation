#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/codex_276860_scalar_operand_origin")
TIERS = ("28mm", "35mm", "70mm", "150mm")
REQUIRED_TARGET_COUNTS = {
    "caller_pre_29a140": 1,
    "maker_after_299fd0": 1,
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def words(hex_string):
    data = bytes.fromhex(hex_string)
    require(len(data) == 16, f"expected 16 bytes, got {len(data)}")
    return [data[i] | (data[i + 1] << 8) for i in range(0, 16, 2)]


def validate_pair(path, pair, index):
    table = pair.get("table")
    scalar = pair.get("scalar")
    broadcast = pair.get("broadcast")
    require(table, f"{path.name}: pair {index} missing table sample")
    require(scalar, f"{path.name}: pair {index} missing scalar sample")
    require(broadcast, f"{path.name}: pair {index} missing broadcast sample")
    require(table.get("site_va") == 0x27786B, f"{path.name}: pair {index} table site")
    require(scalar.get("site_va") == 0x27791D, f"{path.name}: pair {index} scalar site")
    require(broadcast.get("site_va") == 0x277945, f"{path.name}: pair {index} broadcast site")

    for key in ("thread_id",):
        require(table.get(key) == scalar.get(key) == broadcast.get(key), f"{path.name}: pair {index} {key}")
    for key in ("rbp", "r9"):
        require(
            table["registers"].get(key)
            == scalar["registers"].get(key)
            == broadcast["registers"].get(key),
            f"{path.name}: pair {index} register {key} mismatch",
        )

    table_load = table.get("table_load", {})
    scalar_values = scalar.get("scalar_values_before_movd", {})
    require(
        table_load.get("stack_minus_0x210_eq_table_base") is True,
        f"{path.name}: pair {index} table base not stack rbp-0x210",
    )
    require(
        table_load.get("table_value_u16")
        == (scalar_values.get("xmm2_source_ecx_u32") & 0xFFFF),
        f"{path.name}: pair {index} table value != scalar ecx",
    )

    x2 = scalar_values.get("xmm2_expected_broadcast_u16")
    x3 = scalar_values.get("xmm3_expected_broadcast_u16")
    require(words(broadcast["xmm_hex"]["xmm2"]) == [x2] * 8, f"{path.name}: pair {index} xmm2")
    require(words(broadcast["xmm_hex"]["xmm3"]) == [x3] * 8, f"{path.name}: pair {index} xmm3")

    ctx = broadcast.get("target_stack_context", {})
    relationships = {
        "object_eq_target": ctx.get("object_from_stack_rbp_minus_0x1c8")
        == broadcast.get("target_object"),
        "r9_record_lookup_found": ctx.get("record_lookup_from_r9", {}).get("record_index")
        is not None,
    }
    for key, value in relationships.items():
        require(value is True, f"{path.name}: pair {index} {key}={value}")


def validate_report(path):
    packet = json.loads(path.read_text())
    require(packet.get("capture_complete") is True, f"{path.name}: capture not complete")
    require(packet.get("terminated_after_capture") is True, f"{path.name}: not terminated after capture")
    require(not packet.get("drive_hit_step_cap"), f"{path.name}: hit step cap")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")
    process = packet.get("process", {})
    require(process.get("valid") is True, f"{path.name}: invalid process packet")
    for site, expected in REQUIRED_TARGET_COUNTS.items():
        require(
            packet.get("target_counts", {}).get(site) == expected,
            f"{path.name}: target count {site}={packet.get('target_counts', {}).get(site)}",
        )
    pairs = packet.get("paired_samples", [])
    require(len(pairs) >= 4, f"{path.name}: too few paired samples {len(pairs)}")
    for index, pair in enumerate(pairs):
        validate_pair(path, pair, index)
    return packet


def main():
    for tier in TIERS:
        path = ROOT / f"scalar_origin_{tier}.json"
        require(path.exists(), f"missing report {path}")
        packet = validate_report(path)
        print(
            f"{path.name}: OK paired_samples={len(packet.get('paired_samples', []))} "
            f"terminated_after_capture={packet.get('terminated_after_capture')}"
        )


if __name__ == "__main__":
    main()
