#!/usr/bin/env python3
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path("/Volumes/Dev/L16_Lumen_ReverseEngineering")
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
REPORT = ROOT / "runs/editor_render_type_topology/editor_refocus_slider_formula_28mm.json"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value):
    return struct.unpack("<I", struct.pack("<f", value))[0]


binary = LIBCP.read_bytes()
require(
    sha256(binary) == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
    "installed libcp identity",
)

ranges = {
    (0x3A900, 0x3ABB7): "df97caff040beaa6043e59c6a23b1e17a54119b39029438d49a9aacf3c21df7f",
    (0x3BBB43, 0x3BBD83): "ec6fdf181d96e721b6bcf347fabca7e914c216c21af3657de0db9b01251e441a",
    (0x3C0FC0, 0x3C1273): "624dcfd6c714ae431b9b077bfc312195a89efd9b394d5be64ab935f9edb24c9e",
    (0x3C1280, 0x3C154D): "d0a5ac84ca03f182d449e2ceb585e9d7f29a6e705a48bd703f3e0c1a406b43b5",
}
for (start, end), expected in ranges.items():
    require(sha256(binary[start:end]) == expected, f"static range {start:#x}..{end:#x}")

constant_words = {
    0x5A88E0: 0x80000000,
    0x5A8990: bits(-126.0),
    0x5A89A0: bits(128.0),
    0x5A91EC: 0x3E991687,  # 0.299
    0x5A91F0: 0x3F1645A2,  # 0.587
    0x5A91F4: 0x3DE978D5,  # 0.114
    0x5DAE2C: bits(f32(0.07802452147006989)),
    0x5DAE30: bits(f32(0.22606715559959412)),
    0x5DAE34: bits(f32(0.69583356380462646)),
    0x5DAE38: bits(f32(0.99992519617080688)),
    0x6027A8: bits(f32(0.075)),
}
for address, expected in constant_words.items():
    actual = struct.unpack_from("<I", binary, address)[0]
    require(actual == expected, f"constant word {address:#x}: {actual:#x}")

require(
    struct.unpack_from("<4I", binary, 0x602790)
    == (bits(0.0), bits(0.75), bits(1.0), bits(1.0)),
    "cyan visualization color",
)

report = json.loads(REPORT.read_text())
scalar = report["scalar"]
mask = report["mask"]
blend = report["blend"]

require(scalar["calls"] == 388, "RefocusSlider scalar call census")
require(mask["calls"] == 388, "RefocusSlider mask call census")
require(blend["calls"] == 388, "RefocusSlider blend call census")
require(
    scalar["pixels"] == mask["pixels"] == blend["pixels"] == 108_720_348,
    "full-treatment pixel census",
)
require(scalar["selected_converter_va"] == "0x3a900", "selected converter VA")
require(scalar["rec601_exact"] == scalar["pixels"], "Rec.601 exact pixel count")
require(scalar["rec601_max_abs"] == 0, "Rec.601 maximum error")
require(mask["exact"] == mask["pixels"], "mask exact pixel count")
require(mask["max_abs"] == 0, "mask maximum error")
require(mask["parameter_mismatch"] == 0, "stable mask parameters")
require(blend["exact_lanes"] == blend["total_lanes"], "blend exact lane count")
require(blend["total_lanes"] == 4 * blend["pixels"], "blend lane census")
require(blend["max_abs"] == 0, "blend maximum error")

focus = struct.unpack("<f", struct.pack("<I", int(mask["focus_bits"], 16)))[0]
scaled_focus = f32(f32(focus * f32(0.075)) * f32(focus * f32(0.075)))
expected_q = f32(f32(1.0) / scaled_focus)
require(bits(expected_q) == int(mask["q_bits"], 16), "q = 1/(0.075*focus)^2")
require(mask["one_bits"] == "3f800000", "mask complement one")
require(mask["scale_bits"] == "3ecccccd", "mask scale 0.4")

print("PASS RefocusSlider Rec.601 conversion: 108720348/108720348 exact")
print("PASS RefocusSlider depth mask: 108720348/108720348 exact")
print("PASS RefocusSlider cyan blend: 434881392/434881392 exact lanes")
