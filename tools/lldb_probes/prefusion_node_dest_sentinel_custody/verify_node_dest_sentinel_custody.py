#!/usr/bin/env python3
"""Verify same-address node-destination sentinel custody packets."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_node_dest_sentinel_custody"
TIERS = ("28mm", "35mm", "70mm", "150mm")

STORE_X = 0x21B923
STORE_Y = 0x21B92A
AFTER_SENTINEL_Y_STORE = 0x21B930
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
    require(report.get("errors") == [], f"{tier}: errors present {report.get('errors')}")
    require(report.get("drive_hit_step_cap") is False, f"{tier}: step cap hit")


def is_finite_non_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def is_full_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("is_sentinel_neg1_neg1")) and pair.get("hex") == SENTINEL_HEX


def stack_has_va(packet: dict, va: int) -> bool:
    return any(frame.get("libcp_va") == va for frame in packet.get("after_store_stack") or packet.get("stack") or [])


def verify_match(tier: str, match: dict, index: int) -> None:
    pair_addr = match.get("pair_addr")
    require(pair_addr, f"{tier}: match {index} missing pair address")

    copied = match.get("copied_pair") or {}
    copied_pair = copied.get("pair_at_copy") or {}
    require(copied_pair.get("addr") == pair_addr, f"{tier}: match {index} copied address mismatch")
    require(is_finite_non_sentinel(copied_pair), f"{tier}: match {index} copied pair not finite/non-sentinel")

    copy_event = match.get("copy_event") or {}
    require(copy_event.get("copy_site") in {"copy_a_ret_22a61f", "copy_b_ret_22c93f"}, f"{tier}: match {index} unexpected copy site")
    require(copy_event.get("copy_call_site") in {"copy_a_call_22a61a", "copy_b_call_22c93a"}, f"{tier}: match {index} unexpected copy call site")

    store_x = match.get("store_x_packet") or {}
    require(store_x.get("pc_va") == STORE_X, f"{tier}: match {index} missing x-store packet")
    require(store_x.get("pair_addr") == pair_addr, f"{tier}: match {index} x-store address mismatch")
    require(is_finite_non_sentinel(store_x.get("pair_before_x_store")), f"{tier}: match {index} x-store preimage not finite/non-sentinel")

    store_y = match.get("store_y_packet") or {}
    require(store_y.get("pc_va") == STORE_Y, f"{tier}: match {index} missing y-store packet")
    require(store_y.get("pair_addr") == pair_addr, f"{tier}: match {index} y-store address mismatch")
    mid = store_y.get("pair_mid_before_y_store") or {}
    require(mid.get("x_is_sentinel") is True, f"{tier}: match {index} mid-pair x not sentinel")
    require(mid.get("y_is_sentinel") is False, f"{tier}: match {index} mid-pair y already sentinel")

    after = match.get("pair_after_y_store") or {}
    require(is_full_sentinel(after), f"{tier}: match {index} after-store pair not full sentinel")
    require(after.get("addr") == pair_addr, f"{tier}: match {index} after-store address mismatch")
    require(stack_has_va(match, AFTER_SENTINEL_Y_STORE), f"{tier}: match {index} missing after-store stack VA")
    require(match.get("watchpoint_id"), f"{tier}: match {index} missing downstream watchpoint")
    require(match.get("watchpoint_error") is None, f"{tier}: match {index} watchpoint error")


def verify_watchpoint_sample(tier: str, sample: dict, matched_addrs: set[int], index: int) -> None:
    pair = sample.get("pair_now") or {}
    require(is_full_sentinel(pair), f"{tier}: watch sample {index} not full sentinel")
    require(pair.get("addr") in matched_addrs, f"{tier}: watch sample {index} address not matched")
    require(sample.get("libcp_va") != AFTER_SENTINEL_Y_STORE, f"{tier}: watch sample {index} stopped at arm site")


def verify_tier(tier: str) -> dict:
    report = load_json(RUN / f"node_dest_sentinel_custody_{tier}.json")
    require_clean(report, tier)
    require_hdr(RUN / f"node_dest_sentinel_custody_{tier}.hdr")

    counts = report["counts"]
    require(counts["copy_vectors_recorded"] > 0, f"{tier}: no copy vectors recorded")
    require(counts["copy_vectors_with_finite_pairs"] > 0, f"{tier}: no finite copy vectors recorded")
    require(counts["copied_pair_addrs_recorded"] > 0, f"{tier}: no copied pair addresses recorded")
    require(counts["copied_pair_addr_limit_hit"] == 0, f"{tier}: copied-pair address cap hit")
    require(counts["store_x_hits"] > 0, f"{tier}: no x-store hits")
    require(counts["store_y_hits"] > 0, f"{tier}: no y-store hits")
    require(counts["after_store_pair_is_sentinel"] > 0, f"{tier}: no full sentinel completions")
    require(counts["sentinel_matches"] > 0, f"{tier}: no copied-address sentinel matches")
    require(counts["watchpoints_armed"] == counts["sentinel_matches"], f"{tier}: watchpoint/match count mismatch")
    require(counts["watchpoint_hits"] > 0, f"{tier}: no downstream hits for matched sentinel address")

    matches = report.get("matches") or []
    require(len(matches) == counts["sentinel_matches"], f"{tier}: match count mismatch")
    for index, match in enumerate(matches, 1):
        verify_match(tier, match, index)

    unique_after = {match.get("pair_addr") for match in matches if match.get("pair_addr")}
    samples = report.get("watchpoint_samples") or []
    require(len(samples) > 0, f"{tier}: no downstream watchpoint samples")
    for index, sample in enumerate(samples, 1):
        verify_watchpoint_sample(tier, sample, unique_after, index)
    downstream_vas = {sample.get("libcp_va") for sample in samples if sample.get("libcp_va") is not None}

    return {
        "copy_vectors": counts["copy_vectors_recorded"],
        "copied_addrs": counts["copied_pair_addrs_recorded"],
        "after_store": counts["after_store_pair_is_sentinel"],
        "matches": counts["sentinel_matches"],
        "watch_hits": counts["watchpoint_hits"],
        "downstream_vas": len(downstream_vas),
        "unique_after": len(unique_after),
    }


def main() -> None:
    for tier in TIERS:
        row = verify_tier(tier)
        print(
            f"{tier}: OK copy_vectors={row['copy_vectors']} copied_addrs={row['copied_addrs']} "
            f"after_store_full={row['after_store']} matches={row['matches']} "
            f"watch_hits={row['watch_hits']} downstream_vas={row['downstream_vas']} "
            f"unique_after={row['unique_after']}"
        )


if __name__ == "__main__":
    main()
