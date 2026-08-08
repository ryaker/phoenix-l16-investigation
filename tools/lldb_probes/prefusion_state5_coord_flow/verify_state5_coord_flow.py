#!/usr/bin/env python3
"""Verify the Lane A state-5 coordinate-flow proof packets.

This checker validates the repo-local JSON/HDR artifacts for:

- state-5 coordinate output at 0x2457c0;
- state+0x1e8 copy-out by 0xe8e70;
- copied destination-vector propagation;
- node-destination non-copy candidate/index/scoring consumption.

It intentionally verifies custody and bounded consumer facts only. It does not
promote those facts to image-effect proof, public State semantics, reducer
closure, or final acceptance/rejection semantics.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TIERS = ("28mm", "35mm", "70mm", "150mm")

OUTPUT_DIR = ROOT / "runs/prefusion_state5_coord_output"
CONSUMER_DIR = ROOT / "runs/prefusion_state5_coord_consumer_watch"
COPY_DEST_DIR = ROOT / "runs/prefusion_state5_coord_copy_dest_watch"
NODE_DEST_DIR = ROOT / "runs/prefusion_state5_coord_node_dest_watch"

OUTPUT_TARGETS = {
    "28mm": 2,
    "35mm": 2,
    "70mm": 1,
    "150mm": 1,
}

CONSUMER_CALLERS = {0x224E28, 0x224F08}
COPY_DEST_CALLERS = {0x224E28, 0x224F08, 0x22A61F, 0x22C93F}
NODE_DEST_CONSUMER_VAS = {0x21B444, 0x21B44C, 0x21C2B0, 0x21C2B6}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require_hdr(path: Path) -> None:
    require(path.exists(), f"missing HDR output: {path}")
    with path.open("rb") as fh:
        header = fh.read(16)
    require(header.startswith(b"#?RADIANCE"), f"not Radiance HDR: {path}")


def require_clean_process(data: dict, label: str) -> None:
    require(data.get("process_exit_status") == 0, f"{label}: nonzero exit")
    require(data.get("errors") == [], f"{label}: errors present")
    require(data.get("drive_hit_step_cap") is False, f"{label}: step cap hit")


def pair_is_finite_non_sentinel(pair: dict) -> bool:
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def frame_va(sample: dict, index: int) -> int | None:
    stack = sample.get("stack") or []
    if len(stack) <= index:
        return None
    return stack[index].get("libcp_va")


def verify_output(tier: str) -> dict:
    path = OUTPUT_DIR / f"state5_coord_output_{tier}.json"
    data = load_json(path)
    require_clean_process(data, f"output {tier}")
    require_hdr(OUTPUT_DIR / f"state5_coord_output_{tier}.hdr")

    counts = data["counts"]
    require(counts["entry_hits"] > 0, f"output {tier}: no entry hits")
    require(counts["return_ok_hits"] > 0, f"output {tier}: no normal returns")
    require(counts["feature_size_mismatch_hits"] == 0, f"output {tier}: feature mismatch")
    require(counts["total_features_size_mismatch_hits"] == 0, f"output {tier}: total mismatch")
    require(
        len(data["return_summaries"]) == counts["return_ok_hits"],
        f"output {tier}: return summary count mismatch",
    )
    for idx, summary in enumerate(data["return_summaries"]):
        vector = summary["return_output_vector"]
        require(vector["finite_non_sentinel"] > 0, f"output {tier}: empty vector {idx}")
        require(vector["pairs_truncated"] is False, f"output {tier}: truncated vector {idx}")

    samples = data["state5_store_path_samples"]
    require(samples, f"output {tier}: no store-path samples")
    require(
        all(sample["record"]["state_0x24"] == 5 for sample in samples),
        f"output {tier}: non-state-5 store sample",
    )
    targets = sorted({sample["record"]["target_0x28"] for sample in samples})
    require(targets == [OUTPUT_TARGETS[tier]], f"output {tier}: unexpected targets {targets}")
    return {
        "entry": counts["entry_hits"],
        "returns": counts["return_ok_hits"],
        "store_samples": len(samples),
        "target": targets[0],
    }


def verify_consumer(tier: str) -> dict:
    path = CONSUMER_DIR / f"coord_consumer_watch_{tier}.json"
    data = load_json(path)
    require_clean_process(data, f"consumer {tier}")
    require_hdr(CONSUMER_DIR / f"coord_consumer_watch_{tier}.hdr")

    counts = data["counts"]
    require(counts["return_ok_hits"] > 0, f"consumer {tier}: no returns")
    require(counts["feature_size_mismatch_hits"] == 0, f"consumer {tier}: feature mismatch")
    require(counts["total_features_size_mismatch_hits"] == 0, f"consumer {tier}: total mismatch")
    require(counts["watchpoints_armed"] == 3, f"consumer {tier}: watchpoint count")
    require(counts["watchpoint_hits"] > 0, f"consumer {tier}: no watchpoint hits")
    require(
        all(pair_is_finite_non_sentinel(armed["pair_at_arm"]) for armed in data["armed"]),
        f"consumer {tier}: armed non-finite/sentinel pair",
    )
    samples = data["watchpoint_samples"]
    require(samples, f"consumer {tier}: no watch samples")
    require(
        any(pair_is_finite_non_sentinel(sample["pair_now"]) for sample in samples),
        f"consumer {tier}: no finite watch sample",
    )
    require(
        all((sample.get("stack") or [{}])[0].get("function") == "___lldb_unnamed_symbol_e8e70" for sample in samples),
        f"consumer {tier}: non-e8e70 top frame",
    )
    callers = sorted({frame_va(sample, 1) for sample in samples})
    require(set(callers).issubset(CONSUMER_CALLERS), f"consumer {tier}: unexpected callers {callers}")
    require(set(callers) == CONSUMER_CALLERS, f"consumer {tier}: missing caller path {callers}")
    return {"armed": counts["watchpoints_armed"], "hits": counts["watchpoint_hits"], "callers": callers}


def verify_copy_dest(tier: str) -> dict:
    path = COPY_DEST_DIR / f"copy_dest_watch_{tier}.json"
    data = load_json(path)
    require_clean_process(data, f"copy-dest {tier}")
    require_hdr(COPY_DEST_DIR / f"copy_dest_watch_{tier}.hdr")

    counts = data["counts"]
    require(counts["copy_pairs_admitted"] > 0, f"copy-dest {tier}: no copied pairs")
    require(counts["watchpoints_armed"] == 3, f"copy-dest {tier}: watchpoint count")
    require(counts["watchpoint_hits"] > 0, f"copy-dest {tier}: no watchpoint hits")
    require(
        all(pair_is_finite_non_sentinel(armed["pair_at_arm"]) for armed in data["armed"]),
        f"copy-dest {tier}: armed non-finite/sentinel pair",
    )
    samples = data["watchpoint_samples"]
    require(
        any(pair_is_finite_non_sentinel(sample["pair_now"]) for sample in samples),
        f"copy-dest {tier}: no finite watch sample",
    )
    require(
        all((sample.get("stack") or [{}])[0].get("function") == "___lldb_unnamed_symbol_e8e70" for sample in samples),
        f"copy-dest {tier}: non-e8e70 top frame",
    )
    callers = sorted({frame_va(sample, 1) for sample in samples})
    require(set(callers).issubset(COPY_DEST_CALLERS), f"copy-dest {tier}: unexpected callers {callers}")
    require(
        any(caller in {0x22A61F, 0x22C93F} for caller in callers),
        f"copy-dest {tier}: no node-vector copy caller",
    )
    return {"admitted": counts["copy_pairs_admitted"], "hits": counts["watchpoint_hits"], "callers": callers}


def verify_node_dest(tier: str) -> dict:
    path = NODE_DEST_DIR / f"node_dest_watch_{tier}.json"
    data = load_json(path)
    require_clean_process(data, f"node-dest {tier}")
    require_hdr(NODE_DEST_DIR / f"node_dest_watch_{tier}.hdr")

    counts = data["counts"]
    require(counts["copy_pairs_admitted"] > 0, f"node-dest {tier}: no copied pairs")
    require(counts["copy_call_a_hits"] > 0, f"node-dest {tier}: missing 0x22a61a call")
    require(counts["copy_ret_a_hits"] > 0, f"node-dest {tier}: missing 0x22a61f return")
    require(counts["copy_call_b_hits"] == 0, f"node-dest {tier}: unexpected 0x22c93a call")
    require(counts["copy_ret_b_hits"] == 0, f"node-dest {tier}: unexpected 0x22c93f return")
    require(counts["watchpoints_armed"] == 3, f"node-dest {tier}: watchpoint count")
    require(counts["watchpoint_hits"] > 0, f"node-dest {tier}: no watchpoint hits")
    require(
        all(pair_is_finite_non_sentinel(armed["pair_at_arm"]) for armed in data["armed"]),
        f"node-dest {tier}: armed non-finite/sentinel pair",
    )
    samples = data["watchpoint_samples"]
    require(
        all(pair_is_finite_non_sentinel(sample["pair_now"]) for sample in samples),
        f"node-dest {tier}: non-finite/sentinel watch sample",
    )
    vas = sorted({sample["libcp_va"] for sample in samples})
    require(set(vas) == NODE_DEST_CONSUMER_VAS, f"node-dest {tier}: unexpected consumer VAs {vas}")
    require(
        all(frame_va(sample, 1) in {0x22A9E7, 0x21C59C} for sample in samples),
        f"node-dest {tier}: unexpected frame-1 stack",
    )
    return {"admitted": counts["copy_pairs_admitted"], "hits": counts["watchpoint_hits"], "consumer_vas": vas}


def hex_vas(vas: list[int]) -> str:
    return ",".join(f"0x{va:x}" for va in vas)


def main() -> None:
    for tier in TIERS:
        out = verify_output(tier)
        consumer = verify_consumer(tier)
        copy_dest = verify_copy_dest(tier)
        node_dest = verify_node_dest(tier)
        print(
            f"{tier}: OK "
            f"output(entry={out['entry']} returns={out['returns']} samples={out['store_samples']} target={out['target']}); "
            f"consumer(armed={consumer['armed']} hits={consumer['hits']} callers={hex_vas(consumer['callers'])}); "
            f"copy_dest(admitted={copy_dest['admitted']} hits={copy_dest['hits']} callers={hex_vas(copy_dest['callers'])}); "
            f"node_dest(admitted={node_dest['admitted']} hits={node_dest['hits']} consumers={hex_vas(node_dest['consumer_vas'])})"
        )


if __name__ == "__main__":
    main()
