#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_20ca00_copied_sentinel_gate")
SENTINEL_HEX = "000080bf000080bf"
GATE_BRANCH = 0x20D363
GATE_SKIP_TARGET = 0x20D565

EXPECTED = {
    "28mm": {
        "after_store_hits": 3,
        "after_store_without_pending": 0,
        "source_watch_hits": 4097,
        "source_copy_20d309_hits": 1912,
        "source_copy_index_matches": 0,
        "source_copy_index_mismatches": 1912,
        "source_watch_hit_cap_reached": 1,
        "source_watchpoints_disabled_after_cap": 1,
        "source_watchpoints_disabled_after_match": 0,
        "dest_watchpoints_armed": 0,
        "dest_watch_hits": 0,
        "dest_gate_hits": 0,
    },
    "35mm": {
        "after_store_hits": 305,
        "after_store_without_pending": 302,
        "source_watch_hits": 4097,
        "source_copy_20d309_hits": 2224,
        "source_copy_index_matches": 0,
        "source_copy_index_mismatches": 2224,
        "source_watch_hit_cap_reached": 1,
        "source_watchpoints_disabled_after_cap": 1,
        "source_watchpoints_disabled_after_match": 0,
        "dest_watchpoints_armed": 0,
        "dest_watch_hits": 0,
        "dest_gate_hits": 0,
    },
    "70mm": {
        "after_store_hits": 315,
        "after_store_without_pending": 312,
        "source_watch_hits": 310,
        "source_copy_20d309_hits": 244,
        "source_copy_index_matches": 1,
        "source_copy_index_mismatches": 243,
        "source_watch_hit_cap_reached": 0,
        "source_watchpoints_disabled_after_cap": 0,
        "source_watchpoints_disabled_after_match": 1,
        "dest_watchpoints_armed": 1,
        "dest_watch_hits": 301,
        "dest_copy_helper_hits": 14,
        "dest_gate_hits": 1,
        "dest_gate_addr_matches": 1,
        "dest_gate_sentinel_pairs": 1,
        "dest_gate_branch_to_skip": 1,
    },
    "150mm": {
        "after_store_hits": 525,
        "after_store_without_pending": 522,
        "source_watch_hits": 4097,
        "source_copy_20d309_hits": 731,
        "source_copy_index_matches": 0,
        "source_copy_index_mismatches": 731,
        "source_watch_hit_cap_reached": 1,
        "source_watchpoints_disabled_after_cap": 1,
        "source_watchpoints_disabled_after_match": 0,
        "dest_watchpoints_armed": 0,
        "dest_watch_hits": 0,
        "dest_gate_hits": 0,
    },
}

COMMON = {
    "store_y_hits": 3,
    "after_store_pair_is_sentinel": 3,
    "breakpoints_disabled_after_source_limit": 1,
    "source_watchpoints_armed": 3,
    "dest_watch_hit_cap_reached": 0,
    "dest_watchpoints_disabled_after_trace_limit": 0,
    "non_watchpoint_stops": 0,
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier):
    hdr = ROOT / f"copied_sentinel_gate_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def load_tier(tier):
    path = ROOT / f"copied_sentinel_gate_{tier}.json"
    return json.loads(path.read_text())


def validate_clean(tier, packet):
    require(packet.get("process_exit_status") == 0, f"{tier}: process exit {packet.get('process_exit_status')}")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: drive step cap hit")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require(not packet.get("non_watchpoint_stops"), f"{tier}: non-watchpoint stops {packet.get('non_watchpoint_stops')}")


def validate_counts(tier, packet):
    counts = packet.get("counts") or {}
    for name, expected in COMMON.items():
        require(counts.get(name) == expected, f"{tier}: {name} {counts.get(name)} != {expected}")
    for name, expected in EXPECTED[tier].items():
        require(counts.get(name) == expected, f"{tier}: {name} {counts.get(name)} != {expected}")


def validate_no_match_tier(tier, packet):
    require(not packet.get("gate_traces"), f"{tier}: unexpected gate traces")
    matches = [candidate for candidate in packet.get("copy_candidates", []) if candidate.get("index_matches_gate")]
    require(not matches, f"{tier}: unexpected index matches")


def validate_70mm_gate(packet):
    matches = [candidate for candidate in packet.get("copy_candidates", []) if candidate.get("index_matches_gate")]
    require(len(matches) == 1, f"70mm: expected one copied source/index match, got {len(matches)}")
    match = matches[0]
    require(match.get("source_pair_matches_watch") is True, "70mm: source pair did not match watch address")
    source_index = ((match.get("source_index") or {}).get("source_index"))
    gate_index = ((match.get("gate_index") or {}).get("gate_index"))
    require(source_index == 774 and gate_index == 774, f"70mm: unexpected indices {source_index}/{gate_index}")
    require((match.get("dest_pair_at_candidate") or {}).get("hex") == SENTINEL_HEX, "70mm: dest pair not sentinel at candidate")

    traces = packet.get("gate_traces") or []
    require(len(traces) == 1, f"70mm: expected one gate trace, got {len(traces)}")
    trace = traces[0]
    require((trace.get("pair_at_gate") or {}).get("hex") == SENTINEL_HEX, "70mm: gate pair not sentinel")
    branch = trace.get("gate_branch") or {}
    require(branch.get("pc_va") == GATE_BRANCH, f"70mm: gate branch PC {branch.get('pc_va')}")
    require(branch.get("computed_gate_addr_matches_watch") is True, "70mm: gate address did not match watched dest")
    flags = branch.get("rflags_after_ucomiss") or {}
    require(flags.get("read_ok") is True and flags.get("cf") == 0 and flags.get("jae_taken") is True, f"70mm: flags {flags}")
    step = trace.get("gate_branch_step") or {}
    require(step.get("before") == GATE_BRANCH and step.get("after") == GATE_SKIP_TARGET, f"70mm: branch step {step}")


def validate_tier(tier):
    packet = load_tier(tier)
    validate_clean(tier, packet)
    require_hdr_output(tier)
    validate_counts(tier, packet)
    if tier == "70mm":
        validate_70mm_gate(packet)
    else:
        validate_no_match_tier(tier, packet)
    counts = packet["counts"]
    print(
        f"{tier}: OK copy20d309={counts['source_copy_20d309_hits']} "
        f"matches={counts['source_copy_index_matches']} "
        f"dest_gate_hits={counts['dest_gate_hits']} "
        f"source_cap={counts['source_watch_hit_cap_reached']}"
    )


def main():
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        validate_tier(tier)


if __name__ == "__main__":
    main()
