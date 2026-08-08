#!/usr/bin/env python3
"""Verify static formula and live packet for Laplacian clarity."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/"
    "libcp.dylib"
)
REPORT = ROOT / "runs/laplacian_clarity/laplacian_clarity_28mm.json"
HDR = ROOT / "runs/laplacian_clarity/laplacian_clarity_28mm.hdr"
UNUSED_A_REPORT = ROOT / "runs/laplacian_clarity/unused_fields_a_28mm.json"
UNUSED_B_REPORT = ROOT / "runs/laplacian_clarity/unused_fields_b_28mm.json"
UNUSED_A_HDR = ROOT / "runs/laplacian_clarity/unused_fields_a_28mm.hdr"
UNUSED_B_HDR = ROOT / "runs/laplacian_clarity/unused_fields_b_28mm.hdr"
EXPECTED_SHA = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
SCHEMA_VERIFIER = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody/"
    "verify_embedded_calibration_proto_schema.py"
)
RANGE_HASHES = {
    (0x12C50, 0x12DA1): "72a10e972fbf9b90c643d4deaf62f11d1b8210f6c5cfd0cca27cd19d285875be",
    (0x136E0, 0x13883): "3e4e19c909a8af403826acb67906e6e82a342e2bbad2467871a89fbb02a5bcb5",
    (0x13E40, 0x140E7): "1178fbc292e3dc2891ad5c19cfe2b6abece9432684eb59b56eadeab1f9998c0a",
    (0x14670, 0x14C50): "ceeb1d8bcb65ddf8e0704c4766b6d7f634962a47d75949828b27e0b088e5dbde",
    (0x16250, 0x167B0): "4e2bfd5af09ccb02ef9d297828a6d556f703ddc137ffa538321dc1ad3c53b992",
    (0x2E3F30, 0x2E3F85): "e6aa52063f6679f336c16a8ad6e07378b943a405c056fc5a0ed88c60be8c2986",
    (0x2E4D9B, 0x2E4E0A): "4144c40993068778d9c7c73822eb7b1e0bdd4b9b3c96ac1c7e84f5ad9773f2fc",
    (0x2E4E21, 0x2E4F5B): "50503c1ea39ba7b2475dab796982ecea5761e8a4e3c205fb4a8cef870f538ffe",
    (0x2E5594, 0x2E5C6A): "bc7b6d7cf5a40babf4896e008336f99a2c7a0c27f224e397be1f9ea2742cb723",
    (0x2E7370, 0x2E74D4): "a72708fe633904bd124038bc62afa044affc636b1f9e7cfccbe635df0b9e004e",
    (0x33ED40, 0x33EDB0): "ef6461172e12e1d7a81be43da3346bc03b3a9dc41ce6a56170b1277b81599476",
    (0x319154, 0x319277): "2924ef7fc301de31558f6843b833ace801b13d2936e227f70b68ded4c935ef44",
}
PROPERTY_MAP = {
    0x31915E: ("lpyr_clarity", 0x00),
    0x319181: ("lpyr_shadows", 0x04),
    0x3191A4: ("lpyr_highlights", 0x08),
    0x3191C7: ("lpyr_sigma", 0x0C),
    0x3191EA: ("lpyr_lower_percentile", 0x10),
    0x31920D: ("lpyr_higher_percentile", 0x14),
    0x319230: ("lpyr_mid_percentile", 0x18),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def f32(blob: bytes, offset: int) -> float:
    return struct.unpack_from("<f", blob, offset)[0]


def f64(blob: bytes, offset: int) -> float:
    return struct.unpack_from("<d", blob, offset)[0]


def u64(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob: bytes, offset: int) -> str:
    end = blob.index(b"\0", offset)
    return blob[offset:end].decode("ascii")


def schema_clarity_field(blob: bytes) -> dict[str, object]:
    spec = importlib.util.spec_from_file_location("embedded_schema", SCHEMA_VERIFIER)
    require(spec is not None and spec.loader is not None, "schema verifier import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    descriptors = module.locate_all_descriptors(blob)
    for descriptor in descriptors:
        for message in descriptor["messages"]:
            if message["full_name"] != ".ltpb.Settings":
                continue
            for field in message["fields"]:
                if field["number"] == 9:
                    return field
    raise AssertionError("missing .ltpb.Settings field 9")


def level_count(width: int, height: int) -> int:
    raw = math.trunc(math.log2(min(width, height)) - 2.0)
    return min(6, max(2, raw))


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def shaping_terms(
    samples: tuple[float, ...],
    shadows: float,
    highlights: float,
    lower: float,
    higher: float,
    mid: float,
    entry_scale: float,
) -> dict[str, float]:
    q = next(value for value in samples if value >= mid)
    denominator = 2.0 * (q * q + 4.0) - (q + 2.0) ** 2 + 1e-15
    highlight_slope = (
        2.0 * (0.05 * q + 2.0) - 1.05 * (q + 2.0)
    ) / denominator
    highlight_offset = (
        1.05 * (q * q + 4.0) - (0.05 * q + 2.0) * (q + 2.0)
    ) / denominator
    shadow_amplitude = (
        clamp(2.0 / entry_scale, 0.0, 1.0)
        * 1.3
        * min(1.2, max(0.12, (8.0 - lower) / 22.0))
        * (1.0 - shadows)
    )
    highlight_amplitude = (
        clamp((higher + 1.0) * (2.0 / 3.0), 0.12, 1.0)
        * (1.0 - highlights)
    )
    highlight_envelope_scale = 0.9 * (
        3.05 * higher - higher * higher - 0.1
    )
    return {
        "q": q,
        "highlight_slope": highlight_slope,
        "highlight_offset": highlight_offset,
        "shadow_amplitude": shadow_amplitude,
        "highlight_amplitude": highlight_amplitude,
        "highlight_envelope_scale": highlight_envelope_scale,
        "shadow_low_exponent_scale": -2.5649492740631104 / ((lower + 5.0) ** 2),
        "shadow_high_exponent_scale": -0.1776280701160431,
    }


def verify_watch_report(
    path: Path, hdr: Path, expected: dict[int, set[int]]
) -> None:
    report = json.loads(path.read_text())
    require(report["errors"] == [], f"watch probe errors: {report['errors']}")
    require(report["process"]["exit_status"] == 0, f"watch render failed: {path}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"bad watch HDR: {hdr}")
    ids_to_offsets = {
        item["watchpoint_id"]: item["offset"] for item in report["armed"]
    }
    observed: dict[int, set[int]] = {offset: set() for offset in expected}
    for item in report["watchpoint_hits"]:
        offset = ids_to_offsets[item["watchpoint_id"]]
        observed[offset].add(item["libcp_va"])
    require(observed == expected, f"config consumer PCs changed: {observed}")
    require(
        all(count > 0 for count in report["watchpoint_hit_counts"].values()),
        f"config field not read: {report['watchpoint_hit_counts']}",
    )


def main() -> None:
    blob = LIBCP.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == EXPECTED_SHA, "libcp hash drift")
    for (start, end), expected in RANGE_HASHES.items():
        actual = hashlib.sha256(blob[start:end]).hexdigest()
        require(actual == expected, f"instruction range drift {start:#x}:{end:#x}")

    require(
        struct.unpack_from("<4f", blob, 0x5F0FC0) == (0.0, 1.0, 1.0, 0.5),
        "LaplacianPyramidConfig default prefix",
    )
    require(math.isclose(f32(blob, 0x5F1044), 32 / 8048, rel_tol=2e-7), "LUT step")
    require(f32(blob, 0x5AAE78) == -16.0, "LUT minimum")
    require(f32(blob, 0x5A8874) == -2.0, "sigma clamp factor")
    require(f64(blob, 0x5C37A0) == -2.0, "Gaussian exponent denominator")
    require(f64(blob, 0x5F1070) == 0.75, "level decay")
    kernel = struct.unpack_from("<5f", blob, 0x5A8850)
    require(
        tuple(struct.unpack_from("<5I", blob, 0x5A8850))
        == (0x3D4CCCCD, 0x3E800000, 0x3ECCCCCD, 0x3E800000, 0x3D4CCCCD),
        "Gaussian reduction kernel",
    )
    require(math.isclose(sum(kernel), 1.0, abs_tol=2e-8), "reduction normalization")
    require(
        struct.unpack_from("<4f", blob, 0x5A8190) == (0.25,) * 4
        and struct.unpack_from("<4I", blob, 0x5A81A0) == (0x3C23D70B,) * 4
        and struct.unpack_from("<4I", blob, 0x5A81B0) == (0x3DA3D70B,) * 4
        and struct.unpack_from("<4I", blob, 0x5A81C0) == (0x3F23D70B,) * 4
        and struct.unpack_from("<4f", blob, 0x5A81D0) == (kernel[0],) * 4
        and struct.unpack_from("<4f", blob, 0x5A81E0) == (kernel[2],) * 4,
        "Gaussian expansion parity constants",
    )
    require(level_count(543, 543) == 6, "543-square level rule")
    require(level_count(16, 100) == 2, "minimum level clamp")
    require(level_count(10432, 7824) == 6, "maximum level clamp")
    require(u64(blob, 0x664FC0) == 0x665010, "downsample callback typeinfo")
    require(u64(blob, 0x664FF8) == 0x14620, "downsample callback operator")
    require(u64(blob, 0x665160) == 0x6651B0, "upscale callback typeinfo")
    require(u64(blob, 0x665198) == 0x16210, "upscale callback operator")
    downsample_name = cstring(blob, u64(blob, 0x665018))
    upscale_name = cstring(blob, u64(blob, 0x6651B8))
    require("ImageGaussianFilterAndSubSampleIfE" in downsample_name, "downsample RTTI")
    require("ImageGaussianUpscaleAndSubtractIfE" in upscale_name, "upscale RTTI")
    expected_curve = tuple(-8.0 + 0.5 * index for index in range(19))
    require(struct.unpack_from("<19f", blob, 0x5F1080) == expected_curve, "default curve")
    require(u64(blob, 0x659EA8) == 0x659F00, "callback typeinfo")
    require(u64(blob, 0x659EE0) == 0x2E7360, "callback operator slot")
    name = cstring(blob, u64(blob, 0x659F08))
    require("CreateAndBlendLaplacianPyramids" in name, "callback public identity")
    require("LaplacianPyramidConfig" in name, "config public identity")
    clarity_field = schema_clarity_field(blob)
    require(
        clarity_field["name"] == "clarity"
        and clarity_field["number"] == 9
        and clarity_field["type"] == "float",
        f"unexpected public clarity field: {clarity_field}",
    )

    report = json.loads(REPORT.read_text())
    require(report["errors"] == [], f"probe errors: {report['errors']}")
    require(report["process"]["exit_status"] == 0, "render did not exit 0")
    require(report["counts"]["entry"] > 0, "clarity body not live")
    require(report["counts"]["callback"] > 0, "clarity callback not live")
    require(report["entries"], "missing config packet")
    require(report["callbacks"], "missing callback packet")
    require(HDR.read_bytes().startswith(b"#?RADIANCE"), "bad HDR output")
    verify_watch_report(
        UNUSED_A_REPORT,
        UNUSED_A_HDR,
        {
            0x04: {0x2E5A73, 0x2E5BBB},
            0x08: {0x2E5A29},
            0x10: {0x2E559A},
        },
    )
    verify_watch_report(
        UNUSED_B_REPORT,
        UNUSED_B_HDR,
        {0x14: {0x2E59D6}, 0x18: {0x2E55A8}},
    )
    live_properties = {
        item["address"]: item["name"] for item in report["properties"]
    }
    require(
        live_properties
        == {address: name for address, (name, _offset) in PROPERTY_MAP.items()},
        f"property map mismatch: {live_properties}",
    )

    first = report["entries"][0]
    config = first["config_f32_0x00_0x20"]
    curve = first["curve"]
    require(curve is not None and len(curve) >= 2, "missing config curve")
    require(all(math.isfinite(value) for value in config), "non-finite config")
    require(
        config[:7] == [0.0, 1.0, 1.0, 0.5, -8.0, 0.20000000298023224, -1.0],
        "live config",
    )
    require(tuple(curve) == expected_curve, "live curve")
    for item in report["callbacks"]:
        require(item["curve_offset"] == -8.0, "callback curve offset")
        require(item["curve_scale"] == 2.0, "callback curve scale")
        require(item["curve_bins"] == 19, "callback curve bins")
    levels = sorted({item["level"] for item in report["callbacks"]})
    require(levels == [0, 1, 2, 3, 4], f"unexpected live levels: {levels}")
    source = first["source_descriptor"]
    require(
        levels == list(range(level_count(source["width"], source["height"]) - 1)),
        "runtime detail levels disagree with static level rule",
    )
    shaping = shaping_terms(
        expected_curve,
        *config[1:3],
        *config[4:7:1],
        first["xmm0"][0],
    )
    require(shaping["q"] == -1.0, "default mid sample selection")
    require(shaping["shadow_amplitude"] == 0.0, "default shadows must be neutral")
    require(shaping["highlight_amplitude"] == 0.0, "default highlights must be neutral")
    named_offsets = {
        name: offset for _address, (name, offset) in PROPERTY_MAP.items()
    }
    print(
        "laplacian_clarity=OK "
        f"entries={report['counts']['entry']} callbacks={report['counts']['callback']} "
        f"settings_field=.ltpb.Settings.clarity#9 named_offsets={named_offsets} "
        f"config={config[:7]} lut=8049@[-16,16] curve={curve} levels={levels} "
        f"gaussian_kernel={kernel} total_levels={level_count(source['width'], source['height'])} "
        f"default_shaping={shaping} "
        "transfer=clamp(x,-2*sigma,2*sigma)+clarity*x*exp(-x*x/(2*sigma*sigma)) "
        "detail=expand(gaussian_next)-gaussian_current "
        "blend=pow(0.75,level)*lerp(adjacent_pyramids)"
    )


if __name__ == "__main__":
    main()
