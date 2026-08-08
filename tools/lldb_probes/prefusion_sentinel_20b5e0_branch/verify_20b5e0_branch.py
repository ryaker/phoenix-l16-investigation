#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_sentinel_20b5e0_branch")
SENTINEL_HEX = "000080bf000080bf"
SENTINEL_PATH = 0x20BA90
OUTPUT_SKIP_TARGET = 0x20BAFD
OUTPUT_UPDATE_WRITE = 0x20BAC0

EXPECTED_COUNTS = {
    "28mm": {
        "after_store_hits": 3,
        "watchpoint_hits": 9,
    },
    "35mm": {
        "after_store_hits": 305,
        "watchpoint_hits": 9,
    },
    "70mm": {
        "after_store_hits": 315,
        "watchpoint_hits": 40,
    },
    "150mm": {
        "after_store_hits": 525,
        "watchpoint_hits": 40,
    },
}

COMMON_COUNTS = {
    "store_y_hits": 3,
    "after_store_pair_is_sentinel": 3,
    "watchpoints_armed": 3,
    "watchpoint_20b912_hits": 3,
    "branch_traces": 3,
    "x_branch_to_sentinel_path": 3,
    "output_branch_to_skip": 3,
    "output_update_write_reached": 0,
    "breakpoints_disabled_after_arm_limit": 1,
    "watchpoints_disabled_after_branch_trace_limit": 1,
    "watchpoints_disabled_after_cap": 0,
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier):
    hdr = ROOT / f"sentinel_20b5e0_branch_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def load_tier(tier):
    path = ROOT / f"sentinel_20b5e0_branch_{tier}.json"
    return json.loads(path.read_text())


def validate_flags(flags, *, x_branch):
    require(flags.get("read_ok") is True, "flags unreadable")
    if x_branch:
        require(flags.get("cf") == 0, f"x branch CF {flags}")
        require(flags.get("jae_taken") is True, f"x branch not jae-taken {flags}")
    else:
        require(flags.get("cf") == 1, f"output branch CF {flags}")
        require(flags.get("jbe_taken") is True, f"output branch not jbe-taken {flags}")


def validate_trace(tier, index, trace):
    pair = trace.get("pair_at_20b912") or {}
    require(pair.get("hex") == SENTINEL_HEX, f"{tier} trace {index}: non-sentinel pair {pair}")
    require(pair.get("is_sentinel_neg1_neg1") is True, f"{tier} trace {index}: pair flag false")

    x_step = trace.get("step_to_x_compare_branch") or {}
    require(x_step.get("hit") is True, f"{tier} trace {index}: did not reach x branch")
    validate_flags((trace.get("x_compare_branch") or {}).get("rflags_after_ucomiss") or {}, x_branch=True)
    require(
        (trace.get("x_branch_step") or {}).get("after") == SENTINEL_PATH,
        f"{tier} trace {index}: x branch did not step to sentinel path",
    )

    output_step = trace.get("step_to_output_compare_branch") or {}
    require(output_step.get("hit") is True, f"{tier} trace {index}: did not reach output branch")
    require(
        OUTPUT_UPDATE_WRITE not in (output_step.get("visited") or []),
        f"{tier} trace {index}: update write reached before output branch",
    )
    validate_flags((trace.get("output_compare_branch") or {}).get("rflags_after_ucomiss") or {}, x_branch=False)
    require(
        (trace.get("output_branch_step") or {}).get("after") == OUTPUT_SKIP_TARGET,
        f"{tier} trace {index}: output branch did not step to skip target",
    )


def validate_tier(tier):
    packet = load_tier(tier)
    require(packet.get("process_exit_status") == 0, f"{tier}: process did not exit cleanly")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: hit drive step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require_hdr_output(tier)

    counts = packet.get("counts") or {}
    for name, value in COMMON_COUNTS.items():
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")
    for name, value in EXPECTED_COUNTS[tier].items():
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")

    traces = packet.get("branch_traces") or []
    require(len(traces) == 3, f"{tier}: expected 3 branch traces")
    for index, trace in enumerate(traces):
        validate_trace(tier, index, trace)

    print(
        f"{tier}: OK 20b912_traces={counts['branch_traces']} "
        f"x_to_20ba90={counts['x_branch_to_sentinel_path']} "
        f"output_to_20bafd={counts['output_branch_to_skip']} "
        f"update_writes={counts['output_update_write_reached']} "
        f"watch_hits={counts['watchpoint_hits']}"
    )


def main():
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        validate_tier(tier)


if __name__ == "__main__":
    main()
