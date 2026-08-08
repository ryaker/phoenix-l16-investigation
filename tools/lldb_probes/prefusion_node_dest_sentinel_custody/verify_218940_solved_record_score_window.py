#!/usr/bin/env python3
"""Verify solved-record admission into the 0x218940 local score window.

This joins the admitted record-z watch packet to a SHA-pinned static decode.
It does not require branch stepping: the runtime packet proves finite positive
z reaches the compare at 0x2189c4, and the static window proves that only
nonpositive/unordered z takes the 0x2189c8 -> 0x218aeb skip.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs" / "prefusion_20ca00_record_z_watch"
STEM = "record_z_watch_unit1_70mm"

WINDOW_BEGIN = 0x218940
WINDOW_END = 0x218B2F
WINDOW_SHA256 = "3b2eb5366eee74ae3ba8615437b6725658e465710d865fae0eecc6388a21eded"

Z_COMPARE = 0x2189C4
BODY_ENTRY = 0x2189CE
SKIP_TARGET = 0x218AEB

ANCHORS = {
    0x218940: ("push", "rbp"),
    0x218945: ("mov", "rdi, qword ptr [rdi + 0x18]"),
    0x218964: ("mov", "rbx, qword ptr [rdx]"),
    0x2189A0: ("movss", "xmm4, dword ptr [rbx + rdx*8]"),
    0x2189A5: ("ucomiss", "xmm11, xmm4"),
    0x2189A9: ("jae", "0x218aeb"),
    0x2189AF: ("movss", "xmm12, dword ptr [rbx + rdx*8 + 4]"),
    0x2189B6: ("ucomiss", "xmm12, xmm11"),
    0x2189BA: ("jbe", "0x218aeb"),
    0x2189C0: ("movss", "xmm6, dword ptr [rax]"),
    0x2189C4: ("ucomiss", "xmm11, xmm6"),
    0x2189C8: ("jae", "0x218aeb"),
    0x2189CE: ("movss", "xmm1, dword ptr [rax - 8]"),
    0x2189D3: ("movss", "xmm3, dword ptr [rax - 4]"),
    0x2189D8: ("movss", "xmm2, dword ptr [rsi + 0x30]"),
    0x2189F3: ("mulss", "xmm7, xmm6"),
    0x218A35: ("addss", "xmm7, dword ptr [rsi + 0x24]"),
    0x218AA4: ("divss", "xmm1, xmm6"),
    0x218ACC: ("ucomiss", "xmm0, xmm9"),
    0x218ADC: ("addss", "xmm10, xmm1"),
    0x218AE5: ("add", "r9d, edi"),
    0x218AE8: ("inc", "r8d"),
    0x218AEB: ("inc", "rdx"),
    0x218B1A: ("cvtsi2ss", "xmm1, r9d"),
    0x218B23: ("movss", "dword ptr [rcx], xmm1"),
    0x218B27: ("mulss", "xmm0, xmm10"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_static_window(libcp: Path = DEFAULT_LIBCP) -> None:
    blob = libcp.read_bytes()
    window = blob[WINDOW_BEGIN:WINDOW_END]
    require(len(window) == WINDOW_END - WINDOW_BEGIN, "short 0x218940 window")
    require(hashlib.sha256(window).hexdigest() == WINDOW_SHA256, "0x218940 window SHA-256 drift")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in disassembler.disasm(window, WINDOW_BEGIN)
    }
    for address, expected in ANCHORS.items():
        require(instructions.get(address) == expected, f"anchor drift at 0x{address:x}: {instructions.get(address)}")

    body_sites = {
        0x2189CE: "record_x_load",
        0x2189D3: "record_y_load",
        0x2189D8: "transform_field_load",
        0x2189F3: "record_z_transform_multiply",
        0x218ADC: "score_sum_xmm10",
        0x218AE5: "over_threshold_count_r9d",
        0x218AE8: "positive_record_count_r8d",
    }
    require(all(Z_COMPARE < address < SKIP_TARGET for address in body_sites), "body site escaped z-skip interval")


def verify_runtime() -> dict:
    report_path = RUN_DIR / f"{STEM}.json"
    log_path = RUN_DIR / f"{STEM}.log"
    hdr_path = RUN_DIR / f"{STEM}.hdr"

    report = json.loads(report_path.read_text())
    log = log_path.read_text(errors="replace")
    require("Process " in log and "launched" in log, "process launch missing")
    require("Written:" in log and "(10432x7824)" in log, "HDR write marker missing")
    require("Traceback" not in log, "callback traceback present")
    require("error:" not in log.lower(), "LLDB error present")
    require("lost connection" not in log.lower(), "debugserver connection lost")
    with hdr_path.open("rb") as handle:
        require(handle.read(10) == b"#?RADIANCE", "HDR output magic mismatch")

    require(report.get("process_exit_status") == 0, "report process exit not zero")
    require(report.get("drive_hit_step_cap") is False, "drive hit step cap")
    require(report.get("errors") == [], f"probe errors: {report.get('errors')}")

    counts = report.get("counts") or {}
    armed = report.get("armed") or {}
    require(armed.get("gate_index") == 3906, "armed gate index drift")
    require(armed.get("record_offset") == 19530, "armed record offset drift")
    require(counts.get("watchpoints_armed") == 1, "expected one watchpoint")
    require(counts.get("watchpoint_hits") == 64, "expected capped 64 watchpoint hits")
    require(counts.get("value_changes") == 0, "watched z changed")
    require(counts.get("value_unchanged") == 64, "unchanged count mismatch")

    samples = report.get("samples") or []
    z_samples = [sample for sample in samples if sample.get("libcp_va") == Z_COMPARE]
    require(len(z_samples) == 37, f"expected 37 z-compare samples, got {len(z_samples)}")
    z_at_arm = armed.get("z_at_arm") or {}
    z_value = z_at_arm.get("value")
    require(isinstance(z_value, (float, int)), "armed z missing")
    require(z_value > 0.0, "record z is not positive")
    require(z_at_arm.get("hex") == "deb55a45", "armed z hex drift")

    for sample in z_samples:
        require(sample.get("registers", {}).get("rax") == armed.get("z_addr"), "z-compare rax is not watched z address")
        require(sample.get("registers", {}).get("rdx") == armed.get("gate_index"), "z-compare rdx is not selected gate index")
        z_now = sample.get("z_now") or {}
        require(z_now.get("hex") == z_at_arm.get("hex"), "z-compare sample changed z hex")
        require(z_now.get("value") == z_value, "z-compare sample changed z value")
        require((sample.get("stack") or [{}])[0].get("libcp_va") == Z_COMPARE, "z-compare stack top drift")

    return {
        "report": report_path,
        "z": z_value,
        "watchpoint_hits": counts.get("watchpoint_hits"),
        "z_compare_hits": len(z_samples),
    }


def main() -> None:
    verify_static_window()
    summary = verify_runtime()
    print(f"binary={DEFAULT_LIBCP}")
    print(f"window=0x{WINDOW_BEGIN:x}..0x{WINDOW_END:x} sha256={WINDOW_SHA256}")
    print(f"report={summary['report']}")
    print(
        "record_z_gate="
        f"z={summary['z']:.9f} z_compare_hits={summary['z_compare_hits']} "
        "static_positive_fallthrough=0x2189c8_not_taken_to_0x2189ce"
    )
    print(
        "static_body=record_xyz plus rsi+0x24..0x50 transform fields feed score_sum_xmm10,"
        "over_threshold_count_r9d,positive_record_count_r8d"
    )
    print("scope=one capped Unit-1 70mm solved-record runtime packet plus static fallthrough proof; no terminality or image effect proven")


if __name__ == "__main__":
    main()
