#!/usr/bin/env python3
"""Verify copied node-destination sentinel custody through the 0x218bc4 guard branch."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_node_dest_218bc4_branch_custody"
TIERS = ("70mm", "150mm")

STORE_X = 0x21B923
STORE_Y = 0x21B92A
SCORE_GUARD_AFTER_COMPARE = 0x218BC4
SCORE_GUARD_SKIP_TARGET = 0x218CB8
SENTINEL_HEX = "000080bf000080bf"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_hdr(path: Path) -> None:
    require(path.exists(), f"missing HDR output: {path}")
    with path.open("rb") as handle:
        require(handle.read(16).startswith(b"#?RADIANCE"), f"not Radiance HDR: {path}")


def require_clean(report: dict, tier: str) -> None:
    require(report.get("process_exit_status") == 0, f"{tier}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{tier}: step cap hit")
    require(report.get("errors") == [], f"{tier}: probe errors present {report.get('errors')}")


def is_finite_non_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def is_full_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("is_sentinel_neg1_neg1")) and pair.get("hex") == SENTINEL_HEX


def verify_match(tier: str, match: dict) -> int:
    pair_addr = match.get("pair_addr")
    require(pair_addr, f"{tier}: match missing pair address")

    copied = match.get("copied_pair") or {}
    copied_pair = copied.get("pair_at_copy") or {}
    require(copied_pair.get("addr") == pair_addr, f"{tier}: copied address mismatch")
    require(is_finite_non_sentinel(copied_pair), f"{tier}: copied pair not finite/non-sentinel")

    store_x = match.get("store_x_packet") or {}
    require(store_x.get("pc_va") == STORE_X, f"{tier}: missing x-store packet")
    require(store_x.get("pair_addr") == pair_addr, f"{tier}: x-store address mismatch")
    require(is_finite_non_sentinel(store_x.get("pair_before_x_store")), f"{tier}: x-store preimage not finite")

    store_y = match.get("store_y_packet") or {}
    require(store_y.get("pc_va") == STORE_Y, f"{tier}: missing y-store packet")
    require(store_y.get("pair_addr") == pair_addr, f"{tier}: y-store address mismatch")
    require(is_full_sentinel(match.get("pair_after_y_store")), f"{tier}: after-store pair not full sentinel")
    return pair_addr


def verify_guard_trace(tier: str, trace: dict, pair_addr: int) -> None:
    require(trace.get("watch_addr") == pair_addr, f"{tier}: trace watch address mismatch")
    pair = trace.get("pair_at_branch") or {}
    require(pair.get("addr") == pair_addr, f"{tier}: guard pair address mismatch")
    require(is_full_sentinel(pair), f"{tier}: guard pair not full sentinel")

    stack = trace.get("initial_stack") or []
    require(stack and stack[0].get("libcp_va") == SCORE_GUARD_AFTER_COMPARE, f"{tier}: trace did not start at 0x218bc4")

    flags = trace.get("rflags_after_ucomiss") or {}
    require(flags.get("read_ok") is True, f"{tier}: flags unreadable")
    require(flags.get("cf") == 0, f"{tier}: guard CF not zero: {flags}")
    require(flags.get("jae_taken") is True, f"{tier}: guard branch not jae-taken: {flags}")

    step = trace.get("branch_step") or {}
    require(step.get("before") == SCORE_GUARD_AFTER_COMPARE, f"{tier}: branch-step before mismatch")
    require(step.get("after") == SCORE_GUARD_SKIP_TARGET, f"{tier}: branch did not step to skip target")


def verify_tier(tier: str) -> dict:
    report = load_json(RUN / f"node_dest_218bc4_branch_{tier}.json")
    require_clean(report, tier)
    require_hdr(RUN / f"node_dest_218bc4_branch_{tier}.hdr")

    counts = report.get("counts") or {}
    require(counts.get("sentinel_matches") == 1, f"{tier}: expected one sentinel match")
    require(counts.get("watchpoints_armed") == 1, f"{tier}: expected one watchpoint")
    require(counts.get("watchpoint_218bc4_hits", 0) >= 1, f"{tier}: no 0x218bc4 watchpoint hit")
    require(counts.get("guard_branch_traces") == 1, f"{tier}: expected one guard branch trace")
    require(counts.get("guard_branch_to_skip") == 1, f"{tier}: guard branch-to-skip count mismatch")
    require(counts.get("guard_branch_not_to_skip") == 0, f"{tier}: guard branch non-skip observed")

    matches = report.get("matches") or []
    require(len(matches) == 1, f"{tier}: expected one match packet")
    pair_addr = verify_match(tier, matches[0])

    traces = report.get("guard_branch_traces") or []
    require(len(traces) == 1, f"{tier}: expected one guard branch trace packet")
    verify_guard_trace(tier, traces[0], pair_addr)

    samples = report.get("watchpoint_samples") or []
    require(samples, f"{tier}: no watchpoint samples")
    require(any(sample.get("libcp_va") == SCORE_GUARD_AFTER_COMPARE for sample in samples), f"{tier}: no sampled 0x218bc4 stop")
    for sample in samples:
        pair = sample.get("pair_now") or {}
        require(is_full_sentinel(pair), f"{tier}: sampled downstream pair not sentinel")
        require(pair.get("addr") == pair_addr, f"{tier}: sampled downstream address mismatch")

    copied = (matches[0].get("copied_pair") or {}).get("pair_at_copy") or {}
    return {
        "pair_addr": pair_addr,
        "pair_index": (matches[0].get("copied_pair") or {}).get("pair_index"),
        "copied_hex": copied.get("hex"),
        "watch_hits": counts.get("watchpoint_hits"),
        "guard_hits": counts.get("watchpoint_218bc4_hits"),
    }


def main() -> None:
    for tier in TIERS:
        row = verify_tier(tier)
        print(
            f"{tier}: OK same_addr={row['pair_addr']} pair_index={row['pair_index']} "
            f"copied_hex={row['copied_hex']} guard_hits={row['guard_hits']} "
            f"watch_hits={row['watch_hits']} branch=0x218bc4->0x218cb8"
        )


if __name__ == "__main__":
    main()
