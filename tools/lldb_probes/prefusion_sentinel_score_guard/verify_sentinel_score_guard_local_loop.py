#!/usr/bin/env python3
import json
import pathlib
import re


ROOT = pathlib.Path("runs/prefusion_sentinel_score_guard_branch_step")
STATIC_DISASM = pathlib.Path(
    "runs/prefusion_node_sentinel_downstream_watch/static_disasm_218b30_218f90.log"
)

EXPECTED = {
    "70mm": {
        "file": "sentinel_score_guard_branch_70mm.json",
        "branch_traces": 6,
    },
    "150mm": {
        "file": "sentinel_score_guard_branch_150mm.json",
        "branch_traces": 3,
    },
}

STATIC_PATTERNS = {
    "x_lane_skip": r"218bc4:.*\bjae\b\s+0x218cb8\b",
    "y_lane_skip": r"218bd3:.*\bjbe\b\s+0x218cb8\b",
    "score_accumulate": r"218ca4:.*\baddss\b\s+%xmm3, %xmm1\b",
    "score_threshold_count": r"218cab:.*\baddl\b\s+%ecx, %r10d\b",
    "positive_coord_count": r"218cae:.*\bincl\b\s+%r9d\b",
    "skip_target_loop_tail": r"218cb8:.*\bincq\b\s+%rbx\b",
    "final_count_input": r"218cd6:.*\bcvtsi2ss\b\s+%r9d, %xmm2\b",
    "final_threshold_input": r"218cf2:.*\bcvtsi2ss\b\s+%r10d, %xmm2\b",
    "final_score_store": r"218cfb:.*\bmovss\b\s+%xmm2, \(%r14\)",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(json_name, tier):
    hdr = ROOT / json_name.replace(".json", ".hdr")
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def validate_static_window():
    text = STATIC_DISASM.read_text()
    for name, pattern in STATIC_PATTERNS.items():
        require(re.search(pattern, text), f"static disasm missing {name}: {pattern}")
    require(
        text.index("218bc4:") < text.index("218ca4:") < text.index("218cb8:"),
        "static order does not show accumulation body between x-lane skip and target",
    )
    require(
        text.index("218cd6:") < text.index("218cfb:"),
        "static order does not show final count/threshold-derived store",
    )


def validate_runtime_tier(tier):
    expected = EXPECTED[tier]
    packet = json.loads((ROOT / expected["file"]).read_text())
    require(packet.get("process_exit_status") == 0, f"{tier}: process did not exit cleanly")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: hit drive step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require_hdr_output(expected["file"], tier)

    counts = packet.get("counts") or {}
    require(
        counts.get("guard_branch_traces") == expected["branch_traces"],
        f"{tier}: branch trace count mismatch",
    )
    require(
        counts.get("guard_branch_to_skip") == expected["branch_traces"],
        f"{tier}: not all branch traces reached skip target",
    )
    require(counts.get("guard_branch_not_to_skip") == 0, f"{tier}: unexpected non-skip traces")

    samples = packet.get("guard_samples") or []
    branch_samples = [sample for sample in samples if sample.get("branch_trace")]
    require(len(branch_samples) == expected["branch_traces"], f"{tier}: branch sample count mismatch")
    for sample in branch_samples:
        pair = sample.get("pair_now") or {}
        flags = sample.get("rflags_after_ucomiss") or {}
        branch = sample.get("branch_trace") or {}
        step = branch.get("branch_step") or {}
        regs = sample.get("registers") or {}
        require(pair.get("hex") == "000080bf000080bf", f"{tier}: branch pair is not sentinel")
        require(flags.get("cf") == 0 and flags.get("jae_taken") is True, f"{tier}: branch flags not skip")
        require(step.get("before") == 0x218BC4, f"{tier}: branch before {step.get('before')}")
        require(step.get("after") == 0x218CB8, f"{tier}: branch after {step.get('after')}")
        require(regs.get("r9") is not None and regs.get("r10") is not None, f"{tier}: missing counters")
        require(regs.get("r14") is not None, f"{tier}: missing score-output register")

    print(
        f"{tier}: OK local_loop_skip_traces={expected['branch_traces']} "
        f"skip_target=0x218cb8 sentinel_pairs={len(branch_samples)}"
    )


def main():
    validate_static_window()
    for tier in ("70mm", "150mm"):
        validate_runtime_tier(tier)


if __name__ == "__main__":
    main()
