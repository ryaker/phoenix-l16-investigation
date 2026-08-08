#!/usr/bin/env python3
"""Verify direct wide-path breakpoint counts around 0x218bc4."""

from __future__ import annotations

import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/prefusion_wide_218bc4_path_census"
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/"
    "libcp.dylib"
)
SITES = (
    (0x216F60, "parent"),
    (0x217926, "callback_construct"),
    (0x217992, "callback_dispatch"),
    (0x219210, "callback"),
    (0x219375, "helper_call"),
    (0x218940, "helper"),
    (0x218BC4, "guard"),
    (0x2179D9, "cost0_construct"),
    (0x217A42, "cost0_dispatch"),
    (0x218E20, "cost0_callback"),
    (0x218F7C, "cost0_helper_call"),
    (0x218B30, "cost0_helper"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u64(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob: bytes, offset: int) -> str:
    end = blob.index(b"\0", offset)
    return blob[offset:end].decode("ascii")


def rel32_target(blob: bytes, callsite: int) -> int:
    require(blob[callsite] == 0xE8, f"0x{callsite:x}: not a direct call")
    displacement = struct.unpack_from("<i", blob, callsite + 1)[0]
    return callsite + 5 + displacement


def verify_static() -> None:
    blob = LIBCP.read_bytes()
    cost0_name = cstring(blob, u64(blob, 0x658108))
    cost1_name = cstring(blob, u64(blob, 0x658188))
    require("SparseMirrorAngleOptimizer8optimize" in cost0_name, "cost0 owner")
    require("E3$_1" in cost0_name, "cost0 callback ordinal")
    require("SparseMirrorAngleOptimizer8optimize" in cost1_name, "cost1 owner")
    require("E3$_2" in cost1_name, "cost1 callback ordinal")
    require(u64(blob, 0x6580E0) == 0x218E20, "cost0 callback slot")
    require(u64(blob, 0x658168) == 0x219210, "cost1 callback slot")
    require(rel32_target(blob, 0x218F7C) == 0x218B30, "cost0 helper call")
    require(rel32_target(blob, 0x219375) == 0x218940, "cost1 helper call")
    require(
        blob[0x2178ED : 0x21791C]
        == bytes.fromhex(
            "8b85 0cfaffff 85c0 0f84bc000000 83f801 "
            "4c8b35c37a4300 4d8b36 448ba5f4f9ffff "
            "4c8bbde8f9ffff 0f856f050000"
        ),
        "CostFunction 0/1 branch bytes changed",
    )


def counts(text: str) -> dict[int, int]:
    result: dict[int, int] = {}
    for va, _ in SITES:
        pattern = re.compile(
            rf"address = libcp\.dylib\[[^\]]*0x{va:016x}\].*?"
            rf"hit count = (\d+)",
            re.DOTALL,
        )
        match = pattern.search(text)
        require(match is not None, f"missing breakpoint listing for 0x{va:x}")
        result[va] = int(match.group(1))
    return result


def main() -> None:
    verify_static()
    print(
        "STATIC: OK CostFunction=0 -> optimize::$_1 -> 0x218b30; "
        "CostFunction=1 -> optimize::$_2 -> 0x218940"
    )
    for tier in ("28mm", "35mm"):
        log = (RUN / f"wide_{tier}.log").read_text(errors="replace")
        require("exited with status = 0" in log, f"{tier}: process did not exit 0")
        hdr = RUN / f"wide_{tier}.hdr"
        require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: bad HDR")
        values = counts(log)
        require(values[0x216F60] > 0, f"{tier}: parent not live")
        require(values[0x217926] == values[0x216F60], f"{tier}: cost1 arm mismatch")
        require(values[0x217992] == values[0x216F60], f"{tier}: cost1 dispatch mismatch")
        require(values[0x219210] > 0, f"{tier}: cost1 callback not live")
        require(values[0x219375] > 0, f"{tier}: cost1 helper call not live")
        for va in (0x2179D9, 0x217A42, 0x218E20, 0x218F7C, 0x218B30, 0x218BC4):
            require(values[va] == 0, f"{tier}: unexpected cost0/guard hit 0x{va:x}")
        rendered = " ".join(
            f"{name}={values[va]}" for va, name in SITES
        )
        print(f"{tier}: OK {rendered}")


if __name__ == "__main__":
    main()
