#!/usr/bin/env python3
"""Verify selected same-address node-destination custody into the 0x20ca00 gate."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GENERIC_RUN = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_custody"
TARGET_RUN = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_target_custody"

SENTINEL_HEX = "000080bf000080bf"
GATE_BRANCH = 0x20D363
GATE_SKIP_TARGET = 0x20D565


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_hdr(path: Path) -> None:
    require(path.exists(), f"missing HDR output: {path}")
    with path.open("rb") as handle:
        require(handle.read(16).startswith(b"#?RADIANCE"), f"not Radiance HDR: {path}")


def is_sentinel(pair: dict | None) -> bool:
    return bool(pair) and pair.get("hex") == SENTINEL_HEX and pair.get("is_sentinel_neg1_neg1") is True


def require_clean(report: dict, tier: str) -> None:
    require(report.get("process_exit_status") == 0, f"{tier}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{tier}: drive step cap hit")
    require(report.get("errors") == [], f"{tier}: probe errors {report.get('errors')}")


def matches_by_addr(report: dict, tier: str) -> dict[int, dict]:
    out = {}
    for index, match in enumerate(report.get("matches") or []):
        pair_addr = match.get("pair_addr")
        copied = match.get("copied_pair") or {}
        require(pair_addr, f"{tier}: match {index} missing address")
        require(pair_addr not in out, f"{tier}: duplicate match address")
        require((copied.get("pair_at_copy") or {}).get("addr") == pair_addr, f"{tier}: copied address mismatch")
        require((copied.get("pair_at_copy") or {}).get("both_finite") is True, f"{tier}: copied pair not finite")
        require(is_sentinel(match.get("pair_after_y_store")), f"{tier}: pair not sentinel after store")
        out[pair_addr] = match
    return out


def validate_positive(
    report: dict,
    tier: str,
    expected_index: int,
    expected_copy_hex: str,
) -> dict:
    by_addr = matches_by_addr(report, tier)
    candidates = report.get("source_copy_20ca00_candidates") or []
    positive = [candidate for candidate in candidates if candidate.get("index_matches_gate")]
    require(len(positive) == 1, f"{tier}: expected one index-match candidate, got {len(positive)}")
    candidate = positive[0]

    source_addr = candidate.get("source_watch_addr")
    require(source_addr in by_addr, f"{tier}: positive candidate has no same-address source match")
    match = by_addr[source_addr]
    copied = match.get("copied_pair") or {}
    require(copied.get("pair_index") == expected_index, f"{tier}: copied pair index")
    require((copied.get("pair_at_copy") or {}).get("hex") == expected_copy_hex, f"{tier}: copied pair bytes")
    require(candidate.get("expected_source_pair") == source_addr, f"{tier}: source cursor mismatch")
    require(candidate.get("source_pair_matches_watch") is True, f"{tier}: source watch mismatch")

    source = candidate.get("source_index") or {}
    gate = candidate.get("gate_index") or {}
    require(source.get("source_index_ok") is True, f"{tier}: source index unreadable")
    require(gate.get("read_ok") is True, f"{tier}: gate index unreadable")
    require(source.get("source_index") == expected_index, f"{tier}: source index")
    require(gate.get("gate_index") == expected_index, f"{tier}: gate index")
    require(is_sentinel(candidate.get("dest_pair_at_candidate")), f"{tier}: destination not sentinel at copy")

    traces = report.get("gate_20ca00_traces") or []
    require(len(traces) == 1, f"{tier}: expected one gate trace")
    trace = traces[0]
    require(trace.get("watch_addr") == candidate.get("dest_pair_addr"), f"{tier}: destination trace address")
    require(is_sentinel(trace.get("pair_at_gate")), f"{tier}: destination not sentinel at gate")
    branch = trace.get("gate_branch") or {}
    require(branch.get("pc_va") == GATE_BRANCH, f"{tier}: gate branch PC")
    require(branch.get("computed_gate_addr_matches_watch") is True, f"{tier}: computed gate address mismatch")
    flags = branch.get("rflags_after_ucomiss") or {}
    require(flags.get("read_ok") is True, f"{tier}: gate flags unreadable")
    require(flags.get("cf") == 0 and flags.get("jae_taken") is True, f"{tier}: gate branch not taken")
    step = trace.get("gate_branch_step") or {}
    require(step.get("before") == GATE_BRANCH and step.get("after") == GATE_SKIP_TARGET, f"{tier}: gate step")

    counts = report.get("counts") or {}
    require(counts.get("source_copy_20d309_hits") == len(candidates), f"{tier}: source-candidate count")
    require(counts.get("source_copy_index_matches") == 1, f"{tier}: source-index match count")
    require(counts.get("dest_watchpoints_armed") == 1, f"{tier}: destination watchpoint count")
    require(counts.get("dest_gate_hits") == 1, f"{tier}: destination gate count")
    require(counts.get("dest_gate_addr_matches") == 1, f"{tier}: destination address count")
    require(counts.get("dest_gate_sentinel_pairs") == 1, f"{tier}: destination sentinel count")
    require(counts.get("dest_gate_branch_to_skip") == 1, f"{tier}: destination skip count")

    return {
        "same_address_matches": len(by_addr),
        "source_hits": counts.get("source_copy_20d309_hits"),
        "watch_hits": counts.get("watchpoint_hits"),
    }


def validate_negative(
    report: dict,
    tier: str,
    expected_pair_indices: set[int],
    expected_source_cap: int,
    require_source_hits: bool,
) -> dict:
    by_addr = matches_by_addr(report, tier)
    observed_indices = {
        (match.get("copied_pair") or {}).get("pair_index")
        for match in by_addr.values()
    }
    require(observed_indices == expected_pair_indices, f"{tier}: targeted pair indices {observed_indices}")

    candidates = report.get("source_copy_20ca00_candidates") or []
    require(not any(candidate.get("index_matches_gate") for candidate in candidates), f"{tier}: unexpected index match")
    require(not report.get("gate_20ca00_traces"), f"{tier}: unexpected gate trace")

    counts = report.get("counts") or {}
    require(counts.get("source_copy_20d309_hits") == len(candidates), f"{tier}: source-candidate count")
    require(counts.get("source_copy_index_matches") == 0, f"{tier}: source-index match count")
    require(counts.get("dest_watchpoints_armed") == 0, f"{tier}: unexpected destination watchpoint")
    require(counts.get("dest_gate_hits") == 0, f"{tier}: unexpected destination gate")
    require(counts.get("watchpoints_disabled_after_cap") == expected_source_cap, f"{tier}: source-cap flag")
    if require_source_hits:
        require(counts.get("source_copy_20d309_hits", 0) > 0, f"{tier}: expected source-copy hits")
    else:
        require(counts.get("source_copy_20d309_hits") == 0, f"{tier}: unexpected source-copy hits")

    return {
        "same_address_matches": len(by_addr),
        "source_hits": counts.get("source_copy_20d309_hits"),
        "watch_hits": counts.get("watchpoint_hits"),
        "source_cap": counts.get("watchpoints_disabled_after_cap"),
    }


def main() -> None:
    selected = {
        "28mm": (
            TARGET_RUN / "node_dest_20ca00_gate_target_28mm.json",
            TARGET_RUN / "node_dest_20ca00_gate_target_28mm.hdr",
        ),
        "35mm": (
            TARGET_RUN / "node_dest_20ca00_gate_target_35mm.json",
            TARGET_RUN / "node_dest_20ca00_gate_target_35mm.hdr",
        ),
        "70mm": (
            GENERIC_RUN / "node_dest_20ca00_gate_70mm.json",
            GENERIC_RUN / "node_dest_20ca00_gate_70mm.hdr",
        ),
        "150mm": (
            TARGET_RUN / "node_dest_20ca00_gate_target_150mm.json",
            TARGET_RUN / "node_dest_20ca00_gate_target_150mm.hdr",
        ),
    }

    reports = {}
    for tier, (json_path, hdr_path) in selected.items():
        report = load(json_path)
        require_clean(report, tier)
        require_hdr(hdr_path)
        reports[tier] = report

    row_28 = validate_positive(reports["28mm"], "28mm", 5394, "0040ea4400007a44")
    row_35 = validate_negative(reports["35mm"], "35mm", {3673, 5411, 5577}, 1, True)
    row_70 = validate_positive(reports["70mm"], "70mm", 77, "0020a74400007042")
    row_150 = validate_negative(reports["150mm"], "150mm", {240}, 0, False)

    print(
        f"28mm: OK index=5394 same_address={row_28['same_address_matches']} "
        f"source20d309={row_28['source_hits']} watch_hits={row_28['watch_hits']} gate_hits=1"
    )
    print(
        f"35mm: OK targeted={row_35['same_address_matches']} source20d309={row_35['source_hits']} "
        f"watch_hits={row_35['watch_hits']} source_cap={row_35['source_cap']} gate_hits=0"
    )
    print(
        f"70mm: OK index=77 same_address={row_70['same_address_matches']} "
        f"source20d309={row_70['source_hits']} watch_hits={row_70['watch_hits']} gate_hits=1"
    )
    print(
        f"150mm: OK targeted={row_150['same_address_matches']} source20d309={row_150['source_hits']} "
        f"watch_hits={row_150['watch_hits']} source_cap={row_150['source_cap']} gate_hits=0"
    )


if __name__ == "__main__":
    main()
