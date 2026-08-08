#!/usr/bin/env python3
"""Pin the external implementation snapshot used by the repair audit."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


FILES = {
    "phoenix_arm/tools/phoenix_depth.cpp": (
        "fcc9e114e504c978d2984f5095b050b398c3cc5d53ac592929ced8d2b95ce799",
        (
            "bool g_contigPatch = false;",
            "static const int kWgt[4] = {8160, 680, 680, 0};",
            "if (std::getenv(\"PHX_SGM8\"))",
            "if (lvl == 0 && idxlo < 0 && !std::getenv(\"PHX_NOCONF\"))",
        ),
    ),
    "phoenix_arm/tools/phoenix_fuse.cpp": (
        "689cb9f17fc39956e32ec329c58dd73df85985ac45c450fb8e311723a0ef0c2d",
        (
            "const bool use_flow = !std::getenv(\"PHX_NOFLOW\");",
            "in.accept_min_ncc = 0.75f;",
            "const bool use_sr = !std::getenv(\"PHX_NOSR\") && use_flow;",
            "if (!std::getenv(\"PHX_NOCHROMA\"))",
            "bool want_tiff = false, no_cnr = false, no_look = true",
        ),
    ),
    "phoenix_arm/engine/depth/cost_sgm.cpp": (
        "4507a875e2ce0fd4f0c3f572b8d060c9b6bdf31d2895bcde7398b76afb8ab3ff",
        (
            "SPEC-GAP G-43: 4-path direction set",
            "aggregatePath(local, guide, params, 0, -1, accum);",
        ),
    ),
    "phoenix_arm/engine/merge/iramp.cpp": (
        "45d8a2e4cf10b4b25e6f56af0303e1f325de734ba30ac04e30f4fbdb185dc574",
        (
            "if (in.accept_min_ncc > 0.0f)",
            "flow_conf",
        ),
    ),
    "phoenix_arm/engine/edit/phoenix_project.cpp": (
        "f467efe25acad9fdc0f38ec769bdb9bc3c3bc46bb44cfe12f7720e8e0f30dc81",
        (
            "float ccm_alpha = 0.245f;",
            "neutral-adapt (von-Kries to as-shot neutral)",
        ),
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path("/Users/ryaker/L16_Phoenix")
    )
    args = parser.parse_args()

    for relative, (expected_digest, markers) in FILES.items():
        path = args.root / relative
        require(path.is_file(), f"missing external source {path}")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(digest == expected_digest,
                f"external source changed: {relative} {digest}")
        text = data.decode("utf-8")
        for marker in markers:
            require(marker in text, f"missing marker in {relative}: {marker}")
        print(f"{relative}: sha256={digest} markers={len(markers)}")

    print(f"implementation_repair_snapshot=OK files={len(FILES)}")


if __name__ == "__main__":
    main()
