#!/usr/bin/env python3
"""Join the admitted CalibStage transfer slices to public calibration names."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VERIFIERS = (
    (
        ROOT / "tools/lldb_probes/calibstage_public_names/verify_calibstage_public_names.py",
        "calibstage_public_names=OK",
    ),
    (
        ROOT
        / "tools/lldb_probes/index5_composed_geometry_origin"
        / "verify_composed_geometry_origin.py",
        "cross_body_28mm=OK",
    ),
    (
        ROOT
        / "tools/lldb_probes/prefusion_wide_minimum_selector"
        / "verify_wide_minimum_selector.py",
        "wide_minimum_selector=OK",
    ),
)


def main() -> None:
    outputs = []
    for path, marker in VERIFIERS:
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        if marker not in result.stdout:
            raise AssertionError(f"{path}: missing success marker {marker!r}")
        outputs.append(result.stdout.strip())

    print("\n".join(outputs))
    print(
        "calibstage_slice_public_names=OK "
        "node+0x30..+0x53=intrinsics.k_mat "
        "node+0x60..+0x83=extrinsics.canonical.rotation "
        "node+0x54..+0x5f=extrinsics.canonical.translation "
        "boundary=derived_composed_values"
    )


if __name__ == "__main__":
    main()
