#!/usr/bin/env python3
"""Verify cross-object pair-vector custody through State body 0x22ae60."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

UNIT1_RUN = ROOT / "runs" / "prefusion_node_dest_20ca00_source_index"
UNIT1_TIERS = ("28mm", "35mm", "70mm", "150mm")
UNIT2_RUN = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_custody_unit2"
UNIT2_REPORT = UNIT2_RUN / "node_dest_20ca00_gate_unit2_28mm.json"
UNIT2_HDR = UNIT2_RUN / "node_dest_20ca00_gate_unit2_28mm.hdr"
UNIT2_SCRIPT = (
    ROOT
    / "tools"
    / "lldb_probes"
    / "prefusion_node_dest_sentinel_custody"
    / "node_dest_20ca00_gate_unit2_28mm.lldb"
)
UNIT2_LRI = "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"
LIVE_HANDLE_RUN = ROOT / "runs" / "state5_handle_identity_two_body"
LIVE_HANDLE_SCRIPTS = {
    "Unit-1 exact 28mm State handle": (
        ROOT
        / "tools"
        / "lldb_probes"
        / "calib_state_operator_runtime"
        / "state5_handle_identity_unit1_28mm.lldb",
        "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
        "state5_handle_identity_unit1_28mm",
    ),
    "Unit-1 exact 35mm State handle": (
        ROOT
        / "tools"
        / "lldb_probes"
        / "calib_state_operator_runtime"
        / "state5_handle_identity_unit1_35mm.lldb",
        "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri",
        "state5_handle_identity_unit1_35mm",
    ),
    "Unit-1 exact 70mm State handle": (
        ROOT
        / "tools"
        / "lldb_probes"
        / "calib_state_operator_runtime"
        / "state5_handle_identity_unit1_70mm.lldb",
        "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
        "state5_handle_identity_unit1_70mm",
    ),
    "Unit-1 exact 150mm State handle": (
        ROOT
        / "tools"
        / "lldb_probes"
        / "calib_state_operator_runtime"
        / "state5_handle_identity_unit1_150mm.lldb",
        "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
        "state5_handle_identity_unit1_150mm",
    ),
    "Unit-2 exact 28mm State handle": (
        ROOT
        / "tools"
        / "lldb_probes"
        / "calib_state_operator_runtime"
        / "state5_handle_identity_unit2_28mm.lldb",
        UNIT2_LRI,
        "state5_handle_identity_unit2_28mm",
    ),
}

SENTINEL_HEX = "000080bf000080bf"
COPY_RETURN_PRE_OWNER = 0x20ADF6
COPY_RETURN_SIBLING = 0x239C34
COPY_RETURN_SIBLING_LOCAL = 0x239FD9
COPY_RETURN_POST_OWNER = 0x20BFFA
STATE_AFTER_PRE_OWNER = 0x22AE73
STATE_AFTER_FIRST_SIBLING = 0x22AE83
STATE_AFTER_POST_OWNER = 0x22AE8C
STATE_AFTER_SECOND_SIBLING = 0x22AE9C

WINDOWS = (
    (0x20AC60, 0x20ADC0),
    (0x20ADA0, 0x20AE10),
    (0x20BD60, 0x20C010),
    (0x225160, 0x225700),
    (0x226C70, 0x227000),
    (0x22ADF0, 0x22AE30),
    (0x22AE60, 0x22AEA8),
    (0x2399A0, 0x239B00),
    (0x239AC0, 0x23A040),
    (0x3FC980, 0x3FC9A4),
)

ANCHORS = {
    0x20AC71: ("mov", "qword ptr [rbp - 0x30], r9"),
    0x20AC75: ("mov", "qword ptr [rbp - 0x38], r8"),
    0x20AC79: ("mov", "r12, rcx"),
    0x20AC7C: ("mov", "r13, rdx"),
    0x20AC7F: ("mov", "rbx, rdi"),
    0x20AC82: ("mov", "r15, qword ptr [rsi]"),
    0x20AC96: ("mov", "qword ptr [rbx + 0x38], r15"),
    0x20AC9E: ("mov", "qword ptr [rbx + 0x40], r14"),
    0x20ACAC: ("mov", "r15, qword ptr [r13]"),
    0x20ACC1: ("mov", "qword ptr [rbx + 0x48], r15"),
    0x20ACC9: ("mov", "qword ptr [rbx + 0x50], r14"),
    0x20ACD7: ("mov", "r15, qword ptr [r12]"),
    0x20ACED: ("mov", "qword ptr [rbx], r15"),
    0x20ACF4: ("mov", "qword ptr [rbx + 8], r14"),
    0x20AD02: ("mov", "rax, qword ptr [rbp - 0x38]"),
    0x20AD1A: ("mov", "qword ptr [rbx + 0x28], r15"),
    0x20AD22: ("mov", "qword ptr [rbx + 0x30], r14"),
    0x20AD30: ("mov", "rcx, qword ptr [rbp - 0x30]"),
    0x20AD36: ("mov", "dword ptr [rbx + 0x70], eax"),
    0x20AD3C: ("mov", "dword ptr [rbx + 0x74], eax"),
    0x20AD3F: ("movabs", "rax, 0xbf800000bf800000"),
    0x20AD49: ("mov", "qword ptr [rbx + 0x78], rax"),
    0x20AD60: ("push", "rbp"),
    0x20AD8F: ("jmp", "0x20ac60"),
    0x20ADB1: ("mov", "r15, rdi"),
    0x20ADB9: ("mov", "r13, qword ptr [r15 + 0x28]"),
    0x20ADE8: ("lea", "rsi, [r12 + 0x28]"),
    0x20ADF1: ("call", "0xe0ae0"),
    0x20BD74: ("mov", "r15, rdi"),
    0x20BFBB: ("mov", "r12, qword ptr [r15 + 0x28]"),
    0x20BFEA: ("lea", "rsi, [r14 + 0x28]"),
    0x20BFF5: ("call", "0xe0ae0"),
    0x225171: ("mov", "r14, rcx"),
    0x225174: ("mov", "r15, rdx"),
    0x225177: ("mov", "r13, rdi"),
    0x22518E: ("mov", "qword ptr [r13 + 0x30], r12"),
    0x2251B8: ("mov", "qword ptr [r13 + 0xa0], r12"),
    0x2251DA: ("mov", "dword ptr [r13 + 0x100], eax"),
    0x2251E5: ("mov", "dword ptr [r13 + 0x104], eax"),
    0x225451: ("lea", "r12, [r13 + 0x30]"),
    0x2254FC: ("lea", "r15, [r13 + 0xa0]"),
    0x225522: ("lea", "r12, [r13 + 0x100]"),
    0x225529: ("lea", "rax, [r13 + 0x40]"),
    0x225531: ("lea", "rax, [r13 + 0x50]"),
    0x2255BB: ("mov", "edi, 0x80"),
    0x2255C8: ("mov", "rdi, r14"),
    0x2255CB: ("mov", "rsi, qword ptr [rbp - 0x50]"),
    0x2255CF: ("mov", "rdx, r15"),
    0x2255D2: ("mov", "rcx, qword ptr [rbp - 0x58]"),
    0x2255D6: ("mov", "r8, qword ptr [rbp - 0x60]"),
    0x2255DA: ("mov", "r9, r12"),
    0x2255DD: ("call", "0x20ad60"),
    0x2255E2: ("mov", "rbx, qword ptr [r13 + 0x10]"),
    0x2255E6: ("mov", "qword ptr [r13 + 0x10], r14"),
    0x225668: ("mov", "edi, 0x58"),
    0x225675: ("mov", "rdi, r14"),
    0x225678: ("mov", "rsi, qword ptr [rbp - 0x50]"),
    0x22567C: ("mov", "rdx, r15"),
    0x22567F: ("mov", "rcx, qword ptr [rbp - 0x58]"),
    0x225683: ("mov", "r8, qword ptr [rbp - 0x60]"),
    0x225687: ("call", "0x239a90"),
    0x22568C: ("mov", "rbx, qword ptr [r13 + 0x28]"),
    0x225690: ("mov", "qword ptr [r13 + 0x28], r14"),
    0x226C84: ("mov", "r12, rdi"),
    0x226F8F: ("lea", "rax, [rip + 0x431642]"),
    0x226F96: ("mov", "qword ptr [rbp - 0x270], rax"),
    0x226F9D: ("mov", "qword ptr [rbp - 0x268], r12"),
    0x22AE03: ("lea", "rcx, [rip + 0x42d7ce]"),
    0x22AE11: ("mov", "qword ptr [rax + 8], rcx"),
    0x22AE24: ("lea", "rax, [rip + 0x42d7ad]"),
    0x22AE66: ("mov", "rbx, qword ptr [rdi + 8]"),
    0x22AE6A: ("mov", "rdi, qword ptr [rbx + 0x10]"),
    0x22AE6E: ("call", "0x20ada0"),
    0x22AE73: ("mov", "rdi, qword ptr [rbx + 0x28]"),
    0x22AE7E: ("call", "0x239ac0"),
    0x22AE83: ("mov", "rdi, qword ptr [rbx + 0x10]"),
    0x22AE87: ("call", "0x20bd60"),
    0x22AE8C: ("mov", "rdi, qword ptr [rbx + 0x28]"),
    0x22AE97: ("call", "0x239ac0"),
    0x2399AE: ("mov", "qword ptr [rbp - 0x30], r8"),
    0x2399B2: ("mov", "r15, rcx"),
    0x2399B5: ("mov", "r12, rdx"),
    0x2399B8: ("mov", "rbx, rdi"),
    0x2399BB: ("mov", "r14, qword ptr [rsi]"),
    0x2399CF: ("mov", "qword ptr [rbx + 0x20], r14"),
    0x2399D7: ("mov", "qword ptr [rbx + 0x28], r13"),
    0x2399E5: ("mov", "r14, qword ptr [r12]"),
    0x2399FB: ("mov", "qword ptr [rbx + 0x30], r14"),
    0x239A03: ("mov", "qword ptr [rbx + 0x38], r12"),
    0x239A11: ("mov", "r14, qword ptr [r15]"),
    0x239A25: ("mov", "qword ptr [rbx], r14"),
    0x239A2C: ("mov", "qword ptr [rbx + 8], r15"),
    0x239A3A: ("mov", "rax, qword ptr [rbp - 0x30]"),
    0x239A52: ("mov", "qword ptr [rbx + 0x10], r15"),
    0x239A5A: ("mov", "qword ptr [rbx + 0x18], r14"),
    0x239A90: ("push", "rbp"),
    0x239AB3: ("jmp", "0x2399a0"),
    0x239AD5: ("mov", "r12, rdi"),
    0x239BFD: ("mov", "rax, qword ptr [r12 + 0x10]"),
    0x239C27: ("lea", "rsi, [r15 + 0x28]"),
    0x239C2F: ("call", "0xe0ae0"),
    0x239E2C: ("mov", "rax, qword ptr [r14]"),
    0x239ECF: ("add", "rdi, 0x14"),
    0x239FD4: ("call", "0xe0ae0"),
    0x3FC980: ("mov", "rdi, qword ptr [rdi + 8]"),
    0x3FC984: ("cmp", "byte ptr [rdi + 0x3fa], 0"),
    0x3FC991: ("add", "rdi, 0x280"),
    0x3FC998: ("call", "0x226c70"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_clean(report: dict, label: str) -> None:
    require(report.get("process_exit_status") == 0, f"{label}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{label}: step cap hit")
    require(report.get("errors") == [], f"{label}: probe errors {report.get('errors')}")


def require_state_operator_clean(report: dict, label: str) -> None:
    process = report.get("process") or {}
    require(process.get("exit_status") == 0, f"{label}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{label}: step cap hit")
    require(report.get("errors") == [], f"{label}: probe errors {report.get('errors')}")


def require_hdr(path: Path, label: str) -> None:
    require(path.exists(), f"{label}: missing HDR {path}")
    with path.open("rb") as handle:
        require(handle.read(16).startswith(b"#?RADIANCE"), f"{label}: invalid HDR")


def stack_va(sample: dict, index: int) -> int | None:
    stack = sample.get("stack") or []
    if index >= len(stack):
        return None
    return stack[index].get("libcp_va")


def pair_samples(report: dict, address: int) -> list[dict]:
    samples = [
        sample
        for sample in report.get("watchpoint_samples") or []
        if sample.get("watch_addr") == address
    ]
    require(samples, f"0x{address:x}: no watchpoint samples")
    for sample in samples:
        pair = sample.get("pair_now") or {}
        require(pair.get("hex") == SENTINEL_HEX, f"0x{address:x}: pair bytes drift")
        require(pair.get("is_sentinel_neg1_neg1") is True, f"0x{address:x}: pair state drift")
    return samples


def stage_positions(samples: list[dict], include_second_sibling: bool) -> dict[str, int]:
    predicates = {
        "pre_owner": lambda sample: (
            stack_va(sample, 1) == COPY_RETURN_PRE_OWNER
            and stack_va(sample, 2) == STATE_AFTER_PRE_OWNER
        ),
        "first_sibling": lambda sample: (
            stack_va(sample, 1) == COPY_RETURN_SIBLING
            and stack_va(sample, 2) == STATE_AFTER_FIRST_SIBLING
        ),
        "post_owner": lambda sample: (
            stack_va(sample, 1) == COPY_RETURN_POST_OWNER
            and stack_va(sample, 2) == STATE_AFTER_POST_OWNER
        ),
    }
    if include_second_sibling:
        predicates["second_sibling"] = lambda sample: (
            stack_va(sample, 1) == COPY_RETURN_SIBLING
            and stack_va(sample, 2) == STATE_AFTER_SECOND_SIBLING
        )

    positions: dict[str, int] = {}
    for name, predicate in predicates.items():
        positions[name] = next(
            (index for index, sample in enumerate(samples) if predicate(sample)),
            -1,
        )
        require(positions[name] >= 0, f"missing {name} same-address stage")

    expected_order = ["pre_owner", "first_sibling", "post_owner"]
    if include_second_sibling:
        expected_order.append("second_sibling")
    ordered = [positions[name] for name in expected_order]
    require(ordered == sorted(ordered) and len(set(ordered)) == len(ordered), f"stage order drift: {positions}")
    return positions


def matched_address(report: dict, label: str) -> int:
    matches = report.get("matches") or []
    require(matches, f"{label}: no same-address matches")
    address = matches[0].get("pair_addr")
    require(isinstance(address, int) and address > 0, f"{label}: invalid pair address")
    after = matches[0].get("pair_after_y_store") or {}
    require(after.get("addr") == address, f"{label}: match address drift")
    require(after.get("hex") == SENTINEL_HEX, f"{label}: match did not become sentinel")
    return address


def verify_static(libcp: Path) -> None:
    blob = libcp.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == LIBCP_SHA256, "libcp SHA-256 drift")
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions: dict[int, tuple[str, str]] = {}
    for begin, end in WINDOWS:
        instructions.update(
            (instruction.address, (instruction.mnemonic, instruction.op_str))
            for instruction in disassembler.disasm(blob[begin:end], begin)
        )
    for address, expected in ANCHORS.items():
        require(
            instructions.get(address) == expected,
            f"static anchor drift at 0x{address:x}: {instructions.get(address)}",
        )


def verify_unit1(tier: str) -> tuple[int, dict[str, int]]:
    label = f"Unit-1 {tier}"
    report_path = UNIT1_RUN / f"node_dest_20ca00_index_{tier}.json"
    hdr_path = UNIT1_RUN / f"node_dest_20ca00_index_{tier}.hdr"
    report = load_json(report_path)
    require_clean(report, label)
    require_hdr(hdr_path, label)
    address = matched_address(report, label)
    samples = pair_samples(report, address)
    return address, stage_positions(samples, include_second_sibling=False)


def verify_unit2() -> tuple[int, dict[str, int], int]:
    label = "Unit-2 exact 28mm"
    script = UNIT2_SCRIPT.read_text(encoding="utf-8")
    require(UNIT2_LRI in script, f"{label}: LRI path drift")
    report = load_json(UNIT2_REPORT)
    require_clean(report, label)
    require_hdr(UNIT2_HDR, label)
    address = matched_address(report, label)
    samples = pair_samples(report, address)
    positions = stage_positions(samples, include_second_sibling=True)
    local_copy_hits = sum(
        1 for sample in samples if stack_va(sample, 1) == COPY_RETURN_SIBLING_LOCAL
    )
    require(local_copy_hits > 0, f"{label}: no 0x239fd9 sibling-local copy hits")
    return address, positions, local_copy_hits


def require_pair(pair: dict, label: str) -> tuple[int, int]:
    require(pair.get("read_ok") is True, f"{label}: pair unreadable")
    pointer = pair.get("pointer")
    control = pair.get("control")
    require(isinstance(pointer, int) and pointer > 0, f"{label}: invalid pointer")
    require(isinstance(control, int) and control > 0, f"{label}: invalid control")
    return pointer, control


def require_same_pair(report: dict, names: tuple[str, str, str], label: str) -> tuple[int, int]:
    upstream, owner, sibling = names
    upstream_pair = report["upstream_pairs"][upstream]
    owner_pair = report["owner_pairs"][owner]
    sibling_pair = report["sibling_pairs"][sibling]
    values = {
        require_pair(upstream_pair, f"{label}: {upstream}"),
        require_pair(owner_pair, f"{label}: {owner}"),
        require_pair(sibling_pair, f"{label}: {sibling}"),
    }
    require(len(values) == 1, f"{label}: {upstream}/{owner}/{sibling} handle mismatch")
    return values.pop()


def verify_live_state5_handle(label: str, script: Path, lri_path: str, stem: str) -> dict:
    script_text = script.read_text(encoding="utf-8")
    require(lri_path in script_text, f"{label}: LRI path drift")
    require("0x22ae60" in script_text, f"{label}: State-5 breakpoint missing")

    report_path = LIVE_HANDLE_RUN / f"{stem}.json"
    hdr_path = LIVE_HANDLE_RUN / f"{stem}.hdr"
    report = load_json(report_path)
    require_state_operator_clean(report, label)
    require_hdr(hdr_path, label)

    samples = (report.get("samples") or {}).get("0x22ae60") or []
    require(samples, f"{label}: no State-5 samples")
    handles = samples[0].get("state5_handles") or {}
    require(handles.get("read_ok") is True, f"{label}: handle packet unreadable")
    require(handles.get("owner") != handles.get("sibling"), f"{label}: owner/sibling unexpectedly identical")

    equalities = handles.get("mapping_equalities") or {}
    expected_equalities = {
        "inner_40_owner_00_sibling_00",
        "inner_50_owner_28_sibling_10",
        "inner_30_owner_38_sibling_20",
        "inner_a0_owner_48_sibling_30",
    }
    require(set(equalities) == expected_equalities, f"{label}: equality key drift {equalities}")
    require(all(equalities.values()), f"{label}: one or more handle equalities failed {equalities}")

    top_handle = require_same_pair(
        handles,
        ("inner_40", "owner_00", "sibling_00"),
        label,
    )
    keyed_handle = require_same_pair(
        handles,
        ("inner_50", "owner_28", "sibling_10"),
        label,
    )
    require_same_pair(handles, ("inner_30", "owner_38", "sibling_20"), label)
    require_same_pair(handles, ("inner_a0", "owner_48", "sibling_30"), label)

    top = handles.get("top_record_vector") or {}
    require(top.get("read_ok") is True, f"{label}: top record vector unreadable")
    top_bytes = top.get("bytes")
    require(isinstance(top_bytes, int) and top_bytes > 0, f"{label}: invalid top vector bytes")
    require(top_bytes % 0x14 == 0, f"{label}: top vector is not 0x14-stride")

    keyed = handles.get("keyed_record_tree_prefix") or {}
    require(keyed.get("read_ok") is True, f"{label}: keyed tree prefix unreadable")
    qwords = keyed.get("qwords")
    require(isinstance(qwords, list) and len(qwords) == 3, f"{label}: keyed prefix shape drift")

    return {
        "top_handle": top_handle,
        "top_records": top_bytes // 0x14,
        "keyed_handle": keyed_handle,
        "keyed_prefix": qwords,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libcp", type=Path, default=DEFAULT_LIBCP)
    args = parser.parse_args()

    verify_static(args.libcp)
    print(f"binary={args.libcp} sha256={LIBCP_SHA256}")
    for tier in UNIT1_TIERS:
        address, positions = verify_unit1(tier)
        print(f"Unit-1 {tier}: OK same_addr={address} stages={positions}")
    address, positions, local_copy_hits = verify_unit2()
    print(
        "Unit-2 exact 28mm: OK "
        f"same_addr={address} stages={positions} sibling_local_copy_hits={local_copy_hits}"
    )
    for label, (script, lri_path, stem) in LIVE_HANDLE_SCRIPTS.items():
        live = verify_live_state5_handle(label, script, lri_path, stem)
        print(
            f"{label}: OK "
            f"top_records={live['top_records']} "
            f"top_handle={live['top_handle']} keyed_handle={live['keyed_handle']}"
        )
    print(
        "scope=shared pair-vector allocation across owner +0x10 and sibling +0x28 record loops; "
        "live Unit-1 four-focal shared-handle identity plus exact-28mm Unit-2 discriminator; "
        "all-record sharing, image effect, reducer closure, and final acceptance remain open"
    )


if __name__ == "__main__":
    main()
