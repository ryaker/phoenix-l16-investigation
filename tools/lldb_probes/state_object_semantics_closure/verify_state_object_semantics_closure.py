#!/usr/bin/env python3
"""Aggregate the independent proofs that close live State/object semantics."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CHECKS = (
    ("calibdataprocessor_public_identity", "tools/lldb_probes/calibdataprocessor_public_identity/verify_calibdataprocessor_public_identity.py", "150mm: OK calls=38 bodies=13"),
    ("state_rawimagefactory_identity", "tools/lldb_probes/state_e0_rawimagefactory_identity/verify_state_e0_rawimagefactory_identity.py", "state_e0_rawimagefactory_identity=OK"),
    ("capturedimage_public_fields", "tools/lldb_probes/capturedimage_f2770_origin/verify_public_capture_fields.py", "capturedimage_public_capture_fields=OK"),
    ("capturedimage_frame_index", "tools/lldb_probes/capturedimage_frame_index_origin/verify_frame_index_public_origin.py", "capturedimage_frame_index_public_origin=OK"),
    ("calibstage_slices", "tools/lldb_probes/calibstage_slice_public_names/verify_calibstage_slice_public_names.py", "calibstage_slice_public_names=OK"),
    ("composed_geometry", "tools/lldb_probes/index5_composed_geometry_origin/verify_composed_geometry_origin.py", "cross_body_28mm=OK"),
    ("postterminal_state_feed", "tools/lldb_probes/prefusion_postterminal_calib_finalize/verify_postterminal_four_zoom.py", "postterminal_four_zoom=OK"),
    ("guidance_components", "tools/lldb_probes/index5_guidance_channel_origin/verify_guidance_collapse2_semantics.py", "guidance_collapse2_semantics=OK"),
    ("guidance_yuv", "tools/lldb_probes/index5_guidance_channel_origin/verify_create_stereo_yuv.py", "create_stereo_yuv=OK"),
    ("sgm_roles", "tools/lldb_probes/index5_sgm_recurrence_roles/verify_sgm_recurrence_roles.py", "index5_sgm_recurrence_roles=OK"),
    ("iramp_operand_roles", "tools/lldb_probes/iramp_operand_role_custody/verify_iramp_operand_roles.py", "iramp_operand_roles=OK"),
    ("iramp_candidate_policy", "tools/lldb_probes/iramp_candidate_policy/verify_iramp_candidate_policy.py", "iramp_candidate_policy=OK"),
    ("iramp_reconstruction", "tools/lldb_probes/iramp_accumulator_reconstruction/verify_accumulator_reconstruction.py", "iramp_accumulator_reconstruction=OK"),
    ("reference_validation", "tools/lldb_probes/reference_undistorted_planes/verify_reference_validation_artifacts.py", "reference_validation_artifacts=OK"),
)


def main() -> None:
    for label, relative, marker in CHECKS:
        result = subprocess.run(
            [sys.executable, str(ROOT / relative)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"{label}: verifier failed ({result.returncode})\n{result.stdout}\n{result.stderr}"
            )
        output = result.stdout + result.stderr
        if marker not in output:
            raise AssertionError(f"{label}: missing marker {marker!r}\n{output}")
        print(f"state_closure_check={label}:OK")
    print(f"state_closure_checks={len(CHECKS)}")
    print("state_object_semantics_closure=OK")


if __name__ == "__main__":
    main()
