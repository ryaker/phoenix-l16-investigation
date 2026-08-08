#!/usr/bin/env python3
"""Verify index-5 per-level coordinate lifting and projection-record policy."""

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
RUN_ROOT = ROOT / "runs/index5_perlevel_projection_scale"
REPORTS = {
    "unit1_28mm": RUN_ROOT / "unit1_28mm/report.json",
    "unit1_35mm": RUN_ROOT / "unit1_35mm/report.json",
    "unit1_70mm": RUN_ROOT / "unit1_70mm/report.json",
    "unit1_150mm": RUN_ROOT / "unit1_150mm/report.json",
    "unit2_28mm": RUN_ROOT / "unit2_28mm/report.json",
    "unit2_35mm": RUN_ROOT / "unit2_35mm/report.json",
    "unit2_70mm": RUN_ROOT / "unit2_70mm/report.json",
    "unit2_150mm": RUN_ROOT / "unit2_150mm_retry/report.json",
}

EXPECTED_DIMS = [
    [65, 49],
    [130, 98],
    [260, 195],
    [520, 390],
    [1040, 780],
    [2080, 1560],
]
EXPECTED_STEPS = [32, 16, 8, 4, 2, 1]


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
        (0x25E4B0, 0x25E4FA): "ad316edfe91f6b6a2966c2603cf354482da4520ecf6e31968f333ef810add354",
        (0x276E23, 0x276E82): "689590d6536512dea16210d39df56e9da8483ae5a79fdd7c87788f4e247adb95",
        (0x276F56, 0x276FC7): "4d2436ec8b879453d29fefe32f401671d66cb29cd53c8514b024bfaff4e16a35",
    }
    for (begin, end), expected in windows.items():
        observed = hashlib.sha256(data[begin:end]).hexdigest()
        require(observed == expected, f"window 0x{begin:x}..0x{end:x}: {observed}")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    expected_instructions = {
        0x25E4E6: ("movabs", "rax, 0x3f8000003f800000"),
        0x25E4F0: ("mov", "qword ptr [rdi + 0x48], rax"),
        0x276E23: ("mov", "r12d, dword ptr [rcx + 0x1c]"),
        0x276E62: ("imul", "ecx, esi"),
        0x276E65: ("mov", "edx, r12d"),
        0x276E68: ("shr", "edx, 0x1f"),
        0x276E6B: ("add", "edx, r12d"),
        0x276E6E: ("sar", "edx, 1"),
        0x276E70: ("add", "edx, ecx"),
        0x276E75: ("mov", "eax, dword ptr [rax + 0x14]"),
        0x276E78: ("dec", "eax"),
        0x276E7A: ("cmp", "edx, eax"),
        0x276E7C: ("cmovle", "eax, edx"),
        0x276F56: ("mov", "ebx, dword ptr [r14 + 0x1c]"),
        0x276F90: ("imul", "ecx, edx"),
        0x276F93: ("mov", "edx, ebx"),
        0x276F95: ("shr", "edx, 0x1f"),
        0x276F98: ("add", "edx, ebx"),
        0x276F9A: ("sar", "edx, 1"),
        0x276F9C: ("add", "edx, ecx"),
        0x276FA1: ("mov", "eax, dword ptr [rax + 0x10]"),
        0x276FA4: ("dec", "eax"),
        0x276FA6: ("cmp", "edx, eax"),
        0x276FA8: ("cmovle", "eax, edx"),
    }
    for address, expected in expected_instructions.items():
        insn = instruction(decoder, data, address)
        observed = (insn.mnemonic, insn.op_str)
        require(observed == expected, f"0x{address:x}: {observed} != {expected}")
    return digest


def verify_report(name, path):
    report = json.loads(path.read_text(encoding="ascii"))
    require(not report["errors"], f"{name}: {report['errors']}")
    require(report["terminated_after_capture"], f"{name}: incomplete capture")
    packets = sorted(report["packets"], key=lambda packet: packet["index"])
    require([packet["index"] for packet in packets] == list(range(6)), f"{name}: indices")
    require([packet["guidance"]["size"] for packet in packets] == EXPECTED_DIMS, f"{name}: dims")
    require(
        [packet["image_coordinate_step_0x1c"] for packet in packets] == EXPECTED_STEPS,
        f"{name}: steps",
    )

    reference_records = [item["raw_hex"] for item in packets[0]["projection_records"]]
    for packet in packets:
        require(packet["layer_dimensions_0x2b8"] == packet["guidance"]["size"], f"{name}: layer dims")
        require(len(packet["images"]) == 5, f"{name}: Images count")
        require(
            all(image["descriptor"]["size"] == [2080, 1560] for image in packet["images"]),
            f"{name}: Images dimensions",
        )
        require(len(packet["projection_records"]) == 4, f"{name}: projection count")
        require(
            all(record["scale"] == [1.0, 1.0] for record in packet["projection_records"]),
            f"{name}: projection scales",
        )
        require(
            [item["raw_hex"] for item in packet["projection_records"]] == reference_records,
            f"{name}: per-level projection drift",
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    digest = verify_static()
    report_digests = {name: verify_report(name, path) for name, path in REPORTS.items()}
    print(f"index5_perlevel_projection_static=OK libcp={digest}")
    print("levels=65x49,130x98,260x195,520x390,1040x780,2080x1560")
    print("image_coordinate_step=32,16,8,4,2,1")
    print("full=min(step*level_coord+trunc(step/2),image_extent-1)")
    print("Images=5x2080x1560 projection_scales=4x(1,1) records=invariant_across_levels")
    for name, report_digest in report_digests.items():
        print(f"{name}=OK report_sha256={report_digest}")


if __name__ == "__main__":
    main()
