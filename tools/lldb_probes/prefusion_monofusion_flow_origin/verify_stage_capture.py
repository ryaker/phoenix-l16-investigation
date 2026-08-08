#!/usr/bin/env python3
"""Verify one or more five-level MonoFusion intermediate-flow captures."""

import json
import sys
from pathlib import Path


def require(condition, message):
    if not condition:
        raise AssertionError(message)


EXPECTED_STAGES = [
    "initial_8x8_search_r8",
    "refine_8x8_search_r4",
    "refine_16x16_search_r8",
    "refine_16x16_search_r4",
    "overlap_16x16_search_r2",
]
EXPECTED_SIZES = [[4, 3], [16, 12], [32, 24], [130, 97], [519, 389]]


def verify(path):
    report = json.loads(path.read_text())
    require(not report["errors"], f"{path}: probe errors {report['errors']}")
    stages = report["intermediate_stages"]
    require([item["stage"] for item in stages] == EXPECTED_STAGES,
            f"{path}: unexpected stage order")
    require([item["descriptor"]["size"] for item in stages] == EXPECTED_SIZES,
            f"{path}: unexpected stage dimensions")
    for item in stages:
        flow = item["flow"]
        require(flow["read_ok"], f"{path}: unreadable {item['stage']} flow")
        require(flow["finite_pairs"] == flow["pair_count"],
                f"{path}: non-finite {item['stage']} flow")
        print(
            f"stage={item['stage']} size={item['descriptor']['size']} "
            f"sha256={flow['sha256']} sentinel={flow['invalid_sentinel_pairs']}"
        )
    require(report["terminated_after_samples"], f"{path}: capture did not terminate deliberately")


def main():
    require(len(sys.argv) > 1, "provide at least one stage report")
    for arg in sys.argv[1:]:
        verify(Path(arg))


if __name__ == "__main__":
    main()
