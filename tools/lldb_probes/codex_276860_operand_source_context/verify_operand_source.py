#!/usr/bin/env python3
import json
import pathlib
import struct


ROOT = pathlib.Path("runs/codex_276860_operand_source_context")
TIERS = ("28mm", "35mm", "70mm", "150mm")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32_from_hex(hex_string):
    return list(struct.unpack("<ffff", bytes.fromhex(hex_string)))


def u32_from_hex(hex_string):
    return list(struct.unpack("<IIII", bytes.fromhex(hex_string)))


def expected_f32_from_u8x4(hex_string):
    raw = bytes.fromhex(hex_string)
    require(len(raw) == 4, "guide source must be four bytes")
    return [float(v) for v in raw]


def producer_matches(packet, site_name, field_offset, write_value):
    return [
        sample
        for sample in packet.get("producer_samples", [])
        if sample.get("site") == site_name
        and sample.get("field_offset") == field_offset
        and sample.get("write_value") == write_value
        and sample.get("write_object") == packet.get("target_object")
    ]


def any_producer_match(packet, site_names, field_offset, write_value):
    matches = []
    for site_name in site_names:
        matches.extend(producer_matches(packet, site_name, field_offset, write_value))
    return matches


def index_setter_fields(packet):
    target_index = packet.get("target_index")
    for sample in packet.get("setup_samples", []):
        if sample.get("site") != "index_setter_26bbd0":
            continue
        if sample.get("incoming_index_esi") != target_index:
            continue
        return sample.get("setter_object_fields") or {}
    return {}


def watchpoint_matches(packet, field_offset, write_value):
    return [
        sample
        for sample in packet.get("watchpoint_samples", [])
        if (sample.get("watchpoint") or {}).get("offset") == field_offset
        and sample.get("field_value_at_stop") == write_value
    ]


def latest_watchpoint_match(packet, field_offset, write_value):
    matches = watchpoint_matches(packet, field_offset, write_value)
    require(matches, f"missing watchpoint for object+0x{field_offset:x}")
    return matches[-1]


def field_origin(packet, field_offset, write_value, producer_site_names):
    producer_hit = any_producer_match(packet, producer_site_names, field_offset, write_value)
    if producer_hit:
        return f"producer:{producer_hit[-1]['site']}"
    watch_hit = watchpoint_matches(packet, field_offset, write_value)
    if watch_hit:
        va = watch_hit[-1].get("libcp_va")
        return f"watch:{va:#x}" if isinstance(va, int) else "watch:unknown"
    setter_fields = index_setter_fields(packet)
    setter_qwords = setter_fields.get("qwords") or {}
    if setter_qwords.get(f"0x{field_offset:x}") == write_value:
        return "pre_index_setter"
    return None


