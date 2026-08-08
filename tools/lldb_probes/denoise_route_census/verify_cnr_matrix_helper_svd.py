#!/usr/bin/env python3
"""Verify the CNR matrix helper as a 3x3 two-sided SVD equivalent."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "tools/lldb_probes/denoise_route_census"
OUT = ROOT / "runs/denoise_route_census/cnr_matrix_helper_svd.json"

RUNTIME_REPORTS = {
    "unit1_28mm": ROOT / "runs/denoise_route_census/unit1_28mm_cnr_formula.json",
    "unit1_35mm": ROOT / "runs/denoise_route_census/unit1_35mm_cnr_formula.json",
    "unit1_70mm": ROOT / "runs/denoise_route_census/unit1_70mm_cnr_formula.json",
    "unit1_150mm": ROOT / "runs/denoise_route_census/unit1_150mm_cnr_formula.json",
    "unit2_35mm": ROOT / "runs/denoise_route_census/unit2_35mm_cnr_formula.json",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_static() -> dict[str, object]:
    inspector = load_module("inspect_cnr_static", PROBE_DIR / "inspect_cnr_static.py")
    data = inspector.LIBCP.read_bytes()
    report = inspector.inspect(data)
    for name, item in report["ranges"].items():
        require(item["hash_ok"], f"static range hash drift: {name}")

    calls = {(item["at"], item["target"]) for item in report["call_targets"]}
    require(("0x3088a8", "0x309270") in calls, "worker no longer calls helper")
    require(("0x30960e", "0x309d50") in calls, "helper no longer calls rotation helper")

    # Mode 0x14 is the only admitted live CNR helper mode at the caller.
    sections = inspector.macho_sections(data)
    caller = inspector.bytes_at(data, sections, 0x308890, 0x30)
    require(b"\xba\x14\x00\x00\x00" in caller, "CNR helper mode 0x14 not found")

    constants = {item["target"]: item for item in report["rip_reads"]}
    require(constants["0x5d3ad8"]["bytes"]["f64"][0] == 4.440892098500626e-16, "SVD sweep epsilon")
    require(constants["0x5c3890"]["bytes"]["f64"][0] == np.finfo(np.float64).tiny, "DBL_MIN")
    require(
        constants["0x5acc40"]["bytes"]["u64"][:2]
        == [0x7FFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFF],
        "double abs mask",
    )

    return {
        "libcp_sha256": hashlib.sha256(data).hexdigest(),
        "matrix_helper_sha256": report["ranges"]["matrix_helper_0x309270"]["sha256"],
        "rotation_helper_sha256": report["ranges"]["rotation_helper_0x309d50"]["sha256"],
    }


def complete_samples(report: dict[str, object]) -> list[dict[str, object]]:
    return [
        sample
        for sample in report["samples"]
        if sample.get("helper_pre") and sample.get("helper_post")
    ]


def verify_sample(label: str, index: int, sample: dict[str, object]) -> dict[str, object]:
    matrix = np.array(sample["helper_pre"]["matrix_input_9d"]["f64"][:9], dtype=np.float64).reshape(3, 3)
    post = sample["helper_post"]["helper_object_post"]["f64"]
    left = np.array(post[:9], dtype=np.float64).reshape(3, 3)
    right = np.array(post[9:18], dtype=np.float64).reshape(3, 3)
    singular = np.array(post[18:21], dtype=np.float64)

    require(np.all(singular >= 0.0), f"{label} sample {index}: negative singular value")
    require(np.all(singular[:-1] >= singular[1:]), f"{label} sample {index}: unsorted singular values")

    left_orth = float(np.max(np.abs(left @ left.T - np.eye(3))))
    right_orth = float(np.max(np.abs(right @ right.T - np.eye(3))))
    require(left_orth <= 2e-14, f"{label} sample {index}: left orth err {left_orth}")
    require(right_orth <= 2e-14, f"{label} sample {index}: right orth err {right_orth}")

    reconstructed = right.T @ np.diag(singular) @ left
    recon_abs = float(np.max(np.abs(reconstructed - matrix)))
    recon_rel = float(recon_abs / max(1.0, float(np.max(np.abs(matrix)))))
    require(recon_abs <= 1e-7, f"{label} sample {index}: reconstruction abs err {recon_abs}")
    require(recon_rel <= 1e-12, f"{label} sample {index}: reconstruction rel err {recon_rel}")

    numpy_singular = np.linalg.svd(matrix, compute_uv=False)
    singular_abs = float(np.max(np.abs(numpy_singular - singular)))
    require(singular_abs <= 1e-7, f"{label} sample {index}: singular err {singular_abs}")

    return {
        "sample_index": index,
        "matrix_max_abs": float(np.max(np.abs(matrix))),
        "matrix_asymmetry_max_abs": float(np.max(np.abs(matrix - matrix.T))),
        "singular_values": singular.tolist(),
        "left_orthonormal_max_abs": left_orth,
        "right_orthonormal_max_abs": right_orth,
        "reconstruction_max_abs": recon_abs,
        "reconstruction_max_rel": recon_rel,
        "numpy_singular_max_abs": singular_abs,
    }


def verify_runtime() -> dict[str, object]:
    samples_by_label: dict[str, object] = {}
    totals = {
        "sample_count": 0,
        "max_reconstruction_abs": 0.0,
        "max_reconstruction_rel": 0.0,
        "max_orthonormal_abs": 0.0,
        "max_numpy_singular_abs": 0.0,
        "max_matrix_asymmetry_abs": 0.0,
    }

    for label, path in RUNTIME_REPORTS.items():
        report = json.loads(path.read_text())
        require(not report["errors"], f"{label}: probe errors {report['errors']}")
        samples = complete_samples(report)
        require(len(samples) >= 3, f"{label}: insufficient helper samples")
        verified = [verify_sample(label, index, sample) for index, sample in enumerate(samples)]
        samples_by_label[label] = verified
        totals["sample_count"] += len(verified)
        for item in verified:
            totals["max_reconstruction_abs"] = max(
                totals["max_reconstruction_abs"], item["reconstruction_max_abs"]
            )
            totals["max_reconstruction_rel"] = max(
                totals["max_reconstruction_rel"], item["reconstruction_max_rel"]
            )
            totals["max_orthonormal_abs"] = max(
                totals["max_orthonormal_abs"],
                item["left_orthonormal_max_abs"],
                item["right_orthonormal_max_abs"],
            )
            totals["max_numpy_singular_abs"] = max(
                totals["max_numpy_singular_abs"], item["numpy_singular_max_abs"]
            )
            totals["max_matrix_asymmetry_abs"] = max(
                totals["max_matrix_asymmetry_abs"], item["matrix_asymmetry_max_abs"]
            )

    return {"totals": totals, "samples": samples_by_label}


def main() -> None:
    static = verify_static()
    runtime = verify_runtime()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"static": static, "runtime": runtime}, indent=2, sort_keys=True)
        + "\n"
    )
    totals = runtime["totals"]
    print(
        "cnr_matrix_helper_svd=OK "
        f"libcp={static['libcp_sha256']} "
        f"samples={totals['sample_count']} "
        f"max_recon_abs={totals['max_reconstruction_abs']:.3g} "
        f"max_singular_abs={totals['max_numpy_singular_abs']:.3g} "
        f"max_asym={totals['max_matrix_asymmetry_abs']:.3g}"
    )


if __name__ == "__main__":
    main()

