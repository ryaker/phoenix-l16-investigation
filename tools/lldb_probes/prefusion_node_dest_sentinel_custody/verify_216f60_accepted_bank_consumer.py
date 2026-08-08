#!/usr/bin/env python3
"""Verify accepted 0x216f60 selector-1 banks reach later 0x264270 reads."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs" / "prefusion_216f60_accepted_bank_consumer"
RUNS = (
    ("28mm", "28mm"),
    ("35mm", "35mm"),
    ("70mm", "70mm"),
    ("150mm", "150mm"),
    ("unit2_35mm", "Unit-2 35mm"),
)

LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
F33D0_BEGIN = 0xF33D0
F33D0_END = 0xF349D
F33D0_SHA256 = "ce947e1ecadeca1e37461eee9394c61e948ae7a86a84b71c6e39e557ae1656a8"
COPY_BEGIN = 0x264270
COPY_END = 0x264370
COPY_SHA256 = "4a70e92075516bbfa5f0e05b10449fe15a39a0d661baf885bbf9b317dc26cc0e"

F33D0_ANCHORS = {
    0xF33D9: ("cmp", "r8d, 1"),
    0xF33DD: ("je", "0xf3440"),
    0xF3440: ("mov", "eax, dword ptr [rsi + 0x20]"),
    0xF3443: ("mov", "dword ptr [rdi + 0x14c], eax"),
    0xF3449: ("movups", "xmm0, xmmword ptr [rsi]"),
    0xF3450: ("movups", "xmmword ptr [rdi + 0x13c], xmm1"),
    0xF3457: ("movups", "xmmword ptr [rdi + 0x12c], xmm0"),
    0xF345E: ("mov", "eax, dword ptr [rdx + 0x20]"),
    0xF346E: ("movups", "xmmword ptr [rdi + 0x160], xmm1"),
    0xF3475: ("movups", "xmmword ptr [rdi + 0x150], xmm0"),
    0xF347C: ("mov", "eax, dword ptr [rcx]"),
    0xF3490: ("mov", "dword ptr [rdi + 0x17c], eax"),
}
COPY_ANCHORS = {
    0x26428E: ("call", "0xf34e0"),
    0x264299: ("movups", "xmm0, xmmword ptr [rax]"),
    0x26429C: ("movups", "xmm1, xmmword ptr [rax + 0x10]"),
    0x2642A0: ("movups", "xmmword ptr [rbx + 0x10], xmm1"),
    0x2642A4: ("movups", "xmmword ptr [rbx], xmm0"),
    0x2642AD: ("call", "0xf34e0"),
    0x2642CA: ("call", "0xf34e0"),
    0x264306: ("call", "0xf3360"),
    0x26433E: ("call", "0xf3350"),
    0x26434D: ("movss", "xmm2, dword ptr [r12 + 0x68]"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def decode(blob: bytes, begin: int, end: int) -> dict[int, tuple[str, str]]:
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    return {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in disassembler.disasm(blob[begin:end], begin)
    }


def verify_static() -> None:
    blob = LIBCP.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    require(
        hashlib.sha256(blob[F33D0_BEGIN:F33D0_END]).hexdigest() == F33D0_SHA256,
        "f33d0 SHA drift",
    )
    require(
        hashlib.sha256(blob[COPY_BEGIN:COPY_END]).hexdigest() == COPY_SHA256,
        "0x264270 SHA drift",
    )
    for address, expected in F33D0_ANCHORS.items():
        require(
            decode(blob, F33D0_BEGIN, F33D0_END).get(address) == expected,
            f"f33d0 anchor drift at 0x{address:x}",
        )
    for address, expected in COPY_ANCHORS.items():
        require(
            decode(blob, COPY_BEGIN, COPY_END).get(address) == expected,
            f"0x264270 anchor drift at 0x{address:x}",
        )


def verify_runtime() -> dict:
    summaries = {}
    for stem, label in RUNS:
        report_path = RUN_DIR / f"accepted_bank_consumer_{stem}.json"
        output_path = RUN_DIR / f"accepted_bank_consumer_{stem}.hdr"
        report = json.loads(report_path.read_text())
        counts = report["counts"]
        require(report["process_exit_status"] == 0, f"{label}: process exit")
        require(report["drive_hit_step_cap"] is False, f"{label}: step cap")
        require(report["errors"] == [], f"{label}: errors")
        require(report["pending_f33d0"] == [], f"{label}: pending f33d0")
        require(report["pending_f34e0"] == [], f"{label}: pending f34e0")
        require(output_path.stat().st_size > 0, f"{label}: empty HDR")
        require(counts["f33d0_call_hits"] > 0, f"{label}: no accepted f33d0 calls")
        require(
            counts["f33d0_call_hits"] == counts["f33d0_return_hits"],
            f"{label}: f33d0 call/return mismatch",
        )
        require(
            all(packet["selector"] == 1 for packet in report["f33d0_calls"]),
            f"{label}: non-selector-1 accepted call",
        )
        require(
            all(packet["exact_copy_match"] for packet in report["f33d0_returns"]),
            f"{label}: selector-1 exact copy mismatch",
        )
        require(counts["watchpoints_armed"] == 1, f"{label}: watch arm count")
        require(counts["watchpoint_hits"] == len(report["watch_samples"]), f"{label}: watch count")
        require(counts["watchpoint_hits"] > 0, f"{label}: no downstream watch hits")
        require(counts["f34e0_call_hits"] == 0, f"{label}: unexpected 0x3f7ec0 f34e0 hit")
        require(
            counts["materialize_call_hits"] == 0,
            f"{label}: unexpected 0x3f7ec0 materialize hit",
        )

        samples = report["watch_samples"]
        first_overwrite = next(
            (index for index, sample in enumerate(samples) if sample["libcp_va"] == 0xF345E),
            len(samples),
        )
        pre_overwrite = samples[:first_overwrite]
        require(pre_overwrite, f"{label}: no pre-overwrite samples")
        require(
            all(not sample["changed"] for sample in pre_overwrite),
            f"{label}: accepted bank changed before State overwrite",
        )
        vas = Counter(sample["libcp_va"] for sample in pre_overwrite)
        require(vas[0x26429C] > 0, f"{label}: no direct f34e0-bank read")
        require(vas[0x26434D] > 0, f"{label}: no f3350-side bank read")
        require(
            any(
                any(frame.get("libcp_va") == 0x23A03B for frame in sample["stack"])
                for sample in pre_overwrite
            ),
            f"{label}: no 0x239e00 propagation ancestry",
        )
        summaries[stem] = {
            "label": label,
            "accepted_calls": counts["f33d0_call_hits"],
            "watch_hits": counts["watchpoint_hits"],
            "pre_overwrite": len(pre_overwrite),
            "direct_reads": vas[0x26429C],
            "accessor_reads": vas[0x26434D],
            "changes": counts["watch_value_changes"],
            "stereo_sites": counts["f34e0_call_hits"] + counts["materialize_call_hits"],
        }
    return summaries


def main() -> None:
    verify_static()
    summaries = verify_runtime()
    print(
        f"static_accepted_bank_consumer=OK libcp_sha256={LIBCP_SHA256} "
        f"f33d0_sha256={F33D0_SHA256} copy_sha256={COPY_SHA256}"
    )
    for stem, _label in RUNS:
        summary = summaries[stem]
        print(
            f"{summary['label']}: accepted_calls={summary['accepted_calls']} "
            f"watch_hits={summary['watch_hits']} pre_overwrite={summary['pre_overwrite']} "
            f"direct_reads={summary['direct_reads']} accessor_reads={summary['accessor_reads']} "
            f"value_changes={summary['changes']} stereo_sites={summary['stereo_sites']}"
        )


if __name__ == "__main__":
    main()
