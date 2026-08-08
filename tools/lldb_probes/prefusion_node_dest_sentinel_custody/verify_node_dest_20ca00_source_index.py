#!/usr/bin/env python3
"""Verify 0x20ca00 source/gate index packets for copied node-destination sentinels."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_node_dest_20ca00_source_index"
TIERS = ("28mm", "35mm", "70mm", "150mm")

SECOND_20CA00_COPY_RETURN = 0x20D309
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


def is_full_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("is_sentinel_neg1_neg1")) and pair.get("hex") == SENTINEL_HEX


def is_finite_non_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def require_clean(report: dict, tier: str) -> None:
    require(report.get("process_exit_status") == 0, f"{tier}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{tier}: step cap hit")
    require(report.get("errors") == [], f"{tier}: probe errors present {report.get('errors')}")


def verify_match(tier: str, match: dict) -> int:
    pair_addr = match.get("pair_addr")
    require(pair_addr, f"{tier}: missing matched pair address")
    copied_pair = (match.get("copied_pair") or {}).get("pair_at_copy") or {}
    require(copied_pair.get("addr") == pair_addr, f"{tier}: copied-pair address mismatch")
    require(is_finite_non_sentinel(copied_pair), f"{tier}: copied pair not finite/non-sentinel")
    after = match.get("pair_after_y_store") or {}
    require(after.get("addr") == pair_addr, f"{tier}: after-store address mismatch")
    require(is_full_sentinel(after), f"{tier}: after-store pair not full sentinel")
    return pair_addr


def verify_candidate(tier: str, candidate: dict, pair_addr: int, index: int) -> bool:
    require(candidate.get("caller_va") == SECOND_20CA00_COPY_RETURN, f"{tier} cand {index}: wrong caller")
    require(candidate.get("source_watch_addr") == pair_addr, f"{tier} cand {index}: source watch address mismatch")
    require(candidate.get("source_pair_matches_watch") is True, f"{tier} cand {index}: source pair did not match watch")

    source_index = candidate.get("source_index") or {}
    gate_index = candidate.get("gate_index") or {}
    require(source_index.get("source_index_ok") is True, f"{tier} cand {index}: source index unreadable")
    require(gate_index.get("read_ok") is True, f"{tier} cand {index}: gate index unreadable")
    require(
        (gate_index.get("parent_stack_frame") or {}).get("libcp_va") == SECOND_20CA00_COPY_RETURN,
        f"{tier} cand {index}: parent frame is not 0x20d309",
    )

    dest_pair = candidate.get("dest_pair_at_candidate") or {}
    require(dest_pair.get("read_ok") is True, f"{tier} cand {index}: dest pair unreadable")
    return bool(candidate.get("index_matches_gate"))


def verify_tier(tier: str) -> dict:
    report = load_json(RUN / f"node_dest_20ca00_index_{tier}.json")
    require_clean(report, tier)
    require_hdr(RUN / f"node_dest_20ca00_index_{tier}.hdr")

    matches = report.get("matches") or []
    require(len(matches) == 1, f"{tier}: expected exactly one node-destination match")
    pair_addr = verify_match(tier, matches[0])

    counts = report.get("counts") or {}
    candidates = report.get("source_copy_20ca00_candidates") or []
    require(counts.get("source_copy_20d309_hits", 0) > 0, f"{tier}: no 0x20d309 candidates")
    require(len(candidates) > 0, f"{tier}: no stored candidate packets")
    require(
        counts.get("source_copy_20d309_hits") == counts.get("source_copy_index_matches", 0) + counts.get("source_copy_index_mismatches", 0),
        f"{tier}: index match/mismatch counts do not add up",
    )

    stored_matches = 0
    for index, candidate in enumerate(candidates, 1):
        if verify_candidate(tier, candidate, pair_addr, index):
            stored_matches += 1
    require(stored_matches == counts.get("source_copy_index_matches", 0), f"{tier}: stored match count mismatch")

    return {
        "pair_addr": pair_addr,
        "candidates": counts.get("source_copy_20d309_hits"),
        "stored": len(candidates),
        "matches": counts.get("source_copy_index_matches"),
        "mismatches": counts.get("source_copy_index_mismatches"),
    }


def main() -> None:
    for tier in TIERS:
        row = verify_tier(tier)
        print(
            f"{tier}: OK same_addr={row['pair_addr']} "
            f"source_index_packets={row['candidates']} stored={row['stored']} "
            f"index_matches={row['matches']} index_mismatches={row['mismatches']}"
        )


if __name__ == "__main__":
    main()
