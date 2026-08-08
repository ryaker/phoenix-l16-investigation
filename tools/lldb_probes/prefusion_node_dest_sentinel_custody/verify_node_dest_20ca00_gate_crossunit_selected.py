#!/usr/bin/env python3
"""Verify selected Unit-1/Unit-2 node-destination gate observations."""

from __future__ import annotations

from pathlib import Path

import verify_node_dest_20ca00_gate_selected_custody as base


ROOT = Path(__file__).resolve().parents[3]
U1_GENERIC = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_custody"
U1_TARGET = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_target_custody"
U2_GENERIC = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_custody_unit2"
U2_TARGET = ROOT / "runs" / "prefusion_node_dest_20ca00_gate_target_custody_unit2"


def load_clean(json_path: Path, hdr_path: Path, label: str) -> dict:
    report = base.load(json_path)
    base.require_clean(report, label)
    base.require_hdr(hdr_path)
    return report


def main() -> None:
    u1_28 = load_clean(
        U1_TARGET / "node_dest_20ca00_gate_target_28mm.json",
        U1_TARGET / "node_dest_20ca00_gate_target_28mm.hdr",
        "Unit-1 28mm",
    )
    u1_35 = load_clean(
        U1_GENERIC / "node_dest_20ca00_gate_35mm.json",
        U1_GENERIC / "node_dest_20ca00_gate_35mm.hdr",
        "Unit-1 35mm",
    )
    u1_70 = load_clean(
        U1_GENERIC / "node_dest_20ca00_gate_70mm.json",
        U1_GENERIC / "node_dest_20ca00_gate_70mm.hdr",
        "Unit-1 70mm",
    )
    u2_28 = load_clean(
        U2_GENERIC / "node_dest_20ca00_gate_unit2_28mm.json",
        U2_GENERIC / "node_dest_20ca00_gate_unit2_28mm.hdr",
        "Unit-2 28mm",
    )
    u2_35 = load_clean(
        U2_GENERIC / "node_dest_20ca00_gate_unit2_35mm.json",
        U2_GENERIC / "node_dest_20ca00_gate_unit2_35mm.hdr",
        "Unit-2 35mm generic",
    )
    u2_35_repeat = load_clean(
        U2_TARGET / "node_dest_20ca00_gate_unit2_target_35mm.json",
        U2_TARGET / "node_dest_20ca00_gate_unit2_target_35mm.hdr",
        "Unit-2 35mm targeted repeat",
    )
    u2_70 = load_clean(
        U2_GENERIC / "node_dest_20ca00_gate_unit2_70mm.json",
        U2_GENERIC / "node_dest_20ca00_gate_unit2_70mm.hdr",
        "Unit-2 70mm",
    )

    row_u1_28 = base.validate_positive(u1_28, "Unit-1 28mm", 5394, "0040ea4400007a44")
    row_u1_35 = base.validate_negative(u1_35, "Unit-1 35mm", {278, 300, 2938, 3165}, 1, True)
    row_u1_70 = base.validate_positive(u1_70, "Unit-1 70mm", 77, "0020a74400007042")
    row_u2_28 = base.validate_negative(u2_28, "Unit-2 28mm", {607, 768, 896, 933}, 1, True)
    row_u2_35 = base.validate_positive(u2_35, "Unit-2 35mm generic", 12, "0000b94300006143")
    row_u2_35_repeat = base.validate_negative(
        u2_35_repeat,
        "Unit-2 35mm targeted repeat",
        {11, 12, 13, 14},
        1,
        True,
    )
    row_u2_70 = base.validate_negative(u2_70, "Unit-2 70mm", {3149, 5737, 5797, 6310}, 1, True)

    print(
        "Unit-1: OK "
        f"28mm=index5394/gate, 35mm=no-match/{row_u1_35['source_hits']}/cap, "
        "70mm=index77/gate"
    )
    print(
        "Unit-2: OK "
        f"28mm=no-match/{row_u2_28['source_hits']}/cap, 35mm=index12/gate, "
        f"70mm=no-match/{row_u2_70['source_hits']}/cap"
    )
    print(
        "Unit-2 35mm targeted repeat: OK "
        f"indices=11,12,13,14 no-match/{row_u2_35_repeat['source_hits']}/cap"
    )
    print(
        "cross-unit mechanism: OK "
        f"positive_same_address_counts={row_u1_28['same_address_matches']},"
        f"{row_u1_70['same_address_matches']},{row_u2_35['same_address_matches']}"
    )


if __name__ == "__main__":
    main()
