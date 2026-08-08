#!/usr/bin/env python3
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path("/Volumes/Dev/L16_Lumen_ReverseEngineering")
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN = ROOT / "runs/editor_render_type_topology"
REPORTS = {
    "max9": RUN / "editor_refocus_point_overlay_28mm_max9.json",
    "max0p1": RUN / "editor_refocus_point_overlay_28mm_max0p1.json",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def float_from_bits(word):
    return struct.unpack("<f", struct.pack("<I", int(word, 16)))[0]


binary = LIBCP.read_bytes()
require(
    sha256(binary) == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
    "installed libcp identity",
)

ranges = {
    (0x3BBDC4, 0x3BBF12): "040054dc579329d268f523783a4fd6ade326b024bacef0e6f9348d6ad4a7e609",
    (0x3F08C0, 0x3F0AF0): "08e439445e6d314790f45a6f4d6778d8057ac6d3a08b8789893a5eacbbfa0fdc",
}
for (start, end), expected in ranges.items():
    require(sha256(binary[start:end]) == expected, f"static range {start:#x}..{end:#x}")

require(struct.unpack_from("<I", binary, 0x5A8128)[0] == 0x3F800000,
        "blend constant one")

reports = {name: json.loads(path.read_text()) for name, path in REPORTS.items()}
for name, report in reports.items():
    require(report["range_calls"] == 388, f"{name} range call census")
    require(report["overlay_calls"] == 388, f"{name} overlay call census")
    require(report["pixels"] == 108_720_348, f"{name} pixel census")
    require(report["total_lanes"] == 434_881_392, f"{name} lane census")
    require(report["exact_lanes"] == report["total_lanes"],
            f"{name} exact lane count")
    require(report["max_abs"] == 0, f"{name} maximum error")
    require(report["descriptor_mismatches"] == 0,
            f"{name} descriptor custody")
    require(report["parameter_mismatches"] == 0,
            f"{name} stable parameters")
    require(report["color_bits"] ==
            ["3f800000", "00000000", "00000000", "3e800000"],
            f"{name} live overlay color")

wide = reports["max9"]
narrow = reports["max0p1"]
require(wide["max_blur_bits"] == "41100000", "wide max-blur value")
require(wide["lower_bits"] == "43234c33", "wide lower bound")
require(wide["upper_bits"] == "479b529f", "wide upper bound")
require(wide["outside_pixels"] == 0, "wide all-inside treatment")

require(narrow["max_blur_bits"] == "3dcccccd", "narrow max-blur value")
require(narrow["lower_bits"] == "45346539", "narrow lower bound")
require(narrow["upper_bits"] == "46808153", "narrow upper bound")
require(narrow["outside_pixels"] == 88_002_783,
        "narrow outside-focus census")
require(0 < narrow["outside_pixels"] < narrow["pixels"],
        "narrow exercises both predicate outcomes")

print("PASS RefocusPoint max9 all-inside blend: 434881392/434881392 exact lanes")
print("PASS RefocusPoint max0.1 mixed blend: 434881392/434881392 exact lanes")
print(
    "PASS RefocusPoint bounds: "
    f"max9=[{float_from_bits(wide['lower_bits'])}, {float_from_bits(wide['upper_bits'])}] "
    f"max0.1=[{float_from_bits(narrow['lower_bits'])}, "
    f"{float_from_bits(narrow['upper_bits'])}]"
)
