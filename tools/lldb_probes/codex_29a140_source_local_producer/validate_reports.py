#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/codex_29a140_source_local_producer")
REQUIRED_SITES = {
    "caller_pre_29a140",
    "maker_29a140_entry",
    "maker_after_299eb0",
    "maker_after_header_copy_28f490",
    "maker_after_299fd0",
    "caller_post_29a140",
    "caller_pre_header_move_28f420",
    "caller_pre_descriptor_move_f340",
    "later_source_index_branch",
    "later_299c70_entry",
    "later_267010_entry",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def samples_by_site(packet):
    return {
        sample["site"]: sample
        for sample in packet.get("samples", [])
        if sample.get("site") in REQUIRED_SITES
    }


def validate_report(path):
    packet = json.loads(path.read_text())
    process = packet["process"]
    require(process["state"] == "exited", f"{path.name}: process did not exit")
    require(process["exit_status"] == 0, f"{path.name}: nonzero exit {process}")
    require(not packet.get("drive_hit_step_cap"), f"{path.name}: hit step cap")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")

    target_counts = packet["target_counts"]
    missing = REQUIRED_SITES - set(target_counts)
    require(not missing, f"{path.name}: missing target sites {sorted(missing)}")
    for site in sorted(REQUIRED_SITES):
        require(target_counts[site] == 1, f"{path.name}: {site} count {target_counts[site]}")

    samples = samples_by_site(packet)
    pre = samples["caller_pre_29a140"]
    entry = samples["maker_29a140_entry"]
    after_299eb0 = samples["maker_after_299eb0"]
    after_copy = samples["maker_after_header_copy_28f490"]
    after_299fd0 = samples["maker_after_299fd0"]
    caller_post = samples["caller_post_29a140"]
    header_move = samples["caller_pre_header_move_28f420"]
    desc_move = samples["caller_pre_descriptor_move_f340"]

    require(pre["call_args"] == entry["entry_args"], f"{path.name}: entry args mismatch")
    call_args = pre["call_args"]
    require(call_args["rdi_is_output_local"], f"{path.name}: rdi not output local")
    require(call_args["rsi_is_input_descriptor"], f"{path.name}: rsi not input descriptor")
    require(call_args["rdx_is_target_plus_0x208"], f"{path.name}: rdx not target+0x208")
    require(call_args["ecx_low32"] == 8, f"{path.name}: ecx not 8")

    require(
        after_299eb0["output_local"]["control_u32_0x00"] == 8,
        f"{path.name}: control not 8 after 0x299eb0",
    )
    require(
        after_299eb0["output_local"]["header_qwords_0x08_0x20"] == [0, 0, 0],
        f"{path.name}: header not still zero after 0x299eb0",
    )
    require(
        after_copy["output_local"]["header_qwords_0x08_0x20"][0] != 0,
        f"{path.name}: header not populated after 0x28f490",
    )
    require(
        after_copy["output_local"]["descriptor_0x20"]["width_0x10"] == 0,
        f"{path.name}: descriptor populated before 0x299fd0",
    )

    output = after_299fd0["output_local"]
    require(output["control_u32_0x00"] == 8, f"{path.name}: final control not 8")
    desc = output["descriptor_0x20"]
    require(desc["read_ok"], f"{path.name}: descriptor unreadable")
    require(desc["width_0x10"] == 2080, f"{path.name}: width {desc}")
    require(desc["height_0x14"] == 1560, f"{path.name}: height {desc}")
    require(desc["stride_0x18"] == 2080, f"{path.name}: stride {desc}")
    require(desc["field_0x1c"] == 1560, f"{path.name}: field_0x1c {desc}")
    require(
        caller_post["output_local"]["qwords_0x00_0x50"] == output["qwords_0x00_0x50"],
        f"{path.name}: caller post local mismatch",
    )

    require(
        header_move["move_28f420"]["dest_is_target_plus_0x100"],
        f"{path.name}: header move dest mismatch",
    )
    require(
        header_move["move_28f420"]["src_is_output_plus_0x08"],
        f"{path.name}: header move source mismatch",
    )
    require(
        desc_move["move_f340"]["dest_is_target_plus_0x118"],
        f"{path.name}: descriptor move dest mismatch",
    )
    require(
        desc_move["move_f340"]["src_is_output_plus_0x20"],
        f"{path.name}: descriptor move source mismatch",
    )

    require(
        samples["later_299c70_entry"]["rsi_equals_target_plus_0xf8"],
        f"{path.name}: later 0x299c70 source mismatch",
    )
    require(
        samples["later_267010_entry"]["rdx_equals_target_plus_0xe0"],
        f"{path.name}: later 0x267010 lookup mismatch",
    )

    records = after_299fd0["post_299fd0_record_samples"]
    require(records["available"], f"{path.name}: record samples unavailable")
    require(records["stride"] == 2080, f"{path.name}: record stride {records}")
    require(records["first_offsets"], f"{path.name}: no record offsets")
    return packet, records


def main():
    reports = sorted(ROOT.glob("source_local_*.json"))
    require(len(reports) == 4, f"expected 4 reports, found {len(reports)}")
    for path in reports:
        packet, records = validate_report(path)
        print(
            f"{path.name}: OK target={packet['target_object']:#x} "
            f"record_base={records['record_base']:#x} "
            f"offset_table={records['offset_table']:#x} "
            f"first_offsets={records['first_offsets'][:4]}"
        )


if __name__ == "__main__":
    main()
