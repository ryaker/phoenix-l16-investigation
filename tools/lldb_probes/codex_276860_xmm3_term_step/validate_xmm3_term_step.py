#!/usr/bin/env python3
import json
import pathlib
import struct


ROOT = pathlib.Path("runs/codex_276860_xmm3_term_step")
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


def f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def low_f32(hex_string):
    data = bytes.fromhex(hex_string)
    require(len(data) == 16, f"expected 16 bytes, got {len(data)}")
    return struct.unpack_from("<f", data, 0)[0]


def trunc_i32(value):
    truncated = int(value)
    require(-(2**31) <= truncated <= (2**31 - 1), f"i32 overflow {value}")
    return truncated & 0xFFFFFFFF


def close_f32(actual, expected, label):
    require(abs(actual - expected) <= max(1.0e-4, abs(expected) * 1.0e-5), label)


def validate_report(path):
    packet = json.loads(path.read_text())
    require(packet.get("capture_complete") is True, f"{path.name}: capture not complete")
    require(packet.get("terminated_after_capture") is True, f"{path.name}: not terminated after capture")
    require(not packet.get("step_hit_cap"), f"{path.name}: step cap")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")
    process = packet.get("process", {})
    require(process.get("valid") is True, f"{path.name}: invalid process packet")
    for site, expected in REQUIRED_TARGET_COUNTS.items():
        require(
            packet.get("target_counts", {}).get(site) == expected,
            f"{path.name}: target count {site}={packet.get('target_counts', {}).get(site)}",
        )
    samples = packet.get("packet", {})
    table = samples.get("table")
    xmm4 = samples.get("xmm4_ready")
    product = samples.get("product_ready")
    preadd = samples.get("preadd_int")
    scalar = samples.get("postadd_scalar")
    broadcast = samples.get("broadcast_ready")
    for label, sample in (
        ("table", table),
        ("xmm4", xmm4),
        ("product", product),
        ("preadd", preadd),
        ("scalar", scalar),
        ("broadcast", broadcast),
    ):
        require(sample, f"{path.name}: missing {label}")

    require(table.get("site_va") == 0x27786B, f"{path.name}: table site")
    require(xmm4.get("site_va") == 0x277903, f"{path.name}: xmm4 site")
    require(product.get("site_va") == 0x277917, f"{path.name}: product site")
    require(preadd.get("site_va") == 0x27791B, f"{path.name}: preadd site")
    require(scalar.get("site_va") == 0x27791D, f"{path.name}: scalar site")
    require(broadcast.get("site_va") == 0x277945, f"{path.name}: broadcast site")

    for key in ("thread_id",):
        require(
            table.get(key)
            == xmm4.get(key)
            == product.get(key)
            == preadd.get(key)
            == scalar.get(key)
            == broadcast.get(key),
            f"{path.name}: {key} mismatch",
        )
    for key in ("rbp", "r9"):
        require(
            table["registers"].get(key)
            == xmm4["registers"].get(key)
            == product["registers"].get(key)
            == preadd["registers"].get(key)
            == scalar["registers"].get(key)
            == broadcast["registers"].get(key),
            f"{path.name}: register {key} mismatch",
        )

    table_load = table.get("table_load", {})
    require(
        table_load.get("stack_minus_0x210_eq_table_base") is True,
        f"{path.name}: table base not rbp-0x210",
    )
    table_value = table_load.get("table_value_u16")
    require((scalar["registers"]["rcx"] & 0xFFFF) == table_value, f"{path.name}: scalar ecx")

    obj_fields = xmm4.get("target_stack_context", {}).get("object_fields", {})
    obj_u16 = obj_fields.get("u16_0x56")
    obj_f32 = obj_fields.get("f32_0x58")
    require(product["registers"]["rdx"] & 0xFFFFFFFF == obj_u16, f"{path.name}: product edx")

    xmm4_low = low_f32(xmm4["xmm_hex"]["xmm4"])
    product_low = low_f32(product["xmm_hex"]["xmm2"])
    expected_product = f32(f32(f32(obj_u16) * f32(obj_f32)) * f32(xmm4_low))
    close_f32(product_low, expected_product, f"{path.name}: product")
    expected_preadd = trunc_i32(product_low)
    require(preadd["registers"]["rdx"] & 0xFFFFFFFF == expected_preadd, f"{path.name}: preadd edx")
    require(expected_preadd != 0, f"{path.name}: expected nonzero preadd term")
    expected_postadd = (expected_preadd + (table_value & 0xFFFFFFFF)) & 0xFFFFFFFF
    require(scalar["registers"]["rdx"] & 0xFFFFFFFF == expected_postadd, f"{path.name}: postadd edx")

    require(words(broadcast["xmm_hex"]["xmm2"]) == [table_value & 0xFFFF] * 8, f"{path.name}: xmm2")
    require(words(broadcast["xmm_hex"]["xmm3"]) == [expected_postadd & 0xFFFF] * 8, f"{path.name}: xmm3")

    ctx = broadcast.get("target_stack_context", {})
    require(
        ctx.get("object_from_stack_rbp_minus_0x1c8") == broadcast.get("target_object"),
        f"{path.name}: object mismatch",
    )
    require(
        ctx.get("record_lookup_from_r9", {}).get("record_index") is not None,
        f"{path.name}: r9 record lookup",
    )
    return packet


def main():
    for tier in TIERS:
        path = ROOT / f"xmm3_term_step_{tier}.json"
        require(path.exists(), f"missing report {path}")
        packet = validate_report(path)
        print(
            f"{path.name}: OK stepped_sites=5 "
            f"trace_steps={len(packet.get('step_trace', []))}"
        )


if __name__ == "__main__":
    main()
