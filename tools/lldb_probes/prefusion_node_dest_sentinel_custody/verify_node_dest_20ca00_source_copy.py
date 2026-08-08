#!/usr/bin/env python3
"""Verify copied node-destination sentinel custody into the 0x20ca00 second copy."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_node_dest_sentinel_custody"
TIERS = ("28mm", "35mm", "70mm", "150mm")

COPY_RET_A = 0x22A61F
COPY_RET_B = 0x22C93F
SECOND_20CA00_COPY_RETURN = 0x20D309
E0AE0_SOURCE_READ_SITES = {
    0xE0B80,
    0xE0B82,
    0xE0B84,
    0xE0B87,
    0xE0BB0,
    0xE0BB2,
    0xE0BB4,
    0xE0BB7,
    0xE0BBA,
    0xE0BBD,
    0xE0BC0,
    0xE0BC3,
    0xE0BC6,
    0xE0BC9,
    0xE0BCC,
    0xE0BCF,
    0xE0BD2,
    0xE0BD5,
    0xE0BD8,
    0xE0BDB,
}
SENTINEL_HEX = "000080bf000080bf"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_clean(report: dict, tier: str) -> None:
    require(report.get("process_exit_status") == 0, f"{tier}: nonzero exit")
    require(report.get("drive_hit_step_cap") is False, f"{tier}: step cap hit")
    require(report.get("errors") == [], f"{tier}: probe errors present {report.get('errors')}")


def is_finite_non_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("both_finite")) and not bool(pair.get("is_sentinel_neg1_neg1"))


def is_full_sentinel(pair: dict | None) -> bool:
    if not pair:
        return False
    return bool(pair.get("is_sentinel_neg1_neg1")) and pair.get("hex") == SENTINEL_HEX


def verify_match(tier: str, match: dict) -> int:
    pair_addr = match.get("pair_addr")
    require(pair_addr, f"{tier}: missing matched pair address")

    copied = match.get("copied_pair") or {}
    copied_pair = copied.get("pair_at_copy") or {}
    require(copied_pair.get("addr") == pair_addr, f"{tier}: copied pair address mismatch")
    require(is_finite_non_sentinel(copied_pair), f"{tier}: copied pair is not finite/non-sentinel")

    copy_event = match.get("copy_event") or {}
    require(copy_event.get("copy_site") in {"copy_a_ret_22a61f", "copy_b_ret_22c93f"}, f"{tier}: unexpected copy site")
    stack_vas = [frame.get("libcp_va") for frame in copy_event.get("copy_return_stack") or []]
    require(COPY_RET_A in stack_vas or COPY_RET_B in stack_vas, f"{tier}: copy return stack missing node-vector site")

    after = match.get("pair_after_y_store") or {}
    require(after.get("addr") == pair_addr, f"{tier}: after-store address mismatch")
    require(is_full_sentinel(after), f"{tier}: after-store pair is not full sentinel")
    return pair_addr


def is_20ca00_second_copy_sample(sample: dict, pair_addr: int) -> bool:
    pair = sample.get("pair_now") or {}
    stack = sample.get("stack") or []
    return (
        sample.get("libcp_va") in E0AE0_SOURCE_READ_SITES
        and len(stack) > 1
        and stack[1].get("libcp_va") == SECOND_20CA00_COPY_RETURN
        and pair.get("addr") == pair_addr
        and is_full_sentinel(pair)
    )


def verify_tier(tier: str) -> dict:
    report = load_json(RUN / f"node_dest_sentinel_custody_{tier}.json")
    require_clean(report, tier)

    matches = report.get("matches") or []
    require(matches, f"{tier}: no same-address node-destination matches")
    pair_addr = verify_match(tier, matches[0])

    copy_samples = [
        sample
        for sample in report.get("watchpoint_samples") or []
        if is_20ca00_second_copy_sample(sample, pair_addr)
    ]
    require(copy_samples, f"{tier}: no same-address 0x20d309 second-copy source reads")

    unique_pcs = sorted({sample.get("libcp_va") for sample in copy_samples})
    parent_stacks = sorted({sample["stack"][1]["libcp_va"] for sample in copy_samples})
    require(parent_stacks == [SECOND_20CA00_COPY_RETURN], f"{tier}: unexpected parent stacks {parent_stacks}")

    return {
        "pair_addr": pair_addr,
        "samples": len(copy_samples),
        "pcs": ",".join(f"0x{pc:x}" for pc in unique_pcs),
        "copied_hex": (matches[0].get("copied_pair") or {}).get("pair_at_copy", {}).get("hex"),
    }


def main() -> None:
    for tier in TIERS:
        row = verify_tier(tier)
        print(
            f"{tier}: OK same_addr={row['pair_addr']} "
            f"copy20d309_source_reads={row['samples']} e0ae0_pcs={row['pcs']} "
            f"copied_hex={row['copied_hex']}"
        )


if __name__ == "__main__":
    main()
