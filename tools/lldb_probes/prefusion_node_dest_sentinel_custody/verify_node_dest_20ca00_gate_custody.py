#!/usr/bin/env python3
"""Verify copied node-destination custody into the 0x20ca00 gate path."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_custody"
TIERS = ("28mm", "35mm", "70mm", "150mm")

SENTINEL_HEX = "000080bf000080bf"
GATE_BRANCH = 0x20D363
GATE_SKIP_TARGET = 0x20D565


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


def is_full_sentinel(pair: dict | None) -> bool:
    return bool(pair) and pair.get("hex") == SENTINEL_HEX and pair.get("is_sentinel_neg1_neg1") is True


def require_clean(report: dict, tier: str) -> None:
    require(report.get("process_exit_status") == 0, f"{tier}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{tier}: step cap hit")
    require(report.get("errors") == [], f"{tier}: probe errors present {report.get('errors')}")


def validate_same_address_matches(report: dict, tier: str) -> dict[int, dict]:
    matches = report.get("matches") or []
    by_addr = {}
    for index, match in enumerate(matches):
        pair_addr = match.get("pair_addr")
        require(pair_addr, f"{tier}: match {index} missing pair address")
        require(pair_addr not in by_addr, f"{tier}: duplicate match address {pair_addr}")
        require(
            (match.get("copied_pair") or {}).get("pair_at_copy", {}).get("addr") == pair_addr,
            f"{tier}: match {index} copied address mismatch",
        )
        require(is_full_sentinel(match.get("pair_after_y_store")), f"{tier}: match {index} not sentinel after y-store")
        by_addr[pair_addr] = match
    return by_addr


def validate_candidate(tier: str, candidate: dict, matches_by_addr: dict[int, dict]) -> None:
    source_watch_addr = candidate.get("source_watch_addr")
    require(source_watch_addr in matches_by_addr, f"{tier}: candidate source address has no same-address match")
    require(candidate.get("source_pair_matches_watch") is True, f"{tier}: source pair does not match watched address")

    source = candidate.get("source_index") or {}
    require(source.get("source_index_ok") is True, f"{tier}: source index not reconstructed")
    gate = candidate.get("gate_index") or {}
    require(gate.get("read_ok") is True, f"{tier}: gate index unreadable")

    if candidate.get("index_matches_gate"):
        require(source.get("source_index") == gate.get("gate_index"), f"{tier}: index match flag with unequal indices")
        require(is_full_sentinel(candidate.get("dest_pair_at_candidate")), f"{tier}: matched destination pair not sentinel")


def validate_gate_trace(tier: str, trace: dict, candidate: dict) -> None:
    watch_addr = trace.get("watch_addr")
    require(watch_addr == candidate.get("dest_pair_addr"), f"{tier}: gate trace address does not match candidate destination")
    require(is_full_sentinel(trace.get("pair_at_gate")), f"{tier}: gate pair not sentinel")
    branch = trace.get("gate_branch") or {}
    require(branch.get("pc_va") == GATE_BRANCH, f"{tier}: gate branch PC {branch.get('pc_va')}")
    require(branch.get("computed_gate_addr_matches_watch") is True, f"{tier}: computed gate address mismatch")
    flags = branch.get("rflags_after_ucomiss") or {}
    require(flags.get("read_ok") is True, f"{tier}: unreadable gate flags")
    require(flags.get("cf") == 0 and flags.get("jae_taken") is True, f"{tier}: gate flags not jae-taken {flags}")
    step = trace.get("gate_branch_step") or {}
    require(step.get("before") == GATE_BRANCH and step.get("after") == GATE_SKIP_TARGET, f"{tier}: gate branch step {step}")


def validate_tier(tier: str) -> dict:
    report = load_json(RUN / f"node_dest_20ca00_gate_{tier}.json")
    require_clean(report, tier)
    require_hdr(RUN / f"node_dest_20ca00_gate_{tier}.hdr")
    matches_by_addr = validate_same_address_matches(report, tier)

    candidates = report.get("source_copy_20ca00_candidates") or []
    for candidate in candidates:
        validate_candidate(tier, candidate, matches_by_addr)

    matches = [candidate for candidate in candidates if candidate.get("index_matches_gate")]
    traces = report.get("gate_20ca00_traces") or []
    if traces:
        require(len(matches) >= len(traces), f"{tier}: more traces than index-match candidates")
        for trace in traces:
            matching = [candidate for candidate in matches if candidate.get("dest_pair_addr") == trace.get("watch_addr")]
            require(matching, f"{tier}: gate trace has no matching source candidate")
            validate_gate_trace(tier, trace, matching[0])

    counts = report.get("counts") or {}
    require(counts.get("source_copy_20d309_hits") == len(candidates), f"{tier}: candidate count mismatch")
    require(counts.get("source_copy_index_matches") == len(matches), f"{tier}: index-match count mismatch")
    require(counts.get("dest_gate_hits") == len(traces), f"{tier}: gate-trace count mismatch")

    return {
        "same_address_matches": len(matches_by_addr),
        "source_hits": counts.get("source_copy_20d309_hits"),
        "index_matches": counts.get("source_copy_index_matches"),
        "dest_watch_hits": counts.get("dest_watch_hits"),
        "gate_hits": counts.get("dest_gate_hits"),
        "watch_cap": counts.get("watchpoints_disabled_after_cap"),
        "dest_cap": counts.get("dest_watch_hit_cap_reached"),
    }


def main() -> None:
    for tier in TIERS:
        row = validate_tier(tier)
        print(
            f"{tier}: OK same_address={row['same_address_matches']} source20d309={row['source_hits']} "
            f"index_matches={row['index_matches']} dest_watch_hits={row['dest_watch_hits']} "
            f"gate_hits={row['gate_hits']} source_cap={row['watch_cap']} dest_cap={row['dest_cap']}"
        )


if __name__ == "__main__":
    main()
