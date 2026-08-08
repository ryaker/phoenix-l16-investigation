#!/usr/bin/env python3
"""Verify the exact masked min/max policy used before G-40 range building."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
REPORT = ROOT / "runs/index5_range_pool_policy/unit1_28mm/report.json"
PRIOR_REPORTS = {
    "unit1_28mm": ROOT / "runs/codex_26d750_source_range_builder/source_range_28mm.json",
    "unit1_35mm": ROOT / "runs/codex_26d750_source_range_builder/source_range_35mm.json",
    "unit1_70mm": ROOT / "runs/codex_26d750_source_range_builder/source_range_70mm.json",
    "unit1_150mm": ROOT / "runs/codex_26d750_source_range_builder/source_range_150mm.json",
    "unit2_28mm": ROOT / "runs/codex_26d750_source_range_builder/source_range_unit2_28mm.json",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def instruction(decoder, data, address):
    return next(decoder.disasm(data[address : address + 16], address))


def verify_static():
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"installed libcp digest {digest}")
    windows = {
        (0x26D750, 0x26DA68): "3ca365c387b9971773d5f4c9b3855de74af3c57c920b7414bdf6dfa5517b421c",
        (0x298FF0, 0x299255): "e9feb38f963436c0feecd791b460e5c6101ad2a121f6ae186770e79e04c1109f",
        (0x2993F0, 0x2996AE): "5b34148cf6c3079ddf14b1140fef1f4f24f845450744a8257ff1b5235d0ac5b3",
        (0x2997B0, 0x299C63): "80ad3d0f9c4a347cc7b0995bb7af2933c40588e9014338c6d893c98457f2d406",
    }
    for (begin, end), expected in windows.items():
        observed = hashlib.sha256(data[begin:end]).hexdigest()
        require(observed == expected, f"window 0x{begin:x}..0x{end:x}: {observed}")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    expected_instructions = {
        0x26D887: ("mov", "ecx, dword ptr [r13 + 0x14]"),
        0x26D8A7: ("call", "0x298ff0"),
        0x299022: ("mov", "dword ptr [rbp - 0xa4], ecx"),
        0x299028: ("mov", "eax, ecx"),
        0x29902A: ("shr", "eax, 0x1f"),
        0x29902D: ("add", "eax, ecx"),
        0x29902F: ("and", "ecx, 1"),
        0x299032: ("sar", "eax, 1"),
        0x299034: ("lea", "eax, [rcx + rax - 1]"),
        0x2990FE: ("mov", "qword ptr [rax + 0x18], r15"),
        0x299102: ("mov", "qword ptr [rax + 0x20], r12"),
        0x2994AC: ("mov", "cx, 0xffff"),
        0x2994B0: ("xor", "esi, esi"),
        0x2994C0: ("cmp", "byte ptr [r15 + rdx + 1], 0"),
        0x2994C6: ("je", "0x2994f3"),
        0x2994DD: ("movzx", "edi, word ptr [rdi + rbx*2]"),
        0x2994E6: ("cmovb", "cx, di"),
        0x2994EF: ("cmova", "si, di"),
        0x2995F0: ("lea", "r14d, [rbx + r11 + 1]"),
        0x2995FD: ("cmovs", "r14d, ecx"),
        0x299604: ("cmovg", "r14d, r8d"),
        0x29960F: ("cmp", "byte ptr [r10 + rdi], 0"),
        0x299614: ("je", "0x29963e"),
        0x2998DC: ("mov", "r11w, 0xffff"),
        0x299A70: ("movzx", "ebx, word ptr [rax]"),
        0x299A73: ("movzx", "edx, word ptr [rcx]"),
        0x299A7D: ("cmovb", "r11w, bx"),
        0x299A89: ("cmova", "r9w, dx"),
        0x299BF0: ("mov", "rcx, qword ptr [rbp - 0x30]"),
        0x299BFC: ("mov", "ecx, r11d"),
        0x299C04: ("cmovs", "ecx, edi"),
        0x299C09: ("cmovg", "ecx, ebx"),
    }
    for address, expected in expected_instructions.items():
        insn = instruction(decoder, data, address)
        observed = (insn.mnemonic, insn.op_str)
        require(observed == expected, f"0x{address:x}: {observed} != {expected}")
    return digest


def verify_runtime():
    report = json.loads(REPORT.read_text(encoding="ascii"))
    require(not report["errors"], report["errors"])
    require(report["terminated_after_capture"], "runtime capture incomplete")
    packets = sorted(report["packets"], key=lambda packet: packet["target_dimensions"][0])
    require(
        [packet["target_dimensions"] for packet in packets]
        == [[130, 98], [260, 195], [520, 390], [1040, 780], [2080, 1560]],
        "target dimensions",
    )
    require(all(packet["kernel_size_0x14"] == 4 for packet in packets), "kernel size")
    require(all(packet["padding_0x10"] == 1 for packet in packets), "range padding")
    mixed = 0
    for packet in packets:
        require(packet["source"]["width"] * 2 == packet["target_dimensions"][0], "2x width")
        for sample in packet["samples"]:
            require(len(sample["coordinates"]) == 16, "4x4 coordinates")
            require(len(sample["mask_values"]) == 16, "4x4 mask")
            require(sample["observed_low"] == sample["expected_low"], f"low {sample}")
            require(sample["observed_high"] == sample["expected_high"], f"high {sample}")
            if sample["kind"] == "mixed_mask":
                mixed += 1
                require(0 < len(sample["included_values"]) < 16, "mixed mask sample")
    require(mixed >= 1, "no mixed-mask replay")
    prior_digests = {}
    for name, path in PRIOR_REPORTS.items():
        prior = json.loads(path.read_text(encoding="ascii"))
        require(not prior["errors"], f"{name}: prior errors")
        entry = next(
            sample for sample in prior["samples"] if sample["site"] == "builder_26d750_entry"
        )
        require(entry["target_fields"]["field_0x14"] == 4, f"{name}: kernel")
        require(
            any(sample["site"] == "builder_after_298ff0" for sample in prior["samples"]),
            f"{name}: no post-pool packet",
        )
        prior_digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256(REPORT.read_bytes()).hexdigest(), prior_digests


def main():
    digest = verify_static()
    report_digest, prior_digests = verify_runtime()
    print(f"index5_range_pool_static=OK libcp={digest}")
    print("kernel_size=4 offsets=-1,0,1,2 x -1,0,1,2 boundary=clamp")
    print("mask_nonzero=include mask_zero=exclude all_invalid=(65535,0)")
    print(f"five_transition_replay=OK report_sha256={report_digest}")
    for name, prior_digest in prior_digests.items():
        print(f"{name}_kernel=4 report_sha256={prior_digest}")


if __name__ == "__main__":
    main()
