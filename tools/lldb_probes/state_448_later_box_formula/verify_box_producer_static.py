#!/usr/bin/env python3
"""Static verifier for the 0x145980 box producer used by state+0x448.

This guards the evidence doc against hand-read disassembly drift. It checks the
installed libcp call/data anchors that make the later payload box a computed
distortion/undistortion envelope, and reuses the Lane B LRI verifier for the
public 4160x3120 sensor-ROI fact.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
AUDIT_PATH = ROOT / "tools/lane_b_index5_public_meaning_audit.py"


WINDOWS = {
    "f3330_f3350_accessors": [
        "disassemble --start-address 0xf3330 --end-address 0xf3360",
        [
            "movq   0xa0(%rdi), %rax",
            "leaq   0x10c(%rdi), %rax",
        ],
    ],
    "box_producer_145980": [
        "disassemble --start-address 0x145980 --end-address 0x146330",
        [
            "callq  0xf3350",
            "callq  0x145590",
            "callq  0xf3360",
            "callq  0xf3330",
            "callq  0xf2720",
            "callq  0xe7730",
            "callq  0x146380",
            "movl   %eax, (%r14)",
            "movl   %ecx, 0x4(%r14)",
            "movl   %edx, 0x8(%r14)",
            "movl   %esi, 0xc(%r14)",
            "Distortion and undistortion vectors are not the same size",
            "Cannot read data from empty Optional!",
        ],
    ],
    "sample_vector_145590": [
        "disassemble --start-address 0x145590 --end-address 0x145980",
        [
            "callq  0xf3330",
            "callq  0xf3360",
            "callq  0xe730",
            "callq  0xf3350",
            "callq  0xf2720",
            "callq  0xe7730",
            "callq  0xe810",
            "cmpq   $0x1e, %r15",
            "movss  %xmm0, (%r12,%r15,4)",
            "movss  %xmm0, (%r14,%r15,4)",
            "Missing CaptureStack",
            "Cannot read data from empty Optional!",
        ],
    ],
    "vector_pack_146380": [
        "disassemble --start-address 0x146380 --end-address 0x146520",
        [
            "callq  0x556032",
            "movl   (%rcx), %edx",
            "movl   %edx, 0x30(%r15)",
            "movss  -0x4(%rax), %xmm0",
            "movss  %xmm0, 0x34(%r15)",
            "movss  %xmm0, 0x38(%r15)",
        ],
    ],
    "reference_scale_e7730": [
        "disassemble --start-address 0xe7730 --end-address 0xe78c0",
        [
            "callq  0xf2720",
            "Reference camera image not found!",
            "callq  0xf3350",
            "movss  0x18(%rax), %xmm1",
            "callq  0xe7420",
            "Unexpected sensor type!",
            "cvtsd2ss %xmm0, %xmm0",
        ],
    ],
    "radial_interp_e810": [
        "disassemble --start-address 0xe810 --end-address 0xe900",
        [
            "movss  0x98(%rsi), %xmm8",
            "movss  0x9c(%rsi), %xmm9",
            "subsd  0x80(%rsi), %xmm5",
            "divsd  0x90(%rsi), %xmm5",
            "movq   0x58(%rsi), %rdx",
            "movq   0x68(%rsi), %rax",
        ],
    ],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def disassemble(command: str) -> str:
    result = subprocess.run(
        ["arch", "-x86_64", "lldb", "--batch", LIBCP, "-o", command],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.stdout


def load_audit_module():
    spec = importlib.util.spec_from_file_location("lane_b_audit", AUDIT_PATH)
    require(spec is not None and spec.loader is not None, "cannot load Lane B audit module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    passed = []
    for name, (command, needles) in WINDOWS.items():
        text = disassemble(command)
        missing = [needle for needle in needles if needle not in text]
        require(not missing, f"{name}: missing disassembly anchors: {missing}")
        passed.append(name)

    audit = load_audit_module()
    static = audit.validate_lri_static()
    hashes = static["calibration_hashes"]
    require(hashes["32832"] == "722a6e721636c9c4", "intrinsics hash drift")
    require(hashes["262968"] == "f0c34433f9cf9b07", "distortion hash drift")
    require(hashes["35266"] == "6a0d52b6a4d1b4de", "depthcfg hash drift")
    for tier in audit.TIERS:
        require(static[tier]["present_values"] == [780, 3120, 4160], f"{tier}: ROI proto values drift")

    print("static_box_producer=OK windows=" + ",".join(passed))
    print(
        "lri_static=OK calibration_hashes="
        + ",".join(f"{size}:{digest}" for size, digest in sorted(hashes.items()))
        + " roi_values=780,3120,4160"
    )


if __name__ == "__main__":
    main()
