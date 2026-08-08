#!/usr/bin/env python3
"""Verify the Lane A node-coordinate sentinel proof packets.

This checker validates the repo-local JSON/HDR artifacts for:

- sentinel coordinate writes at 0x21b923 / 0x21b92a;
- downstream touches of completed (-1.0, -1.0) node-vector pairs.

It verifies custody/invalidation facts only. It does not prove image effect,
source contribution, public State semantics, reducer closure, or final
acceptance/rejection policy.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TIERS = ("28mm", "35mm", "70mm", "150mm")

WRITE_DIR = ROOT / "runs/prefusion_node_sentinel_write"
DOWNSTREAM_DIR = ROOT / "runs/prefusion_node_sentinel_downstream_watch"

SENTINEL_BITS = 0xBF800000
STORE_X_VA = 0x21B923
STORE_Y_VA = 0x21B92A
AFTER_STORE_VA = 0x21B930

EXPECTED_DOWNSTREAM_VAS = {
    "28mm": {0xE0BB2, 0xE0BB7, 0xE0BBD, 0xE0BC3, 0x20B912},
    "35mm": {0xE0BBD, 0xE0BC3, 0xE0BD5, 0xE0BDB, 0x20B912},
    "70mm": {
        0xE0BB2,
        0xE0BB7,
        0xE0BBD,
        0xE0BC3,
        0xE0BD5,
        0xE0BDB,
        0x20B912,
        0x217035,
        0x21703A,
        0x217048,
        0x21704F,
        0x217064,
        0x21706A,
        0x218BC4,
    },
    "150mm": {
        0xE0BB2,
        0xE0BB7,
        0xE0BD5,
        0xE0BDB,
        0x20B912,
        0x21704F,
        0x21706A,
        0x2170B7,
        0x2170BD,
        0x218BC4,
    },
}
SCAN_COUNT_VAS = {
    0x217035,
    0x21703A,
    0x217048,
    0x21704F,
    0x217064,
    0x21706A,
    0x2170B7,
    0x2170BD,
}
EXPECTED_SCAN_COUNT_SAMPLES = {
    "28mm": 0,
    "35mm": 0,
    "70mm": 6,
    "150mm": 4,
}


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


def is_full_sentinel(pair: dict) -> bool:
    return (
        pair.get("is_sentinel_neg1_neg1") is True
        and pair.get("x_bits") == SENTINEL_BITS
        and pair.get("y_bits") == SENTINEL_BITS
    )


def is_finite_not_full_sentinel(pair: dict) -> bool:
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def frame_va(sample: dict, index: int) -> int | None:
    stack = sample.get("stack") or []
    if len(stack) <= index:
        return None
    return stack[index].get("libcp_va")


def verify_write(tier: str) -> dict:
    path = WRITE_DIR / f"node_sentinel_write_{tier}.json"
    data = load_json(path)
    require_clean_process(data, f"write {tier}")
    require_hdr(WRITE_DIR / f"node_sentinel_write_{tier}.hdr")

    counts = data["counts"]
    require(counts["store_x_hits"] > 0, f"write {tier}: no x-store hits")
    require(counts["store_y_hits"] > 0, f"write {tier}: no y-store hits")
    require(
        counts["store_x_pre_finite_non_sentinel"] == counts["store_x_hits"],
        f"write {tier}: x pre-store finite count mismatch",
    )
    require(
        counts["store_y_mid_x_is_sentinel"] == counts["store_y_hits"],
        f"write {tier}: y mid-store x-sentinel count mismatch",
    )
    require(data["store_x_samples"], f"write {tier}: no x-store samples")
    require(data["store_y_samples"], f"write {tier}: no y-store samples")

    for sample in data["store_x_samples"]:
        require(sample["pc_va"] == STORE_X_VA, f"write {tier}: wrong x-store pc")
        require(sample["static_store_bits"] == SENTINEL_BITS, f"write {tier}: wrong x-store bits")
        require(sample["static_store_float"] == -1.0, f"write {tier}: wrong x-store float")
        require(is_finite_not_full_sentinel(sample["pair_before_store"]), f"write {tier}: bad x pre-pair")
        require(frame_va(sample, 0) == STORE_X_VA, f"write {tier}: wrong x top frame")

    for sample in data["store_y_samples"]:
        pair = sample["pair_mid_store"]
        require(sample["pc_va"] == STORE_Y_VA, f"write {tier}: wrong y-store pc")
        require(sample["static_store_bits"] == SENTINEL_BITS, f"write {tier}: wrong y-store bits")
        require(sample["static_store_float"] == -1.0, f"write {tier}: wrong y-store float")
        require(pair.get("x_bits") == SENTINEL_BITS, f"write {tier}: x not sentinel before y-store")
        require(pair.get("y_bits") != SENTINEL_BITS, f"write {tier}: y already sentinel before y-store")
        require(frame_va(sample, 0) == STORE_Y_VA, f"write {tier}: wrong y top frame")

    return {
        "x_hits": counts["store_x_hits"],
        "y_hits": counts["store_y_hits"],
        "sampled_x": len(data["store_x_samples"]),
        "sampled_y": len(data["store_y_samples"]),
    }


def verify_downstream(tier: str) -> dict:
    path = DOWNSTREAM_DIR / f"node_sentinel_downstream_{tier}.json"
    data = load_json(path)
    require_clean_process(data, f"downstream {tier}")
    require_hdr(DOWNSTREAM_DIR / f"node_sentinel_downstream_{tier}.hdr")

    counts = data["counts"]
    require(counts["store_y_hits"] >= counts["watchpoints_armed"], f"downstream {tier}: store/arm mismatch")
    require(
        counts["after_store_pair_is_sentinel"] >= counts["watchpoints_armed"],
        f"downstream {tier}: after-store sentinel count mismatch",
    )
    require(counts["watchpoints_armed"] == 3, f"downstream {tier}: watchpoints armed != 3")
    require(counts["watchpoint_hits"] > 0, f"downstream {tier}: no watchpoint hits")
    require(data["armed"], f"downstream {tier}: no armed records")
    require(data["watchpoint_samples"], f"downstream {tier}: no watchpoint samples")

    for sample in data["store_y_samples"]:
        pair = sample["pair_before_y_store"]
        require(sample["pc_va"] == STORE_Y_VA, f"downstream {tier}: wrong y-store pc")
        require(pair.get("x_bits") == SENTINEL_BITS, f"downstream {tier}: x not sentinel before y-store")
        require(pair.get("y_bits") != SENTINEL_BITS, f"downstream {tier}: y already sentinel before y-store")
        require(frame_va(sample, 0) == STORE_Y_VA, f"downstream {tier}: wrong y top frame")

    for armed in data["armed"]:
        require(is_full_sentinel(armed["pair_at_arm"]), f"downstream {tier}: armed pair not full sentinel")
        require(armed["watch_size"] == 8, f"downstream {tier}: watch size")
        require(armed["watchpoint_error"] is None, f"downstream {tier}: watchpoint error")
        stack = armed.get("after_store_stack") or []
        require(stack and stack[0].get("libcp_va") == AFTER_STORE_VA, f"downstream {tier}: wrong after-store frame")

    vas = sorted({sample["libcp_va"] for sample in data["watchpoint_samples"]})
    require(set(vas) == EXPECTED_DOWNSTREAM_VAS[tier], f"downstream {tier}: unexpected VAs {vas}")
    scan_count_samples = [sample for sample in data["watchpoint_samples"] if sample["libcp_va"] in SCAN_COUNT_VAS]
    require(
        len(scan_count_samples) == EXPECTED_SCAN_COUNT_SAMPLES[tier],
        f"downstream {tier}: scan/count sample count {len(scan_count_samples)}",
    )
    for sample in data["watchpoint_samples"]:
        require(is_full_sentinel(sample["pair_now"]), f"downstream {tier}: sampled touch changed sentinel")

    return {
        "armed": counts["watchpoints_armed"],
        "hits": counts["watchpoint_hits"],
        "sampled": len(data["watchpoint_samples"]),
        "scan_count_samples": len(scan_count_samples),
        "vas": vas,
    }


def hex_vas(vas: list[int]) -> str:
    return ",".join(f"0x{va:x}" for va in vas)


def main() -> None:
    for tier in TIERS:
        write = verify_write(tier)
        downstream = verify_downstream(tier)
        cap = " capped" if write["x_hits"] >= 512 or write["y_hits"] >= 512 else ""
        print(
            f"{tier}: OK "
            f"write(x={write['x_hits']} y={write['y_hits']} samples={write['sampled_x']}/{write['sampled_y']}{cap}); "
            f"downstream(armed={downstream['armed']} hits={downstream['hits']} "
            f"samples={downstream['sampled']} scan_count={downstream['scan_count_samples']} "
            f"vas={hex_vas(downstream['vas'])})"
        )


if __name__ == "__main__":
    main()
