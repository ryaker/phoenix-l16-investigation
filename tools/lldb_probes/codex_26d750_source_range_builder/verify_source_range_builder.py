#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/codex_26d750_source_range_builder")
EXPECTED = {
    "source_range_28mm.json",
    "source_range_35mm.json",
    "source_range_70mm.json",
    "source_range_150mm.json",
    "source_range_unit2_28mm.json",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def samples_by_site(packet):
    out = {}
    for sample in packet.get("samples", []):
        out.setdefault(sample.get("site"), []).append(sample)
    return out


def descriptor_shape(desc, width=2080, height=1560, stride=2080):
    return (
        desc
        and desc.get("read_ok")
        and desc.get("width_0x10") == width
        and desc.get("height_0x14") == height
        and desc.get("stride_0x18") == stride
        and desc.get("data_0x20")
    )


def first(site_map, site):
    values = site_map.get(site) or []
    require(values, f"missing sample {site}")
    return values[0]


def validate(path):
    packet = json.loads(path.read_text())
    process = packet.get("process") or {}
    require(process.get("state") == "exited", f"{path.name}: process not exited {process}")
    require(process.get("exit_status") == 0, f"{path.name}: nonzero exit {process}")
    require(not packet.get("drive_hit_step_cap"), f"{path.name}: hit step cap")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")

    target_counts = packet.get("target_counts") or {}
    for site in (
        "caller_pre_26d750",
        "caller_post_26d750",
        "caller_pre_29a140",
        "builder_26d750_entry",
        "builder_after_seed_descriptor",
        "builder_after_267120",
        "builder_after_298ff0",
        "builder_return",
    ):
        require(target_counts.get(site) == 1, f"{path.name}: {site} count {target_counts.get(site)}")
    require(
        target_counts.get("builder_after_output_store", 0) >= 8,
        f"{path.name}: too few output stores {target_counts.get('builder_after_output_store')}",
    )

    site_map = samples_by_site(packet)
    pre = first(site_map, "caller_pre_26d750")
    entry = first(site_map, "builder_26d750_entry")
    post = first(site_map, "caller_post_26d750")
    pre_29a140 = first(site_map, "caller_pre_29a140")
    returned = first(site_map, "builder_return")

    for name, args_key in ((path.name, "call_args"), (path.name, "entry_args")):
        args = pre["call_args"] if args_key == "call_args" else entry["entry_args"]
        for key in (
            "rdi_is_target",
            "rsi_is_source_plus_0x2a8",
            "rdx_is_source_plus_0x208",
            "r8_is_output_local",
            "r9_is_target_plus_0x23c",
            "stack_arg_is_target_plus_0x238",
        ):
            require(args.get(key), f"{name}: {args_key} {key} false: {args}")
        require(args.get("ecx_low32") == 8, f"{name}: {args_key} ecx != 8: {args}")

    post_desc = post["post_call_descriptor"]
    pre_desc = pre_29a140["pre_29a140_descriptor"]
    return_desc = returned["builder_output_descriptor_r15"]
    require(descriptor_shape(post_desc), f"{path.name}: post descriptor shape {post_desc}")
    require(descriptor_shape(pre_desc), f"{path.name}: pre-29a140 descriptor shape {pre_desc}")
    require(descriptor_shape(return_desc), f"{path.name}: return descriptor shape {return_desc}")
    require(post_desc["data_0x20"] == pre_desc["data_0x20"], f"{path.name}: post/pre data mismatch")
    require(post_desc["first_pairs"] == pre_desc["first_pairs"], f"{path.name}: post/pre first pairs mismatch")
    require(post_desc["first_pairs"] == return_desc["first_pairs"], f"{path.name}: return first pairs mismatch")
    require(pre_29a140["rsi_is_output_descriptor"], f"{path.name}: pre-29a140 rsi mismatch")
    require(pre_29a140["rdx_is_target_plus_0x208"], f"{path.name}: pre-29a140 rdx mismatch")
    require(pre_29a140["ecx_low32"] == 8, f"{path.name}: pre-29a140 ecx mismatch")

    store_samples = site_map.get("builder_after_output_store") or []
    require(len(store_samples) >= 8, f"{path.name}: store samples len {len(store_samples)}")
    for index, sample in enumerate(store_samples[:8]):
        formula = sample["store_formula"]
        require(formula["formula_matches_registers"], f"{path.name}: store {index} formula mismatch {formula}")
        stored = formula["stored_pair"]
        require(stored and stored[0]["u16_0x00"] == formula["reg_lower_r12w"], f"{path.name}: store lower mismatch {formula}")
        require(stored[0]["u16_0x02"] == formula["reg_count_dx"], f"{path.name}: store count mismatch {formula}")
        require(
            formula["store_addr"]
            == post_desc["data_0x20"] + 4 * (formula["x"] + formula["y"] * post_desc["stride_0x18"]),
            f"{path.name}: store address mismatch {formula}",
        )

    source_layer = pre["source_layer"]
    source_desc = source_layer["fields"]["descriptor_0x2a8"]
    source_mask = source_layer["fields"]["descriptor_0x208"]
    require(
        descriptor_shape(source_desc, width=1040, height=780, stride=1040),
        f"{path.name}: source +0x2a8 shape {source_desc}",
    )
    require(
        descriptor_shape(source_mask, width=1040, height=780, stride=1040),
        f"{path.name}: source +0x208 shape {source_mask}",
    )
    return packet, post_desc


def main():
    reports = sorted(path for path in ROOT.glob("source_range_*.json") if path.name in EXPECTED)
    require({path.name for path in reports} == EXPECTED, f"missing reports: {EXPECTED - {path.name for path in reports}}")
    for path in reports:
        packet, desc = validate(path)
        print(
            f"{path.name}: OK target={packet['target_object']:#x} "
            f"data={desc['data_0x20']:#x} first_pairs={desc['first_pairs'][:4]}"
        )


if __name__ == "__main__":
    main()
