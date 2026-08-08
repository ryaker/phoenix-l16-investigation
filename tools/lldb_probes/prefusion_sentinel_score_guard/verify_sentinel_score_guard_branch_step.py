#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_sentinel_score_guard_branch_step")
SENTINEL_HEX = "000080bf000080bf"
GUARD_BRANCH = 0x218BC4
GUARD_SKIP_TARGET = 0x218CB8

EXPECTED = {
    "70mm": {
        "after_store_hits": 315,
        "after_store_without_pending": 312,
        "watchpoint_hits": 12,
        "watchpoint_guard_hits": 6,
        "branch_traces": 6,
    },
    "150mm": {
        "after_store_hits": 1558,
        "after_store_without_pending": 1555,
        "watchpoint_hits": 3117,
        "watchpoint_guard_hits": 3,
        "branch_traces": 3,
    },
}

COMMON_COUNTS = {
    "store_y_hits": 3,
    "after_store_pair_is_sentinel": 3,
    "sentinel_pairs_skipped_before_arm": 0,
    "watchpoints_armed": 3,
    "watchpoint_guard_known_sentinel_hits": None,
    "watchpoint_guard_skip_by_flags": None,
    "watchpoint_guard_not_skip_by_flags": 0,
    "guard_branch_to_skip": None,
    "guard_branch_not_to_skip": 0,
    "breakpoints_disabled_after_arm_limit": 1,
    "watchpoints_disabled_after_branch_trace_limit": 1,
    "watchpoints_disabled_after_cap": 0,
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_tier(tier):
    return json.loads((ROOT / f"sentinel_score_guard_branch_{tier}.json").read_text())


def require_hdr_output(tier):
    hdr = ROOT / f"sentinel_score_guard_branch_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def validate_trace(tier, index, trace):
    pair = trace.get("pair_at_branch") or {}
    require(pair.get("hex") == SENTINEL_HEX, f"{tier}: trace {index} non-sentinel pair {pair}")
    require(pair.get("is_sentinel_neg1_neg1") is True, f"{tier}: trace {index} sentinel flag false")
    flags = trace.get("rflags_after_ucomiss") or {}
    require(flags.get("read_ok") is True, f"{tier}: trace {index} flags unreadable")
    require(flags.get("cf") == 0, f"{tier}: trace {index} CF {flags}")
    require(flags.get("pf") == 0, f"{tier}: trace {index} PF {flags}")
    require(flags.get("zf") == 0, f"{tier}: trace {index} ZF {flags}")
    require(flags.get("jae_taken") is True, f"{tier}: trace {index} jae not taken by flags")
    step = trace.get("branch_step") or {}
    require(step.get("before") == GUARD_BRANCH, f"{tier}: trace {index} before {step}")
    require(step.get("after") == GUARD_SKIP_TARGET, f"{tier}: trace {index} after {step}")


def validate_tier(tier):
    packet = load_tier(tier)
    require(packet.get("process_exit_status") == 0, f"{tier}: process exit {packet.get('process_exit_status')}")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: drive step cap hit")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require_hdr_output(tier)

    counts = packet.get("counts") or {}
    expected = EXPECTED[tier]
    for name, value in expected.items():
        if name == "branch_traces":
            require(counts.get("guard_branch_traces") == value, f"{tier}: guard_branch_traces {counts.get('guard_branch_traces')} != {value}")
        else:
            require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")
    for name, value in COMMON_COUNTS.items():
        if value is None:
            value = expected["branch_traces"]
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")

    traces = packet.get("guard_branch_traces") or []
    require(len(traces) == expected["branch_traces"], f"{tier}: branch trace packet count")
    for index, trace in enumerate(traces):
        validate_trace(tier, index, trace)

    guard_samples = packet.get("guard_samples") or []
    require(len(guard_samples) == expected["branch_traces"], f"{tier}: guard sample count")
    for index, sample in enumerate(guard_samples):
        require(sample.get("libcp_va") == GUARD_BRANCH, f"{tier}: sample {index} wrong guard VA")
        branch_trace = sample.get("branch_trace") or {}
        validate_trace(tier, index, branch_trace)

    print(
        f"{tier}: OK branch_traces={expected['branch_traces']} "
        f"guard_hits={counts['watchpoint_guard_hits']} "
        f"to_skip={counts['guard_branch_to_skip']} "
        f"watch_hits={counts['watchpoint_hits']}"
    )


def main():
    for tier in ("70mm", "150mm"):
        validate_tier(tier)


if __name__ == "__main__":
    main()
