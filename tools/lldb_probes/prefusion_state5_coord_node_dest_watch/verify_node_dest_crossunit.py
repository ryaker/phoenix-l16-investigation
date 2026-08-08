#!/usr/bin/env python3
"""Verify exact-28mm Unit-2 state-5 node-destination consumer evidence.

This checker intentionally validates only a second-body discriminator for the
already-admitted Unit-1 four-focal node-destination proof. It does not promote
the result to all-body, all-focal, image-effect, reducer-closure, or final
acceptance/rejection proof.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "runs/prefusion_state5_coord_node_dest_watch"
REPORT = RUN_DIR / "node_dest_watch_unit2_28mm.json"
HDR = RUN_DIR / "node_dest_watch_unit2_28mm.hdr"
SCRIPT = (
    ROOT
    / "tools/lldb_probes/prefusion_state5_coord_node_dest_watch"
    / "node_dest_watch_unit2_28mm.lldb"
)
UNIT2_LRI = "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"

NODE_DEST_CONSUMER_VAS = {0x21B444, 0x21B44C, 0x21C2B0, 0x21C2B6}
NODE_DEST_FRAME1_VAS = {0x22A9E7, 0x21C59C}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_report() -> dict:
    require(REPORT.exists(), f"missing report {REPORT}")
    with REPORT.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require_hdr() -> None:
    require(HDR.exists(), f"missing HDR {HDR}")
    with HDR.open("rb") as fh:
        require(fh.read(16).startswith(b"#?RADIANCE"), f"not Radiance HDR: {HDR}")


def pair_is_finite_non_sentinel(pair: dict) -> bool:
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def frame_va(sample: dict, index: int) -> int | None:
    stack = sample.get("stack") or []
    if len(stack) <= index:
        return None
    return stack[index].get("libcp_va")


def main() -> None:
    script_text = SCRIPT.read_text(encoding="utf-8")
    require(UNIT2_LRI in script_text, "Unit-2 exact-28mm LRI missing from LLDB script")
    require("node_dest_watch_unit2_28mm" in script_text, "Unit-2 output name missing from script")

    report = load_report()
    require_hdr()

    require(report.get("process_exit_status") == 0, "process did not exit cleanly")
    require(report.get("errors") == [], f"probe errors present: {report.get('errors')}")
    require(report.get("drive_hit_step_cap") is False, "drive hit step cap")
    require("Unit-2 exact 28mm" in report.get("label", ""), "report label is not Unit-2 exact 28mm")

    counts = report.get("counts") or {}
    require(counts.get("copy_pairs_admitted", 0) > 0, "no copied node-destination pairs admitted")
    require(counts.get("copy_call_a_hits", 0) > 0, "missing 0x22a61a copy call")
    require(counts.get("copy_ret_a_hits", 0) > 0, "missing 0x22a61f copy return")
    require(counts.get("watchpoints_armed") == 3, "expected exactly three watchpoints")
    require(counts.get("watchpoint_hits", 0) > 0, "no watchpoint hits")

    armed = report.get("armed") or []
    require(len(armed) == 3, f"unexpected armed watchpoint count {len(armed)}")
    require(
        all(pair_is_finite_non_sentinel(item.get("pair_at_arm") or {}) for item in armed),
        "armed pair was not finite non-sentinel",
    )

    samples = report.get("watchpoint_samples") or []
    require(samples, "missing watchpoint samples")
    require(
        all(pair_is_finite_non_sentinel(sample.get("pair_now") or {}) for sample in samples),
        "non-finite or sentinel pair observed in node-destination consumer samples",
    )
    vas = sorted({sample.get("libcp_va") for sample in samples})
    require(set(vas) == NODE_DEST_CONSUMER_VAS, f"unexpected consumer VAs {vas}")
    require(
        all(frame_va(sample, 1) in NODE_DEST_FRAME1_VAS for sample in samples),
        "unexpected frame-1 stack for node-destination consumer sample",
    )

    first = armed[0]
    print(
        "Unit-2 exact 28mm: OK "
        f"admitted={counts['copy_pairs_admitted']} "
        f"watchpoints={counts['watchpoints_armed']} "
        f"hits={counts['watchpoint_hits']} "
        f"first_pair_index={first.get('pair_index')} "
        f"consumer_vas={','.join(f'0x{va:x}' for va in vas)}"
    )
    print(
        "scope=second-body discriminator for state-5 node-destination non-copy "
        "candidate/index/scoring consumer; image effect, reducer closure, and final "
        "acceptance remain open"
    )


if __name__ == "__main__":
    main()
