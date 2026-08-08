#!/usr/bin/env python3
"""Verify copied node-destination sentinel custody through the 0x20b5e0 branch path."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_node_dest_20b5e0_branch_custody"
TIERS = ("28mm", "35mm", "70mm", "150mm")

STORE_X = 0x21B923
STORE_Y = 0x21B92A
AFTER_SENTINEL_Y_STORE = 0x21B930
WATCH_STOP_AFTER_X_LOAD = 0x20B912
SENTINEL_PATH = 0x20BA90
OUTPUT_SKIP_TARGET = 0x20BAFD
OUTPUT_UPDATE_WRITE = 0x20BAC0
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


def is_finite_non_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def is_full_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("is_sentinel_neg1_neg1")) and pair.get("hex") == SENTINEL_HEX


def require_clean(report: dict, tier: str) -> None:
    require(report.get("process_exit_status") == 0, f"{tier}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{tier}: step cap hit")
    require(report.get("errors") == [], f"{tier}: probe errors present {report.get('errors')}")


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
    mid = store_y.get("pair_mid_before_y_store") or {}
    require(mid.get("x_is_sentinel") is True, f"{tier}: mid x lane not sentinel")
    require(mid.get("y_is_sentinel") is False, f"{tier}: mid y lane already sentinel")

    after = match.get("pair_after_y_store") or {}
    require(after.get("addr") == pair_addr, f"{tier}: after-store address mismatch")
    require(is_full_sentinel(after), f"{tier}: after-store pair not full sentinel")
    require(match.get("watchpoint_id"), f"{tier}: missing downstream watchpoint")
    require(match.get("watchpoint_error") is None, f"{tier}: watchpoint error")
    return pair_addr


def validate_flags(flags: dict, tier: str, *, x_branch: bool) -> None:
    require(flags.get("read_ok") is True, f"{tier}: flags unreadable")
    if x_branch:
        require(flags.get("cf") == 0, f"{tier}: x branch CF not 0: {flags}")
        require(flags.get("jae_taken") is True, f"{tier}: x branch not jae-taken: {flags}")
    else:
        require(flags.get("cf") == 1, f"{tier}: output branch CF not 1: {flags}")
        require(flags.get("jbe_taken") is True, f"{tier}: output branch not jbe-taken: {flags}")


def verify_branch_trace(tier: str, trace: dict, pair_addr: int) -> None:
    require(trace.get("watch_addr") == pair_addr, f"{tier}: branch trace watch address mismatch")
    pair = trace.get("pair_at_20b912") or {}
    require(pair.get("addr") == pair_addr, f"{tier}: 20b912 pair address mismatch")
    require(is_full_sentinel(pair), f"{tier}: 20b912 pair not full sentinel")

    stack = trace.get("initial_stack") or []
    require(stack and stack[0].get("libcp_va") == WATCH_STOP_AFTER_X_LOAD, f"{tier}: trace did not start at 0x20b912")

    x_step = trace.get("step_to_x_compare_branch") or {}
    require(x_step.get("hit") is True, f"{tier}: did not reach x compare branch")
    validate_flags((trace.get("x_compare_branch") or {}).get("rflags_after_ucomiss") or {}, tier, x_branch=True)
    require((trace.get("x_branch_step") or {}).get("after") == SENTINEL_PATH, f"{tier}: x branch did not step to sentinel path")

    output_step = trace.get("step_to_output_compare_branch") or {}
    require(output_step.get("hit") is True, f"{tier}: did not reach output compare branch")
    require(OUTPUT_UPDATE_WRITE not in (output_step.get("visited") or []), f"{tier}: update write reached before output branch")
    validate_flags((trace.get("output_compare_branch") or {}).get("rflags_after_ucomiss") or {}, tier, x_branch=False)
    require((trace.get("output_branch_step") or {}).get("after") == OUTPUT_SKIP_TARGET, f"{tier}: output branch did not step to skip")


def verify_tier(tier: str) -> dict:
    report = load_json(RUN / f"node_dest_20b5e0_branch_{tier}.json")
    require_clean(report, tier)
    require_hdr(RUN / f"node_dest_20b5e0_branch_{tier}.hdr")

    counts = report.get("counts") or {}
    require(counts.get("sentinel_matches") == 1, f"{tier}: expected one sentinel match")
    require(counts.get("watchpoints_armed") == 1, f"{tier}: expected one watchpoint")
    require(counts.get("watchpoint_20b912_hits", 0) >= 1, f"{tier}: no 0x20b912 watchpoint hit")
    require(counts.get("branch_traces") == 1, f"{tier}: expected one branch trace")
    require(counts.get("x_branch_to_sentinel_path") == 1, f"{tier}: x branch count mismatch")
    require(counts.get("output_branch_to_skip") == 1, f"{tier}: output branch count mismatch")
    require(counts.get("output_update_write_reached") == 0, f"{tier}: update write reached")

    matches = report.get("matches") or []
    require(len(matches) == 1, f"{tier}: expected one match packet")
    pair_addr = verify_match(tier, matches[0])

    traces = report.get("branch_traces") or []
    require(len(traces) == 1, f"{tier}: expected one branch trace packet")
    verify_branch_trace(tier, traces[0], pair_addr)

    samples = report.get("watchpoint_samples") or []
    require(any(sample.get("libcp_va") == WATCH_STOP_AFTER_X_LOAD for sample in samples), f"{tier}: no sampled 0x20b912 stop")
    for sample in samples:
        pair = sample.get("pair_now") or {}
        require(is_full_sentinel(pair), f"{tier}: sampled downstream pair not sentinel")
        require(pair.get("addr") == pair_addr, f"{tier}: sampled downstream address mismatch")

    return {
        "copied_addrs": counts.get("copied_pair_addrs_recorded"),
        "watch_hits": counts.get("watchpoint_hits"),
        "branch_traces": counts.get("branch_traces"),
        "pair_addr": pair_addr,
    }


def main() -> None:
    for tier in TIERS:
        row = verify_tier(tier)
        print(
            f"{tier}: OK copied_addrs={row['copied_addrs']} "
            f"watch_hits={row['watch_hits']} branch_traces={row['branch_traces']} "
            f"pair_addr={row['pair_addr']}"
        )


if __name__ == "__main__":
    main()
