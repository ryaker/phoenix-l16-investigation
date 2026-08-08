#!/usr/bin/env python3
"""Verify G-42 sum normalization and direct custody into G-43 SGM."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
REPORTS = {
    "unit1_28mm": ROOT / "runs/index5_sgm_cost_input/unit1_28/report.json",
    "unit2_28mm": ROOT / "runs/index5_sgm_cost_input/unit2_28/report.json",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def instruction(decoder, data, address):
    return next(decoder.disasm(data[address : address + 16], address))


def verify_static():
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"installed libcp digest {digest}")
    windows = {
        (0x276B37, 0x276CB2): "4af213e7f19aa79bdc0bed66a7c9f0b8b2a29c897355cb57041a4521521812bd",
        (0x2773BD, 0x277483): "0f88ea921d81ff602800e684c9804eddea085a50607bfde6504e91b056194c7e",
        (0x2779B0, 0x277A1F): "fda023595c1323c7af0f1f56c85d97922e30cbc193311079905e6d39de0a4b43",
    }
    for (begin, end), expected in windows.items():
        observed = hashlib.sha256(data[begin:end]).hexdigest()
        require(observed == expected, f"window 0x{begin:x}..0x{end:x}: {observed}")

    constant = data[0x5DAE28 : 0x5DAE2C]
    require(constant.hex() == "26b4173d", f"constant bytes {constant.hex()}")
    one_over_27 = struct.unpack("<f", constant)[0]
    require(one_over_27 == f32(1.0 / 27.0), f"constant value {one_over_27}")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    expected_instructions = {
        0x276BD9: ("mov", "rax, qword ptr [rbp - 0x130]"),
        0x276BE0: ("sub", "rax, qword ptr [rbp - 0x138]"),
        0x276BE7: ("sar", "rax, 4"),
        0x276BEB: ("movabs", "rcx, 0xcccccccccccccccd"),
        0x276BF5: ("imul", "rax, rcx"),
        0x276C0C: ("cvtsi2ss", "xmm0, rax"),
        0x276C9E: ("movss", "xmm1, dword ptr [rip + 0x364182]"),
        0x276CA6: ("divss", "xmm1, xmm0"),
        0x276CAA: ("movss", "dword ptr [rbp - 0x2e4], xmm1"),
        0x2773DC: ("call", "0x2732f0"),
        0x277420: ("movss", "xmm1, dword ptr [rbp - 0x2e4]"),
        0x277450: ("movzx", "esi, word ptr [rdi + rbx*2]"),
        0x277457: ("cvtsi2ss", "xmm0, esi"),
        0x27745B: ("mulss", "xmm0, xmm1"),
        0x27745F: ("cvttss2si", "esi, xmm0"),
        0x277463: ("mov", "word ptr [rdi + rbx*2], si"),
        0x277467: ("mov", "byte ptr [rdx + rbx], sil"),
        0x2779EE: ("movdqu", "xmm0, xmmword ptr [r10 + rdx*2]"),
        0x2779F4: ("paddusw", "xmm0, xmm6"),
        0x2779F8: ("psubusw", "xmm0, xmm2"),
    }
    for address, expected in expected_instructions.items():
        insn = instruction(decoder, data, address)
        observed = (insn.mnemonic, insn.op_str)
        require(observed == expected, f"0x{address:x}: {observed} != {expected}")
    return digest, one_over_27


def verify_report(label, path, one_over_27):
    report = json.loads(path.read_text(encoding="ascii"))
    require(not report["errors"], f"{label}: {report['errors']}")
    require(report["capture_complete"], f"{label}: incomplete")
    events = {event["site"]: event for event in report["events"]}
    raw = events["after_g42"]
    normalized = events["after_normalize"]
    recurrence = events["sgm_recurrence"]
    require(raw["projection_count"] == 4, f"{label}: source count")
    expected_factor = f32(one_over_27 / f32(raw["projection_count"]))
    require(raw["factor"] == expected_factor, f"{label}: factor")
    expected = [f32(value * raw["factor"]) for value in raw["cost_u16"]]
    expected = [int(value) for value in expected]
    require(normalized["cost_u16"] == expected, f"{label}: normalized vector")
    require(recurrence["r10_is_temp"], f"{label}: temporary custody")
    begin = recurrence["rdx"]
    require(
        recurrence["local_cost_lanes"] == normalized["cost_u16"][begin : begin + 8],
        f"{label}: recurrence lanes",
    )
    return raw, normalized, recurrence, hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    digest, one_over_27 = verify_static()
    print(f"index5_sgm_cost_input_static=OK libcp={digest}")
    print(f"installed_constant={one_over_27:.17g} bytes=26b4173d")
    for label, path in REPORTS.items():
        raw, normalized, recurrence, report_digest = verify_report(
            label, path, one_over_27
        )
        print(
            f"{label}=OK sources={raw['projection_count']} factor={raw['factor']:.17g} "
            f"raw0={raw['cost_u16'][0]} normalized0={normalized['cost_u16'][0]} "
            f"sgm_lane0={recurrence['local_cost_lanes'][0]} report_sha256={report_digest}"
        )
    print("pedestal=ABSENT local_cost=trunc_f32(G42_sum*((1/27)/source_count))")


if __name__ == "__main__":
    main()