def validate_packet(path):
    tier = path.stem.replace("operand_source_", "")
    packet = json.loads(path.read_text())
    require(packet.get("capture_complete") is True, f"{path.name}: capture not complete")
    require(packet.get("terminated_after_capture") is True, f"{path.name}: process not killed after capture")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")
    require(packet.get("target_counts", {}).get("caller_pre_29a140") == 1, f"{path.name}: caller count")
    require(packet.get("target_counts", {}).get("maker_after_299fd0") == 1, f"{path.name}: maker count")
    table = packet.get("packet", {}).get("table")
    require(table, f"{path.name}: missing table packet")
    require(table.get("site_va") == 0x27786B, f"{path.name}: table VA")
    require(table.get("target_stack_context", {}).get("object_from_stack_rbp_minus_0x1c8") == table.get("target_object"), f"{path.name}: target object mismatch")

    ctx = table["target_stack_context"]
    stack = ctx["stack_qwords"]
    fields = ctx["object_fields"]
    qwords = fields["qwords"]
    operands = table["operand_sources"]

    require(stack["rbp_minus_0x208"] == qwords["0x1e8"], f"{path.name}: rbp-0x208 != object+0x1e8")
    require(operands["sub_vector_base_rbp_minus_0x208"] == qwords["0x1e8"], f"{path.name}: sub vector base")
    require(stack["rbp_minus_0x210"] == qwords["0x198"], f"{path.name}: rbp-0x210 != object+0x198")
    require(table["table_load"]["table_base_rdi"] == qwords["0x198"], f"{path.name}: table base != object+0x198")
    require(table["table_load"]["stack_minus_0x210_eq_table_base"] is True, f"{path.name}: stack table equality")
    producer_origins = {
        "0x198": field_origin(
            packet,
            0x198,
            qwords["0x198"],
            ("table_buffer_store_0x198_26ca94",),
        ),
        "0x1e8": field_origin(
            packet,
            0x1E8,
            qwords["0x1e8"],
            ("sub_buffer_store_0x1e8_26cbcd",),
        ),
        "0x200": field_origin(
            packet,
            0x200,
            qwords["0x200"],
            ("xmm8_base_store_0x200_26cc01",),
        ),
        "0x288": field_origin(
            packet,
            0x288,
            qwords["0x288"],
            ("guide_store_0x288_new_26c5e7", "guide_store_0x288_reuse_26c633"),
        ),
    }
    missing_origins = [name for name, origin in producer_origins.items() if origin is None]
    require(not missing_origins, f"{path.name}: missing field origins {missing_origins}")

    guide_desc = fields.get("guide_descriptor_from_0x288") or {}
    guide_dims = guide_desc.get("u32_0x10_0x1c") or []
    require(guide_dims[:2] == [2080, 1560], f"{path.name}: unexpected guide dimensions {guide_dims}")
    expanded_width = guide_dims[0] + 2
    table_u16_capacity = 8 * expanded_width
    midpoint_bytes = 16 * expanded_width
    wp_0x198 = latest_watchpoint_match(packet, 0x198, qwords["0x198"])
    wp_0x1e8 = latest_watchpoint_match(packet, 0x1E8, qwords["0x1e8"])
    wp_0x200 = latest_watchpoint_match(packet, 0x200, qwords["0x200"])
    require(wp_0x198["registers"]["r12"] == qwords["0x198"], f"{path.name}: 0x198 write register")
    require(wp_0x198["registers"]["r14"] == table_u16_capacity, f"{path.name}: table capacity")
    require(wp_0x1e8["registers"]["r15"] == qwords["0x1e8"], f"{path.name}: 0x1e8 write register")
    require(wp_0x200["registers"]["r15"] == qwords["0x1e8"], f"{path.name}: 0x200 base register")
    require(wp_0x200["registers"]["rbx"] == expanded_width, f"{path.name}: expanded width register")
    require(wp_0x200["registers"]["r14"] == midpoint_bytes, f"{path.name}: midpoint bytes")
    require(qwords["0x200"] - qwords["0x1e8"] == midpoint_bytes, f"{path.name}: 0x200 midpoint")

    load = operands.get("xmm8_latest_load")
    require(load, f"{path.name}: missing xmm8 load")
    require(load["target_stack_context"]["object_from_stack_rbp_minus_0x1c8"] == table["target_object"], f"{path.name}: load object")
    load_info = load["xmm8_vector_load"]
    load_hex = load_info["load_hex"]
    require(load_hex == table["xmm_hex"]["xmm8"], f"{path.name}: table xmm8 not equal load bytes")

    store = load_info.get("matched_store_sample")
    require(store, f"{path.name}: missing matched xmm8 store")
    store_info = store["xmm8_vector_store"]
    require(store_info["dest_addr_rax_plus_rcx"] == load_info["load_addr_rcx"], f"{path.name}: store/load address mismatch")
    require(store_info["xmm0_store_hex"] == load_hex, f"{path.name}: store xmm0 != load bytes")
    require(store_info["dest_base_rax"] == qwords["0x200"], f"{path.name}: store base != object+0x200")

    guide = store_info.get("latest_guide_sample")
    require(guide, f"{path.name}: missing guide sample")
    guide_info = guide["guide_source"]
    expected_floats = expected_f32_from_u8x4(guide_info["source_u8x4_hex"])
    actual_floats = f32_from_hex(store_info["xmm0_store_hex"])
    require(actual_floats == expected_floats, f"{path.name}: guide bytes do not reconstruct xmm8 store")
    table_index = table["table_load"]["table_index_rcx"]
    require(0 <= table_index < table_u16_capacity, f"{path.name}: table index outside capacity")
    require(
        table["table_load"]["table_addr_rdi_plus_2rcx"]
        == qwords["0x198"] + 2 * table_index,
        f"{path.name}: table address formula",
    )

    sub_vec = f32_from_hex(operands["sub_vector16_hex"])
    xmm8 = f32_from_hex(table["xmm_hex"]["xmm8"])
    scale = f32_from_hex(operands["object_plus_0x60_hex"])
    sub_delta_from_0x200 = operands["sub_vector_addr"] - qwords["0x200"]
    require(
        operands["sub_vector_addr"] == qwords["0x1e8"] + operands["sub_vector_offset_rdx"],
        f"{path.name}: subtraction vector address formula",
    )
    return {
        "tier": tier,
        "xmm8": xmm8,
        "sub_vector": sub_vec,
        "object_scale": scale,
        "guide_u8x4_hex": guide_info["source_u8x4_hex"],
        "sub_vector_addr": operands["sub_vector_addr"],
        "xmm8_load_addr": load_info["load_addr_rcx"],
        "table_value": table["table_load"]["table_value_u16"],
        "field_origins": producer_origins,
        "field_layout": {
            "expanded_width": expanded_width,
            "table_u16_capacity": table_u16_capacity,
            "midpoint_bytes": midpoint_bytes,
            "sub_delta_from_0x200": sub_delta_from_0x200,
        },
        "producer_sites": sorted({sample["site"] for sample in packet.get("producer_samples", [])}),
    }


def main():
    results = []
    for tier in TIERS:
        results.append(validate_packet(ROOT / f"operand_source_{tier}.json"))
    for result in results:
        print(
            f"operand_source_{result['tier']}.json: OK "
            f"xmm8={result['xmm8']} "
            f"source_vec={result['sub_vector']} "
            f"guide_u8x4={result['guide_u8x4_hex']} "
            f"table={result['table_value']} "
            f"origins={result['field_origins']} "
            f"layout={result['field_layout']} "
            f"producers={','.join(result['producer_sites'])}"
        )


if __name__ == "__main__":
    main()
