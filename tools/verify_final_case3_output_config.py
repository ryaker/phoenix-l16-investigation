#!/usr/bin/env python3
"""Verify admitted final-compositing case-3 output-config evidence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_RUN = ROOT / "runs" / "codex_final_compositing_case1_case3_boundary"
HDR_RUN = ROOT / "runs" / "codex_final_output_hdr_writer_boundary"

ZOOMS = ("28mm", "35mm", "70mm", "150mm")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def event(report: dict, name: str) -> dict:
    matches = [item for item in report.get("events", []) if item.get("site_name") == name]
    require(len(matches) == 1, f"expected one event {name}, got {len(matches)}")
    return matches[0]["packet"]


def u32(value: int | None) -> int | None:
    if value is None:
        return None
    return value & 0xFFFFFFFF


def verify_static() -> None:
    static_path = CASE_RUN / "static_case1_case3_4182a0_windows.txt"
    text = static_path.read_text(encoding="utf-8")
    for needle in (
        "0x418703",
        "cmpl   $0x2, %r12d",
        "0x41870d",
        "cmpl   $0x3, %r12d",
        "0x418717",
        '"tone_mapping.type"',
        '"linear"',
        "0x418797",
        "0x41880f",
        "0x418823",
        "0x4188df",
        "0x418908",
        "callq  0x41e180",
    ):
        require(needle in text, f"static disassembly missing {needle}")


def verify_case_report(zoom: str) -> dict:
    report = load_json(CASE_RUN / f"case1_case3_{zoom}.json")
    require(report.get("errors") == [], f"{zoom} case report has errors")
    require(report.get("drive_hit_step_cap") is False, f"{zoom} case hit step cap")
    require(report.get("process", {}).get("exit_status") == 0, f"{zoom} case did not exit cleanly")

    counts = report["counts"]
    for va in ("0x3bcf16", "0x4186a3", "0x4188df", "0x418908", "0x418bfd"):
        require(counts.get(va) == 1, f"{zoom} expected one hit at {va}, got {counts.get(va)}")
    for va in ("0x418d38", "0x418e27"):
        require(counts.get(va) == 0, f"{zoom} expected zero hits at {va}, got {counts.get(va)}")

    call = event(report, "case3_call_4182a0")["case3_call_operands"]
    require(call["call_r8d_record_plus_0x68"] == 3, f"{zoom} case-3 format arg not 3")
    dims = call["record_plus_0x60_view"]
    require(dims["i32_0x00"] == 10432 and dims["i32_0x04"] == 7824, f"{zoom} case dims mismatch")
    require(dims["i32_0x08"] == 3, f"{zoom} case record+0x68/tag mismatch")

    color = event(report, "helper_color_space_branch")
    require(color["color_space_selector_eax"] == 4, f"{zoom} color selector not 4")
    require(u32(color["registers"]["r12"]) == 3, f"{zoom} helper r12d not 3 at color branch")
    locals_ = color["helper_locals"]
    require(locals_["local_i32_rbp_minus_0x3b8"] == 10432, f"{zoom} local width mismatch")
    require(locals_["local_i32_rbp_minus_0x3b4"] == 7824, f"{zoom} local height mismatch")
    require(locals_["local_i32_rbp_minus_0x3c0"] == 10432, f"{zoom} output width mismatch")
    require(locals_["local_i32_rbp_minus_0x3bc"] == 7824, f"{zoom} output height mismatch")

    writer_call = event(report, "helper_call_41e180")
    require(u32(writer_call["registers"]["r12"]) == 3, f"{zoom} helper r12d not 3 at 0x41e180 call")
    require(writer_call["call_args"]["r8"] == 3, f"{zoom} 0x41e180 call r8 not 3")

    return {
        "zoom": zoom,
        "color_selector": color["color_space_selector_eax"],
        "format": writer_call["call_args"]["r8"],
        "dims": "10432x7824",
    }


def verify_hdr_report(zoom: str) -> dict:
    report = load_json(HDR_RUN / f"hdr_writer_{zoom}.json")
    require(report.get("errors") == [], f"{zoom} HDR report has errors")
    require(report.get("drive_hit_step_cap") is False, f"{zoom} HDR hit step cap")
    require(report.get("process", {}).get("exit_status") == 0, f"{zoom} HDR did not exit cleanly")

    counts = report["counts"]
    for va in ("0x41e180", "0x41e599", "0x2326a0", "0x232731", "0x232733", "0x23274a"):
        require(counts.get(va) == 1, f"{zoom} expected one HDR hit at {va}, got {counts.get(va)}")
    for va in ("0x41e953", "0x41e9ea", "0x41fa93", "0x41fad4", "0x232758"):
        require(counts.get(va) == 0, f"{zoom} expected zero HDR hits at {va}, got {counts.get(va)}")

    entry = event(report, "helper_41e180_entry")["helper_entry_args"]
    require(entry["format_r8d"] == 3, f"{zoom} 0x41e180 entry format not 3")
    require(entry["dims_rdx"]["i32_0x00"] == 10432, f"{zoom} 0x41e180 width mismatch")
    require(entry["dims_rdx"]["i32_0x04"] == 7824, f"{zoom} 0x41e180 height mismatch")

    call = event(report, "helper_call_2326a0_hdr_writer")["helper_hdr_writer_call"]
    desc = call["descriptor_rdi"]
    require(call["extension_rsi_string"]["text_capped"] == ".hdr", f"{zoom} extension not .hdr")
    require(desc["i32_0x10_width"] == 10432, f"{zoom} writer descriptor width mismatch")
    require(desc["i32_0x14_height"] == 7824, f"{zoom} writer descriptor height mismatch")
    require(desc["i32_0x18_stride_or_count"] == 10432, f"{zoom} writer descriptor stride mismatch")
    require(desc["u64_0x20_data"] not in (0, None), f"{zoom} writer descriptor data missing")

    virt = event(report, "writer_virtual_write_call")["writer_virtual_call"]["call_descriptor_rdx"]
    require(virt["i32_0x00_width"] == 10432, f"{zoom} virtual width mismatch")
    require(virt["i32_0x04_height"] == 7824, f"{zoom} virtual height mismatch")
    require(virt["i32_0x10_bytes_per_pixel"] == 16, f"{zoom} virtual bpp mismatch")
    require(virt["i64_0x08_row_bytes"] == 10432 * 16, f"{zoom} virtual row bytes mismatch")
    require(virt["u64_0x18_data"] == desc["u64_0x20_data"], f"{zoom} virtual data pointer changed")

    return {
        "zoom": zoom,
        "extension": call["extension_rsi_string"]["text_capped"],
        "row_bytes": virt["i64_0x08_row_bytes"],
        "bpp": virt["i32_0x10_bytes_per_pixel"],
    }


def main() -> None:
    verify_static()
    rows = []
    for zoom in ZOOMS:
        case = verify_case_report(zoom)
        hdr = verify_hdr_report(zoom)
        rows.append({**case, **hdr})

    for row in rows:
        print(
            f"{row['zoom']}: OK dims={row['dims']} format={row['format']} "
            f"color_selector={row['color_selector']} ext={row['extension']} "
            f"row_bytes={row['row_bytes']} bpp={row['bpp']}"
        )


if __name__ == "__main__":
    main()
