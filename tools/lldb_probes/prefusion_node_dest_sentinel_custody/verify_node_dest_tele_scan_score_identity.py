#!/usr/bin/env python3
"""Verify same-address tele node-destination custody into scan/score windows."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_node_dest_sentinel_custody"
TIERS = ("70mm", "150mm")

SENTINEL_HEX = "000080bf000080bf"
AFTER_SENTINEL_Y_STORE = 0x21B930
SCAN_COUNT_PCS = {
    "70mm": {0x217048, 0x217064},
    "150mm": {0x217035, 0x21703A},
}
SCORE_GUARD_PC = 0x218BC4
SCAN_BODY = 0x216F60
SCORE_BODY = 0x218B30
SCORE_CALLER_START = 0x218E20
SCORE_CALLER_END = 0x218F90


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


def stack_vas(packet: dict) -> list[int]:
    return [
        frame["libcp_va"]
        for frame in packet.get("stack", [])
        if frame.get("libcp_va") is not None
    ]


def verify_match(tier: str, report: dict) -> tuple[int, str, int]:
    counts = report["counts"]
    require(counts.get("sentinel_matches") == 1, f"{tier}: expected one same-address match")
    require(counts.get("watchpoints_armed") == 1, f"{tier}: expected one watchpoint")
    require(counts.get("watchpoints_disabled_after_cap") == 1, f"{tier}: expected watch cap marker")

    matches = report.get("matches") or []
    require(len(matches) == 1, f"{tier}: match count mismatch")
    match = matches[0]

    pair_addr = match.get("pair_addr")
    require(pair_addr, f"{tier}: missing match address")

    copied = ((match.get("copied_pair") or {}).get("pair_at_copy") or {})
    require(copied.get("addr") == pair_addr, f"{tier}: copied address mismatch")
    require(is_finite_non_sentinel(copied), f"{tier}: copied pair not finite/non-sentinel")

    after = match.get("pair_after_y_store") or {}
    require(after.get("addr") == pair_addr, f"{tier}: after-store address mismatch")
    require(is_full_sentinel(after), f"{tier}: after-store pair not full sentinel")
    require(
        any(frame.get("libcp_va") == AFTER_SENTINEL_Y_STORE for frame in match.get("after_store_stack", [])),
        f"{tier}: missing 0x21b930 after-store stack frame",
    )

    return pair_addr, copied["hex"], (match.get("copied_pair") or {}).get("pair_index")


def require_watch_sample(tier: str, sample: dict, pair_addr: int, index: int) -> None:
    pair = sample.get("pair_now") or {}
    require(pair.get("addr") == pair_addr, f"{tier}: watch sample {index} address mismatch")
    require(is_full_sentinel(pair), f"{tier}: watch sample {index} not full sentinel")


def verify_scan_samples(tier: str, samples: list[dict], pair_addr: int) -> list[int]:
    pcs = SCAN_COUNT_PCS[tier]
    selected = [sample for sample in samples if sample.get("libcp_va") in pcs]
    require(len(selected) == len(pcs), f"{tier}: expected scan/count stops at {sorted(hex(pc) for pc in pcs)}")

    seen = {sample.get("libcp_va") for sample in selected}
    require(seen == pcs, f"{tier}: scan/count pc set mismatch {sorted(hex(pc) for pc in seen)}")
    for index, sample in enumerate(selected, 1):
        require_watch_sample(tier, sample, pair_addr, index)
        vas = stack_vas(sample)
        require(vas and vas[0] in pcs, f"{tier}: scan sample {index} top frame mismatch")
        require(any(0x216F60 <= va < 0x217110 for va in vas), f"{tier}: scan sample {index} missing 0x216f60 body")

    return sorted(seen)


def verify_score_samples(tier: str, samples: list[dict], pair_addr: int) -> int:
    selected = [sample for sample in samples if sample.get("libcp_va") == SCORE_GUARD_PC]
    require(selected, f"{tier}: no 0x218bc4 score-guard samples")

    for index, sample in enumerate(selected, 1):
        require_watch_sample(tier, sample, pair_addr, index)
        vas = stack_vas(sample)
        require(vas and vas[0] == SCORE_GUARD_PC, f"{tier}: score sample {index} top frame mismatch")
        require(any(0x218B30 <= va < 0x218F90 for va in vas), f"{tier}: score sample {index} missing 0x218b30 body")
        require(
            any(SCORE_CALLER_START <= va < SCORE_CALLER_END for va in vas[1:]),
            f"{tier}: score sample {index} missing 0x218e20 caller body",
        )

    return len(selected)


def verify_tier(tier: str) -> dict:
    report = load_json(RUN / f"node_dest_sentinel_custody_{tier}.json")
    require_clean(report, tier)
    require_hdr(RUN / f"node_dest_sentinel_custody_{tier}.hdr")

    pair_addr, copied_hex, pair_index = verify_match(tier, report)
    samples = report.get("watchpoint_samples") or []
    require(samples, f"{tier}: no watchpoint samples")
    for index, sample in enumerate(samples, 1):
        require_watch_sample(tier, sample, pair_addr, index)

    scan_pcs = verify_scan_samples(tier, samples, pair_addr)
    score_hits = verify_score_samples(tier, samples, pair_addr)

    return {
        "pair_addr": pair_addr,
        "pair_index": pair_index,
        "copied_hex": copied_hex,
        "scan_pcs": ",".join(hex(pc) for pc in scan_pcs),
        "score_hits": score_hits,
        "watch_hits": len(samples),
    }


def main() -> None:
    for tier in TIERS:
        row = verify_tier(tier)
        print(
            f"{tier}: OK same_addr={row['pair_addr']} pair_index={row['pair_index']} "
            f"copied_hex={row['copied_hex']} scan_pcs={row['scan_pcs']} "
            f"score_guard_hits={row['score_hits']} watch_hits={row['watch_hits']}"
        )


if __name__ == "__main__":
    main()
