#!/usr/bin/env python3
"""Verify static custody and captured four-focal validation artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE_PATH = (
    ROOT
    / "tools/lldb_probes/prefusion_cache_rtti_identity"
    / "verify_prefusion_cache_rtti_identity.py"
)
UNDISTORT_ANALYSIS = ROOT / "runs/reference_undistorted_planes/analysis.json"
DEPTH_ANALYSIS = ROOT / "runs/reference_stage_maps/analysis.json"
INDEX_DISTRIBUTIONS = ROOT / "runs/reference_stage_maps/index5_repeat_distributions.json"
INDEX_COUPLING = ROOT / "runs/reference_stage_maps/index5_full_map_coupling.json"

EXPECTED_PLANES = {
    "28mm": {
        "B1": ([4774, 3631], "d1a150a642e6a9aa64c47da668fa86b1ec8caae5e1f8d796a1d003117b9769b3"),
        "B2": ([4764, 3616], "2d61ca786e1c29003e004ebd1a403073087b4116c9515b888ec8140af5e181dc"),
        "B3": ([4764, 3616], "43d0ebefa86eec411a489600a5d073825b02a291a543f78c794e0c930b7641ed"),
        "B4": ([4318, 3260], "179a5d69a4f0cdcd68ac1097780db853fbdadf014d750190ccae2448f10300f6"),
        "B5": ([4739, 3596], "279bece18ecad776bb66ea3448ae9e335bf271e1fba319b38e99516f5cde1188"),
    },
    "35mm": {
        "B1": ([4784, 3636], "372a81a8a0e8aced41ab56aa7cfacc29a5e647176239fed83d7e4bd8417cc5d0"),
        "B2": ([4719, 3580], "21f3b91800739cbe8abc062a4e49cd31fa281aa72e5b59f30975c7a7cd43171a"),
        "B3": ([4769, 3626], "e5b0b230849d4321e6666c0410f7f916a398ca1f5257e8a3bcf76d0196a4494f"),
        "B4": ([4328, 3260], "f8783e1b2c68d3379ee2e736222a65bc699b42ae04a5252d39075831643db9ed"),
        "B5": ([4739, 3591], "17e159822c06f31e156dcc9d7db09a7802c561177f3c63f728c4142d4170c4bb"),
    },
    "70mm": {
        "C1": ([4217, 3186], "07055c34cecc0eb8aeb57f4f865f10b7afe8a9f30da348482a92b90f0d06e07e"),
        "C2": ([4178, 3134], "c23951f0f20d8e32f40fcfe8e90c99f0515a7626c422e57f65f13c84cf53e6c2"),
        "C3": ([4170, 3177], "c96610a63bc97fc9ba6750ecedc021d039d6a2c7d343a00013ba1e85b0c7bbdd"),
        "C4": ([4217, 3216], "ed769ca719ae4eee88026a5b6095492b0c6f8d71b7e793eaf7025985458df5cd"),
        "C5": ([4174, 3160], "1cd84d2eaf732fd0c5320b2a764a8b19fdfa01b23e851cd6bacc71948e51064e"),
    },
    "150mm": {
        "C1": ([4161, 3164], "97fc5e1eafd6a57791bd39ad16734d22302f02ec80970942343aa30a86e36e52"),
        "C2": ([4118, 3109], "6b65986e7cd8bd8eb0099f0fa8d6ce508a440cc25638af69368f2a4a1abf196f"),
        "C3": ([4140, 3134], "ea89092cd3bf45c823cc201f4d9bef88db95bfa976a85da5b3d5bc5051b8c5bb"),
        "C4": ([4161, 3152], "2ec5a139f10503e74307b098fe3d189fe2e98ee02cfe251e6eea850e2f462c95"),
        "C5": ([4174, 3160], "ab23cac8e775a11bc7d773b89ff24d1ea3d622cd1711e692382aaab852809796"),
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_module("reference_validation_static_base", BASE_PATH)
STATIC = BASE.STATIC


def u64(raw: bytes) -> int:
    return struct.unpack("<Q", raw)[0]


def call_target(data: bytes, mapping, va: int) -> int:
    raw = STATIC.bytes_at(data, mapping, va, 5)
    require(raw[0] == 0xE8, f"0x{va:x} is not a direct call")
    return va + 5 + struct.unpack_from("<i", raw, 1)[0]


def verify_static() -> str:
    digest, _ = BASE.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    windows = {
        (0x667A10, 0x667A68): "ec7d75bdba1b52be10f9c33441a43da113fe71f8df61f715f569c56ba49b3dab",
        (0x261A50, 0x261F27): "8c17b1464461a37ab824e2c778504f4c01d2c6c673c8b364c70eca9e189b9712",
        (0x262130, 0x262170): "e3d03ffb1e5c0c4d687eb4d1385aa1a436719057ee51df6814bf60e87109ad55",
        (0x3E78D0, 0x3E7A36): "22db418fba49a202fef97779ef757dd119a05dea7b9bed5f124ec40cbd82591e",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(STATIC.bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")

    name = BASE.rtti_name(data, mapping, 0x667A20)
    for token in ("ImageWarpClamped", "ImageLensUndistort", "LensUndistortCRA"):
        require(token in name, f"undistort RTTI missing {token}")
    slots = tuple(
        u64(STATIC.bytes_at(data, mapping, 0x667A20 + 8 * index, 8))
        for index in range(9)
    )
    require(
        slots == (0x262080, 0x262090, 0x2620A0, 0x2620E0, 0x262110, 0x262120, 0x262130, 0x262140, 0x262160),
        "ImageLensUndistort callback table changed",
    )
    require(call_target(data, mapping, 0x26159D) == 0x261A50, "undistort body call changed")
    require(call_target(data, mapping, 0x3E79CB) == 0x261050, "SourceImageCache undistort call changed")
    require(call_target(data, mapping, 0x3E79E8) == 0x3E82D0, "SourceImageCache half conversion changed")
    return digest


def verify_undistorted() -> None:
    analysis = json.loads(UNDISTORT_ANALYSIS.read_text(encoding="ascii"))
    for focal, expected_cameras in EXPECTED_PLANES.items():
        run = analysis["runs"][focal]
        require(run["cache_count"] == 5, f"{focal}: cache count")
        require(set(run["planes"]) == set(expected_cameras), f"{focal}: camera set")
        for camera, (size, digest) in expected_cameras.items():
            plane = run["planes"][camera]
            require(plane["size"] == size, f"{focal}/{camera}: size")
            require(plane["sha256"] == digest, f"{focal}/{camera}: digest")
            require(Path(plane["output"]).stat().st_size == plane["logical_bytes"], f"{focal}/{camera}: bytes")
    repeat = analysis["repeat_comparison"]
    require(set(repeat) == set(EXPECTED_PLANES["28mm"]), "28mm repeat camera set")
    require(all(item["same_size"] and item["same_sha256"] for item in repeat.values()), "28mm repeat drift")


def verify_depth_maps() -> None:
    analysis = json.loads(DEPTH_ANALYSIS.read_text(encoding="ascii"))
    reports = analysis["four_focal_reports"]
    require(set(reports) == {"unit1_28mm", "unit1_35mm", "unit1_70mm", "unit1_150mm"}, "depth focal set")
    for focal, maps in reports.items():
        require(set(maps) == {"index5_hypothesis_index", "index5_depth", "upsampled_depth", "gdepth_full"}, f"{focal}: map set")
        require(maps["index5_hypothesis_index"]["logical_bytes"] == 2080 * 1560 * 2, f"{focal}: index bytes")
        require(maps["index5_depth"]["logical_bytes"] == 2080 * 1560 * 4, f"{focal}: depth bytes")
        require(maps["upsampled_depth"]["logical_bytes"] == 4160 * 3120 * 4, f"{focal}: upsample bytes")
        require(maps["gdepth_full"]["logical_bytes"] == 10432 * 7824 * 4, f"{focal}: gdepth bytes")
    repeats = analysis["unit1_same_route_repeats"]
    require(repeats["35"]["index5_depth"]["unequal"] == 0, "35mm repeat changed")
    require(repeats["70"]["index5_depth"]["unequal_fraction"] > 0.99, "70mm nondeterminism absent")
    require(repeats["150"]["index5_depth"]["unequal_fraction"] == 1.0, "150mm nondeterminism absent")


def verify_index_distributions() -> None:
    distributions = json.loads(INDEX_DISTRIBUTIONS.read_text(encoding="ascii"))
    require(distributions["sample_count_per_focal"] == 10, "index sample count")
    expected_classes = {
        "28": (4, [4, 4, 1, 1]),
        "35": (2, [9, 1]),
        "70": (10, [1] * 10),
        "150": (10, [1] * 10),
    }
    expected_depth_max_nrmse = {
        "28": 0.1084359554282923,
        "35": 0.00037496268285911995,
        "70": 1.397124471877407,
        "150": 1.3978847902101652,
    }
    for focal, (class_count, class_sizes) in expected_classes.items():
        maps = distributions["focals"][focal]["maps"]
        for name in ("index5_hypothesis_index", "index5_depth"):
            require(maps[name]["exact_class_count"] == class_count, f"{focal}/{name}: classes")
            require(maps[name]["exact_class_sizes"] == class_sizes, f"{focal}/{name}: class sizes")
        actual = maps["index5_depth"]["pair_summary"]["normalized_rmse"]["maximum"]
        require(abs(actual - expected_depth_max_nrmse[focal]) < 1e-15, f"{focal}: depth nrmse")

    coupling = json.loads(INDEX_COUPLING.read_text(encoding="ascii"))
    require(coupling["total_pixels"] == 129_792_000, "coupling pixel count")
    for focal, count in {"28": 752, "35": 752, "70": 1472, "150": 1472}.items():
        entry = coupling["focals"][focal]
        require(entry["lookup_count"] == count, f"{focal}: lookup count")
        require(len(entry["samples"]) == 10, f"{focal}: coupling samples")
        require(all(item["bit_mismatches"] == 0 for item in entry["samples"]), f"{focal}: coupling mismatch")


def main() -> None:
    digest = verify_static()
    verify_undistorted()
    verify_depth_maps()
    verify_index_distributions()
    print(f"reference_validation_static=OK libcp={digest}")
    print("undistorted_planes=20 four_focal_camera_scoped repeat_28mm=byte_identical")
    print("depth_maps=16 four_focal_complete repeats=4x4 nondeterministic_tele=true")
    print("index5_distribution_samples=40 pairwise=180 coupling_pixels=129792000 mismatches=0")
    print("reference_validation_artifacts=OK")


if __name__ == "__main__":
    main()
