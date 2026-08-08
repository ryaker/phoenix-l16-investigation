#!/usr/bin/env python3
"""Verify the scoped checklist and current canonical blocker accounting."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs/TRUTH.md"
LEDGER = ROOT / "docs/canonical/CLAIM_LEDGER.md"
HANDOFF = ROOT / "docs/canonical/FINAL_TRUTH_SPEC_HANDOFF.md"
WSJF = ROOT / "docs/canonical/WSJF_PRIORITY.md"
PARITY = ROOT / "docs/canonical/PARITY_BLOCKERS.md"

EVIDENCE = (
    "bundle_static_runtime_final_stage_constants_four_zoom.md",
    "bundle_static_runtime_calibstage_slice_public_names.md",
    "bundle_static_runtime_index5_cost_operand_names_four_zoom.md",
    "bundle_static_runtime_ccm_illuminant_selection_four_zoom.md",
    "bundle_static_runtime_calibdataprocessor_public_identity_four_zoom.md",
    "bundle_static_runtime_prefusion_postterminal_state_to_pipelinecache_four_zoom.md",
    "bundle_static_runtime_index5_sgm_parameter_origins_four_zoom.md",
    "bundle_static_runtime_row_image_public_policy_four_zoom.md",
    "bundle_static_runtime_c6_terminal_filter_differential_tele.md",
    "bundle_static_runtime_prefusion_wide_218bc4_path_divergence.md",
    "lldb_unit2_capturedimage_constructor_runtime_join.md",
    "bundle_static_runtime_laplacian_clarity_kernel_28mm.md",
    "lldb_final_iramp_score_image_effect_wide_tele.md",
    "bundle_static_runtime_prefusion_monofusion_mode_selector_profiles.md",
    "bundle_static_runtime_prefusion_parent_identity_closure_four_zoom.md",
    "bundle_static_runtime_tele_firing_topology_two_body.md",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def claim_row(ledger: str, claim_id: str) -> str:
    match = re.search(
        rf"^\| `{re.escape(claim_id)}` \|.*$", ledger, flags=re.MULTILINE
    )
    require(match is not None, f"missing ledger row {claim_id}")
    return match.group(0)


def main() -> None:
    truth = TRUTH.read_text()
    ledger = LEDGER.read_text()
    handoff = HANDOFF.read_text()
    wsjf = WSJF.read_text()
    parity = PARITY.read_text()

    version_match = re.search(r"\*\*Version\*\*: 3\.0\.(\d+)", truth)
    require(version_match is not None, "missing TRUTH 3.0.x version")
    require(int(version_match.group(1)) >= 254, "TRUTH predates ledger reconciliation")

    for item in ("A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4",
                 "C1", "C2", "C3", "C4", "C5", "D1", "E1"):
        require(f"| {item} |" in truth, f"missing TRUTH checklist row {item}")

    for marker in (
        "(-1/192,-1/96,-1/48,-1/24)",
        "0x7fffffff",
        "P1=1",
        "P2/P1=500",
        "Vec3<Float16>",
        "CLM-C6-001",
        "8049-sample transfer",
    ):
        require(marker in truth, f"missing TRUTH marker {marker}")

    for claim_id in (
        "CLM-WARP-003",
        "CLM-SHARPEN-001",
        "CLM-SHARPEN-002",
        "CLM-DENOISE-001",
        "CLM-RESAMPLE-001",
        "CLM-WARP-004",
        "CLM-CCM-002",
        "CLM-C6-001",
    ):
        row = claim_row(ledger, claim_id)
        require("| `PROVEN` | `SPEC_READY` |" in row, f"{claim_id} not admitted")

    for claim_id in (
        "CLM-PREFUSION-001",
        "CLM-PREFUSION-002",
        "CLM-MERGE-005",
        "CLM-MERGE-006",
        "CLM-ZOOM-002",
    ):
        require(
            "| `PROVEN` | `SPEC_READY` |" in claim_row(ledger, claim_id),
            f"{claim_id} not admitted",
        )

    blocker_rows = []
    for row in re.findall(r"^\| `CLM-[^|]+?\|.*$", ledger, flags=re.MULTILINE):
        if "| `BLOCKER` |" in row:
            blocker_rows.append(row.split("|", 2)[1].strip())
    if not blocker_rows:
        require("| - | None |" in parity, "zero-blocker parity table missing")
        require(
            "No canonical profile-3 blocker remains" in wsjf,
            "zero-blocker WSJF statement missing",
        )
    require(
        "Scoped Checklist Handoff (Not Final)" in handoff,
        "scoped checklist handoff lost its non-final scope guard",
    )

    evidence_root = ROOT / "docs/evidence"
    for filename in EVIDENCE:
        require((evidence_root / filename).is_file(), f"missing evidence {filename}")
        require(filename in handoff, f"handoff omits {filename}")

    current_wsjf = wsjf.split("## Historical Raw WSJF Table", 1)[0]
    require(
        "`CLM-DEMOSAIC-002` is removed from the ranking" in current_wsjf,
        "WSJF demosaic closure missing",
    )
    require("CLM-INPUT-001" in current_wsjf, "WSJF raw-input closure missing")
    require(
        "`CLM-RESAMPLE-001` is removed at TRUTH `3.0.258`" in current_wsjf,
        "WSJF resampler closure missing",
    )
    require(
        "`CLM-WARP-004` is removed at TRUTH `3.0.259`" in current_wsjf,
        "WSJF distortion closure missing",
    )
    require(
        re.search(r"## Current Status \(TRUTH 3\.0\.\d+\)", parity) is not None,
        "current parity status heading missing",
    )
    require(
        "This scoped checklist is complete." in truth,
        "TRUTH scoped-checklist statement missing",
    )
    print(
        "scoped_checklist_verification=OK "
        f"version=3.0.{version_match.group(1)} items=16 evidence={len(EVIDENCE)} "
        f"active_full_cleanroom_blockers={len(blocker_rows)}"
    )


if __name__ == "__main__":
    main()
