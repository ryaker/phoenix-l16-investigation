#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "runs/codex_final_case3_to_hdr_writer_custody"

EXPECTED = {
    "case3_writer_28mm.json": {"label": "Unit-1 28mm", "full": True},
    "case3_writer_35mm.json": {"label": "Unit-1 35mm", "full": True},
    "case3_writer_70mm.json": {"label": "Unit-1 70mm", "full": True},
    "case3_writer_150mm_min.json": {"label": "Unit-1 150mm", "full": False},
    "case3_writer_unit2_28mm.json": {"label": "Unit-2 exact 28mm", "full": True},
}

REQUIRED_POSITIVE = (
    "0x3bcf16",
    "0x4182a0",
    "0x418908",
    "0x41e180",
    "0x41e599",
    "0x2326a0",
    "0x232731",
    "0x232733",
)

REQUIRED_FULL_RETURNS = (
    "0x418bfd",
    "0x41f9eb",
)

REQUIRED_ZERO = (
    "0x418d38",
    "0x418e27",
    "0x41e953",
    "0x41e9ea",
    "0x41fa93",
    "0x41fad4",
    "0x232758",
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def site_packet(report, site):
    packets = [
        event["packet"]
        for event in report["events"]
        if event.get("packet", {}).get("site_va") == site
    ]
    require(len(packets) == 1, f"{report['label']}: expected one packet for {site}, got {len(packets)}")
    return packets[0]


def dims_tuple(view):
    return (view["i32_0x00"], view["i32_0x04"], view["i32_0x08"])


def dims_wh(view):
    return (view["i32_0x00"], view["i32_0x04"])


def descriptor_tuple(desc):
    return (
        desc["i32_0x10_width"],
        desc["i32_0x14_height"],
        desc["i32_0x18_stride_or_count"],
        desc["i32_0x1c"],
        desc["u64_0x20_data"],
    )


def check_report(path, full=True):
    report = json.loads(path.read_text())
    label = report["label"]
    require(report["process"]["exit_status"] == 0, f"{label}: nonzero exit")
    require(report["process"]["state"] == "exited", f"{label}: process did not exit")
    require(not report["errors"], f"{label}: probe errors {report['errors']}")
    require(not report["drive_hit_step_cap"], f"{label}: hit step cap")

    counts = report["counts"]
    for site in REQUIRED_POSITIVE:
        require(counts.get(site) == 1, f"{label}: {site} count {counts.get(site)}")
    if full:
        for site in REQUIRED_FULL_RETURNS:
            require(counts.get(site) == 1, f"{label}: {site} count {counts.get(site)}")
        for site in REQUIRED_ZERO:
            require(counts.get(site) == 0, f"{label}: {site} count {counts.get(site)}")

    case3 = site_packet(report, "0x3bcf16")["case3_call"]
    require(case3["matches_context"], f"{label}: case3 context mismatch")
    for offset in ("0x10", "0x20", "0x50", "0x60"):
        require(case3[f"matches_record_plus_{offset}"], f"{label}: record+{offset} mismatch")
    require(case3["arg_r8d_record_plus_0x68"] == 3, f"{label}: case3 format is not 3")
    require(dims_tuple(case3["record_plus_0x60_dims"]) == (10432, 7824, 3), f"{label}: record+0x60 dims")

    entry_4182a0 = site_packet(report, "0x4182a0")["helper_4182a0_entry_args"]
    require(entry_4182a0["context_rdi"] == case3["context_rdi"], f"{label}: 4182a0 context changed")
    require(entry_4182a0["arg_rsi_view"]["addr"] == case3["arg_rsi_record_plus_0x10"], f"{label}: 4182a0 rsi custody")
    require(entry_4182a0["arg_rdx_dims"]["addr"] == case3["arg_rdx_record_plus_0x60"], f"{label}: 4182a0 rdx custody")
    require(entry_4182a0["arg_r9_view"]["addr"] == case3["arg_r9_record_plus_0x20"], f"{label}: 4182a0 r9 custody")
    require(dims_tuple(entry_4182a0["arg_rdx_dims"]) == (10432, 7824, 3), f"{label}: 4182a0 dims")

    call_41e180 = site_packet(report, "0x418908")["helper_4182a0_call_41e180"]
    require(call_41e180["arg_rsi_view"]["addr"] == case3["arg_rsi_record_plus_0x10"], f"{label}: 418908 rsi custody")
    require(call_41e180["record20_r9_view"]["addr"] == case3["arg_r9_record_plus_0x20"], f"{label}: 418908 r9 custody")
    require(call_41e180["format_r8d"] == 3, f"{label}: 418908 format")
    require(dims_wh(call_41e180["dims_rdx"]) == (10432, 7824), f"{label}: 418908 stack dims")

    entry_41e180 = site_packet(report, "0x41e180")["helper_41e180_entry_args"]
    require(entry_41e180["context_rdi"] == call_41e180["context_rdi"], f"{label}: 41e180 context")
    require(entry_41e180["arg_rsi_view"]["addr"] == case3["arg_rsi_record_plus_0x10"], f"{label}: 41e180 rsi custody")
    require(entry_41e180["record20_r9_view"]["addr"] == case3["arg_r9_record_plus_0x20"], f"{label}: 41e180 r9 custody")
    require(entry_41e180["dims_rdx"]["addr"] == call_41e180["dims_rdx"]["addr"], f"{label}: 41e180 dims addr")
    require(entry_41e180["format_r8d"] == 3, f"{label}: 41e180 format")
    require(dims_wh(entry_41e180["dims_rdx"]) == (10432, 7824), f"{label}: 41e180 dims")

    hdr_call = site_packet(report, "0x41e599")["helper_41e180_hdr_writer_call"]
    desc = hdr_call["descriptor_rdi"]
    require(descriptor_tuple(desc)[:4] == (10432, 7824, 10432, 7824), f"{label}: HDR descriptor shape")
    require(desc["u64_0x20_data"], f"{label}: HDR descriptor data is zero")
    require(hdr_call["extension_rsi_string"]["text_capped"] == ".hdr", f"{label}: HDR extension")
    require(hdr_call["third_arg_rdx_view"]["addr"] == case3["arg_rsi_record_plus_0x10"], f"{label}: HDR third arg custody")

    writer_entry = site_packet(report, "0x2326a0")["writer_entry_args"]
    require(descriptor_tuple(writer_entry["descriptor_rdi"]) == descriptor_tuple(desc), f"{label}: writer entry descriptor")
    require(writer_entry["extension_rsi_string"]["text_capped"] == ".hdr", f"{label}: writer entry extension")
    require(writer_entry["third_arg_rdx_view"]["addr"] == case3["arg_rsi_record_plus_0x10"], f"{label}: writer entry third arg")

    virtual = site_packet(report, "0x232731")["writer_virtual_call"]
    call_desc = virtual["call_descriptor_rdx"]
    require(call_desc["i32_0x00_width"] == 10432, f"{label}: virtual width")
    require(call_desc["i32_0x04_height"] == 7824, f"{label}: virtual height")
    require(call_desc["i64_0x08_row_bytes"] == 10432 * 16, f"{label}: virtual row bytes")
    require(call_desc["i32_0x10_bytes_per_pixel"] == 16, f"{label}: virtual bpp")
    require(call_desc["u64_0x18_data"] == desc["u64_0x20_data"], f"{label}: virtual data pointer")
    require(virtual["third_arg_rsi_view"]["addr"] == case3["arg_rsi_record_plus_0x10"], f"{label}: virtual third arg")

    return {
        "label": label,
        "record": case3["record_r13"],
        "record_plus_0x60": case3["arg_rdx_record_plus_0x60"],
        "stack_dims": call_41e180["dims_rdx"]["addr"],
        "descriptor": desc["addr"],
        "data": desc["u64_0x20_data"],
    }


def main():
    summaries = []
    for filename, spec in EXPECTED.items():
        path = RUN_DIR / filename
        require(path.exists(), f"missing report: {path}")
        summary = check_report(path, full=spec["full"])
        require(spec["label"] in summary["label"], f"{filename}: label mismatch")
        summary["full"] = spec["full"]
        summaries.append(summary)

    print("final case3-to-HDR-writer custody: OK")
    for summary in summaries:
        print(
            f"{summary['label']}: record=0x{summary['record']:x} "
            f"record+0x60=0x{summary['record_plus_0x60']:x} "
            f"stack_dims=0x{summary['stack_dims']:x} "
            f"descriptor=0x{summary['descriptor']:x} data=0x{summary['data']:x} "
            f"full_error_scope={summary['full']}"
        )


if __name__ == "__main__":
    main()
