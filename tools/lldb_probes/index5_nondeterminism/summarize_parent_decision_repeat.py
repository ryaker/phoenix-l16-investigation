#!/usr/bin/env python3
"""Summarize repeated Unit-2 70mm 0x216f60 decision packets by camera key."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "index5_nondeterminism"


def reason(packet: dict) -> str:
    for branch in packet["branches"]:
        if branch["taken"]:
            return branch["name"]
    return "accepted"


def main() -> None:
    for stem in ("u2_70_parent_r1", "u2_70_parent_r2"):
        report = json.loads((RUN / stem / "parent_decision.json").read_text())
        print(stem)
        for packet in report["packets"]:
            print(
                "  ordinal={ordinal} camera={camera} count={count} winner={winner} "
                "winner_score={score:.9g} winner_side={side:.9g} "
                "center_score={center:.9g} center_side={center_side:.9g} "
                "ratio={ratio:.9g} outcome={outcome}".format(
                    ordinal=packet["ordinal"],
                    camera=packet["camera_id"],
                    count=packet["return_vector"]["count"],
                    winner=packet["winner"]["index"],
                    score=packet["winner"]["score"]["value"],
                    side=packet["winner_side"]["value"],
                    center=packet["center_score"]["value"],
                    center_side=packet["center_side"]["value"],
                    ratio=packet["center_score_times_0_8_f32"],
                    outcome=reason(packet),
                )
            )


if __name__ == "__main__":
    main()
