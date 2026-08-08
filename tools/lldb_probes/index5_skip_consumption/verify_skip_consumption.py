#!/usr/bin/env python3
"""Verify how selected pattern-2 Skip-mask pixels receive final depth."""

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
REPORTS = {
    "unit1_28mm": (
        ROOT / "runs/index5_skip_consumption/unit1_28_thread_gated_v2/report.json",
        ROOT / "runs/index5_skip_consumption/unit1_28_final_v2/final_report.json",
    ),
    "unit2_28mm": (
        ROOT / "runs/index5_skip_consumption/unit2_28_thread_gated/report.json",
        ROOT / "runs/index5_skip_consumption/unit2_28_final/final_report.json",
    ),
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
        (0x27750C, 0x2775A6): "3d4bd304cc6526bfa9b5c7036974cdcefd28b14405f95170c39b4c7d01d6e4a7",
        (0x2777F3, 0x277A41): "780018cbb960fe74c4c3d01673fa94042c177e6fcd8c581c396e5aaa3c39081e",
        (0x299C70, 0x29A7CB): "b5615cf84fd91245518c478bcb9b56ecef0f7647dcb4d4a144217119e717fa01",
    }
    for (begin, end), expected in windows.items():
        observed = hashlib.sha256(data[begin:end]).hexdigest()
        require(observed == expected, f"window 0x{begin:x}..0x{end:x}: {observed}")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    expected_instructions = {
        0x27750C: ("mov", "eax, dword ptr [r14 + 0x220]"),
        0x27751B: ("mov", "rsi, qword ptr [r14 + 0x228]"),
        0x277522: ("cmp", "byte ptr [rsi + rax], 0"),
        0x277535: ("je", "0x276f20"),
        0x277551: ("mov", "qword ptr [rbp - 0x1b8], r8"),
        0x277558: ("lea", "rsi, [r12 + r12]"),
        0x27755F: ("mov", "rdi, r15"),
        0x277562: ("call", "0x555eb2"),
        0x2779EE: ("movdqu", "xmm0, xmmword ptr [r10 + rdx*2]"),
        0x2779F4: ("paddusw", "xmm0, xmm6"),
        0x2779F8: ("psubusw", "xmm0, xmm2"),
        0x277A0C: ("paddusw", "xmm5, xmm0"),
        0x29A6F5: ("movzx", "r8d, word ptr [rdx + rax + 2]"),
        0x29A730: ("movzx", "r9d, word ptr [r10 + rdx*2]"),
        0x29A73B: ("cmovb", "cx, r9w"),
        0x29A740: ("cmovb", "esi, edx"),
        0x29A7B9: ("movzx", "eax, word ptr [r15 + 4]"),
        0x29A7BE: ("imul", "eax, esi"),
        0x29A7C1: ("movzx", "ecx, word ptr [r15]"),
        0x29A7C5: ("add", "ecx, eax"),
    }
    for address, expected in expected_instructions.items():
        insn = instruction(decoder, data, address)
        observed = (insn.mnemonic, insn.op_str)
        require(observed == expected, f"0x{address:x}: {observed} != {expected}")
    return digest


def verify_branch(label, path):
    report = json.loads(path.read_text(encoding="ascii"))
    require(not report["errors"], f"{label}: branch errors")
    require(report["capture_complete"], f"{label}: branch incomplete")
    computed = report["pixels"]["computed"]
    skipped = report["pixels"]["skipped"]
    require(computed["mask"] == 0, f"{label}: computed mask")
    require(skipped["mask"] != 0, f"{label}: skipped mask")
    require(any(computed["local_ready"]), f"{label}: computed unary is zero")
    require(not any(skipped["local_ready"]), f"{label}: skipped unary is nonzero")
    return computed, skipped, hashlib.sha256(path.read_bytes()).hexdigest()


def verify_final(label, path):
    report = json.loads(path.read_text(encoding="ascii"))
    require(not report["errors"], f"{label}: final errors")
    require(report["capture_complete"], f"{label}: final incomplete")
    computed = report["pixels"]["computed"]
    skipped = report["pixels"]["skipped"]
    require(computed["mask"] == 0, f"{label}: final computed mask")
    require(skipped["mask"] != 0, f"{label}: final skipped mask")
    for polarity, pixel in report["pixels"].items():
        record = pixel["record"]
        require(record["count"] > 0, f"{label}:{polarity}: empty record")
        require(record["step"] == 1, f"{label}:{polarity}: step")
        costs = record["costs"]
        lane = min(range(len(costs)), key=costs.__getitem__)
        require(record["selected_lane"] == lane, f"{label}:{polarity}: argmin")
        require(
            record["selected_absolute_index"] == record["base"] + lane,
            f"{label}:{polarity}: absolute index",
        )
    require(any(skipped["record"]["costs"]), f"{label}: skipped final costs zero")
    return computed, skipped, hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    digest = verify_static()
    print(f"index5_skip_consumption_static=OK libcp={digest}")
    for label, (branch_path, final_path) in REPORTS.items():
        branch_computed, branch_skipped, branch_digest = verify_branch(
            label, branch_path
        )
        final_computed, final_skipped, final_digest = verify_final(label, final_path)
        print(
            f"{label}=OK branch_xy=({branch_computed['x']},{branch_computed['y']})/"
            f"({branch_skipped['x']},{branch_skipped['y']}) "
            f"local0={branch_computed['local_ready'][0]}/{branch_skipped['local_ready'][0]} "
            f"selected={final_computed['record']['selected_absolute_index']}/"
            f"{final_skipped['record']['selected_absolute_index']} "
            f"reports={branch_digest},{final_digest}"
        )
    print("mask0=compute_G42 mask_nonzero=zero_unary both=SGM_then_cost_volume_first_argmin")


if __name__ == "__main__":
    main()
