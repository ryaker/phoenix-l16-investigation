#!/usr/bin/env python3
"""Build and verify an independent tagged linear-ProPhoto float TIFF."""

from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import json
import struct
import subprocess
from pathlib import Path

import numpy as np
import tifffile


ROOT = Path(__file__).resolve().parents[2]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUNS = ROOT / "runs/output_tagged_export"
ICC_PATH = RUNS / "phoenix_linear_prophoto.icc"
TIFF_PATH = RUNS / "phoenix_linear_prophoto_float32.tiff"
REPORT_PATH = RUNS / "verification.json"


class cmsCIExyY(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("Y", ctypes.c_double),
    ]


class cmsCIExyYTRIPLE(ctypes.Structure):
    _fields_ = [
        ("Red", cmsCIExyY),
        ("Green", cmsCIExyY),
        ("Blue", cmsCIExyY),
    ]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def xy_from_xyz(xyz):
    total = sum(xyz)
    require(total > 0, "invalid XYZ")
    return xyz[0] / total, xyz[1] / total


def installed_prophoto():
    data = LIBCP.read_bytes()
    require(
        hashlib.sha256(data).hexdigest()
        == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        "libcp hash drift",
    )
    compact = struct.unpack_from("<7f", data, 0x5AAE20)
    require(
        compact
        == (
            0.7976748943328857,
            0.13519169390201569,
            0.03135339915752411,
            0.2880401909351349,
            0.7118741273880005,
            8.569999772589654e-05,
            0.8252099752426147,
        ),
        "installed ProPhoto matrix drift",
    )
    matrix = (
        (compact[0], compact[1], compact[2]),
        (compact[3], compact[4], compact[5]),
        (0.0, 0.0, compact[6]),
    )
    red_xyz = (matrix[0][0], matrix[1][0], matrix[2][0])
    green_xyz = (matrix[0][1], matrix[1][1], matrix[2][1])
    blue_xyz = (matrix[0][2], matrix[1][2], matrix[2][2])
    white_xyz = tuple(sum(row) for row in matrix)
    primaries = {
        "red": xy_from_xyz(red_xyz),
        "green": xy_from_xyz(green_xyz),
        "blue": xy_from_xyz(blue_xyz),
    }
    white = xy_from_xyz(white_xyz)
    return matrix, primaries, white


def lcms():
    library_path = ctypes.util.find_library("lcms2")
    require(library_path, "LittleCMS 2 unavailable")
    library = ctypes.CDLL(library_path)
    library.cmsBuildGamma.argtypes = [ctypes.c_void_p, ctypes.c_double]
    library.cmsBuildGamma.restype = ctypes.c_void_p
    library.cmsFreeToneCurve.argtypes = [ctypes.c_void_p]
    library.cmsCreateRGBProfile.argtypes = [
        ctypes.POINTER(cmsCIExyY),
        ctypes.POINTER(cmsCIExyYTRIPLE),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.cmsCreateRGBProfile.restype = ctypes.c_void_p
    library.cmsSetProfileVersion.argtypes = [ctypes.c_void_p, ctypes.c_double]
    library.cmsSetHeaderRenderingIntent.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    library.cmsMLUalloc.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    library.cmsMLUalloc.restype = ctypes.c_void_p
    library.cmsMLUsetASCII.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    library.cmsMLUsetASCII.restype = ctypes.c_int
    library.cmsMLUfree.argtypes = [ctypes.c_void_p]
    library.cmsWriteTag.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
    library.cmsWriteTag.restype = ctypes.c_int
    library.cmsMD5computeID.argtypes = [ctypes.c_void_p]
    library.cmsMD5computeID.restype = ctypes.c_int
    library.cmsSaveProfileToFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    library.cmsSaveProfileToFile.restype = ctypes.c_int
    library.cmsCloseProfile.argtypes = [ctypes.c_void_p]
    return library


def add_text_tag(library, profile, signature, text):
    mlu = library.cmsMLUalloc(None, 1)
    require(mlu, "cmsMLUalloc failed")
    try:
        require(
            library.cmsMLUsetASCII(mlu, b"en", b"US", text.encode("ascii")),
            f"cannot set {text}",
        )
        require(library.cmsWriteTag(profile, signature, mlu), f"cannot write {signature:#x}")
    finally:
        library.cmsMLUfree(mlu)


def create_profile(primaries, white):
    library = lcms()
    white_point = cmsCIExyY(white[0], white[1], 1.0)
    primary_triple = cmsCIExyYTRIPLE(
        cmsCIExyY(*primaries["red"], 1.0),
        cmsCIExyY(*primaries["green"], 1.0),
        cmsCIExyY(*primaries["blue"], 1.0),
    )
    curves = [library.cmsBuildGamma(None, 1.0) for _ in range(3)]
    require(all(curves), "cannot build linear tone curves")
    curve_array = (ctypes.c_void_p * 3)(*curves)
    profile = library.cmsCreateRGBProfile(
        ctypes.byref(white_point), ctypes.byref(primary_triple), curve_array
    )
    try:
        require(profile, "cannot create RGB profile")
        library.cmsSetProfileVersion(profile, 4.3)
        library.cmsSetHeaderRenderingIntent(profile, 1)
        add_text_tag(library, profile, 0x64657363, "Phoenix Linear ProPhoto RGB")
        add_text_tag(library, profile, 0x63707274, "CC0-1.0 Phoenix investigation")
        require(library.cmsMD5computeID(profile), "cannot compute profile ID")
        require(
            library.cmsSaveProfileToFile(profile, str(ICC_PATH).encode()),
            "cannot save profile",
        )
    finally:
        if profile:
            library.cmsCloseProfile(profile)
        for curve in curves:
            library.cmsFreeToneCurve(curve)


def canonicalize_profile():
    data = bytearray(ICC_PATH.read_bytes())
    data[24:36] = struct.pack(">6H", 2026, 7, 4, 0, 0, 0)
    digest_input = bytearray(data)
    digest_input[44:48] = b"\0" * 4
    digest_input[64:68] = b"\0" * 4
    digest_input[84:100] = b"\0" * 16
    data[84:100] = hashlib.md5(digest_input).digest()
    ICC_PATH.write_bytes(data)


def profile_tags(data):
    require(data[36:40] == b"acsp", "ICC signature")
    count = struct.unpack_from(">I", data, 128)[0]
    result = {}
    for index in range(count):
        offset = 132 + 12 * index
        signature, payload_offset, size = struct.unpack_from(">4sII", data, offset)
        result[signature.decode("ascii")] = data[payload_offset : payload_offset + size]
    return result


def s15fixed16(raw):
    return struct.unpack(">i", raw)[0] / 65536.0


def xyz_tag(payload):
    require(payload[:4] == b"XYZ ", "XYZ tag type")
    return tuple(s15fixed16(payload[8 + 4 * index : 12 + 4 * index]) for index in range(3))


def linear_curve(payload):
    if payload[:4] == b"curv":
        count = struct.unpack_from(">I", payload, 8)[0]
        if count == 0:
            return True
        if count == 1:
            return struct.unpack_from(">H", payload, 12)[0] == 256
    if payload[:4] == b"para":
        function_type = struct.unpack_from(">H", payload, 8)[0]
        return function_type == 0 and s15fixed16(payload[12:16]) == 1.0
    return False


def verify_profile(primaries, white):
    data = ICC_PATH.read_bytes()
    require(struct.unpack_from(">I", data, 0)[0] == len(data), "ICC size")
    require(data[16:20] == b"RGB ", "ICC input space")
    require(data[20:24] == b"XYZ ", "ICC PCS")
    digest_input = bytearray(data)
    digest_input[44:48] = b"\0" * 4
    digest_input[64:68] = b"\0" * 4
    digest_input[84:100] = b"\0" * 16
    require(data[84:100] == hashlib.md5(digest_input).digest(), "ICC profile ID")
    tags = profile_tags(data)
    for tag in ("rXYZ", "gXYZ", "bXYZ", "wtpt", "rTRC", "gTRC", "bTRC", "desc"):
        require(tag in tags, f"missing ICC {tag}")
    colorants = {
        "red": xyz_tag(tags["rXYZ"]),
        "green": xyz_tag(tags["gXYZ"]),
        "blue": xyz_tag(tags["bXYZ"]),
    }
    for name, xyz in colorants.items():
        actual = xy_from_xyz(xyz)
        expected = primaries[name]
        require(
            max(abs(actual[index] - expected[index]) for index in range(2)) < 7e-5,
            f"{name} primary mismatch: {actual} != {expected}",
        )
    actual_white = xy_from_xyz(xyz_tag(tags["wtpt"]))
    require(
        max(abs(actual_white[index] - white[index]) for index in range(2)) < 5e-5,
        f"white mismatch: {actual_white} != {white}",
    )
    require(all(linear_curve(tags[tag]) for tag in ("rTRC", "gTRC", "bTRC")), "nonlinear TRC")
    return data, colorants, actual_white


def write_tiff(profile):
    pixels = np.array(
        [
            [[-0.125, 0.0, 0.5], [1.0, 1.25, 4.0], [0.125, 0.25, 0.375]],
            [[8.0, 0.75, 0.25], [0.03125, -1.0, 2.0], [0.9, 0.8, 0.7]],
        ],
        dtype=np.float32,
    )
    tifffile.imwrite(
        TIFF_PATH,
        pixels,
        photometric="rgb",
        metadata=None,
        compression=None,
        byteorder="<",
        extratags=[
            (274, "H", 1, 1, False),
            (34675, "B", len(profile), profile, False),
        ],
    )
    return pixels


def run(command):
    result = subprocess.run(command, text=True, capture_output=True)
    require(result.returncode == 0, f"{command}: {result.stderr}")
    return result.stdout + result.stderr


def verify_tiff(profile, expected_pixels):
    with tifffile.TiffFile(TIFF_PATH) as handle:
        require(len(handle.pages) == 1, "TIFF page count")
        page = handle.pages[0]
        require(page.shape == (2, 3, 3), f"TIFF shape {page.shape}")
        require(page.dtype == np.dtype("float32"), f"TIFF dtype {page.dtype}")
        require(page.photometric == tifffile.PHOTOMETRIC.RGB, "TIFF photometric")
        require(page.tags["BitsPerSample"].value == (32, 32, 32), "TIFF bit depth")
        require(page.tags["SampleFormat"].value == (3, 3, 3), "TIFF sample format")
        require(page.tags["PlanarConfiguration"].value == 1, "TIFF planar config")
        require(page.tags["Orientation"].value == 1, "TIFF orientation")
        require(page.tags["InterColorProfile"].value == profile, "TIFF ICC payload")
        actual = page.asarray()
    require(
        actual.astype("<f4").tobytes() == expected_pixels.astype("<f4").tobytes(),
        "TIFF float payload changed",
    )

    sips = run(
        [
            "/usr/bin/sips",
            "-g",
            "pixelWidth",
            "-g",
            "pixelHeight",
            "-g",
            "format",
            "-g",
            "profile",
            str(TIFF_PATH),
        ]
    )
    require("pixelWidth: 3" in sips and "pixelHeight: 2" in sips, "sips dimensions")
    require("format: tiff" in sips, "sips format")
    require("Phoenix Linear ProPhoto RGB" in sips, f"sips profile: {sips}")

    exiftool = run(["/opt/homebrew/bin/exiftool", "-a", "-G1", "-s", str(TIFF_PATH)])
    require("SampleFormat" in exiftool and "Float" in exiftool, "exiftool float")
    require("ProfileDescription" in exiftool and "Phoenix Linear ProPhoto RGB" in exiftool, "exiftool ICC")

    identify = run(["/opt/homebrew/bin/identify", "-verbose", str(TIFF_PATH)])
    require("Format: TIFF" in identify and "Profile-icc:" in identify, "ImageMagick TIFF/ICC")
    tiffinfo = run(["/opt/homebrew/bin/tiffinfo", str(TIFF_PATH)])
    require(
        "Sample Format: IEEE floating point" in tiffinfo
        and "ICC Profile: <present>" in tiffinfo,
        "tiffinfo float/ICC",
    )
    return {
        "sips": sips,
        "exiftool_profile": [
            line for line in exiftool.splitlines() if "ProfileDescription" in line
        ],
        "identify_profile": [
            line for line in identify.splitlines() if "Profile-icc:" in line
        ],
        "tiffinfo": [
            line
            for line in tiffinfo.splitlines()
            if "Sample Format:" in line or "ICC Profile:" in line
        ],
    }


def main():
    RUNS.mkdir(parents=True, exist_ok=True)
    matrix, primaries, white = installed_prophoto()
    create_profile(primaries, white)
    canonicalize_profile()
    profile, colorants, actual_white = verify_profile(primaries, white)
    pixels = write_tiff(profile)
    readers = verify_tiff(profile, pixels)
    report = {
        "status": "PASS",
        "libcp_sha256": hashlib.sha256(LIBCP.read_bytes()).hexdigest(),
        "installed_rgb_to_xyz": matrix,
        "derived_primaries_xy": primaries,
        "derived_white_xy": white,
        "icc_sha256": hashlib.sha256(profile).hexdigest(),
        "icc_size": len(profile),
        "icc_colorants_xyz": colorants,
        "icc_white_xy": actual_white,
        "tiff_sha256": hashlib.sha256(TIFF_PATH.read_bytes()).hexdigest(),
        "tiff_size": TIFF_PATH.stat().st_size,
        "pixel_payload_sha256": hashlib.sha256(pixels.astype("<f4").tobytes()).hexdigest(),
        "readers": readers,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        "tagged_linear_prophoto_tiff=PASS "
        f"icc_bytes={len(profile)} tiff_bytes={TIFF_PATH.stat().st_size} "
        f"white=({white[0]:.8f},{white[1]:.8f})"
    )


if __name__ == "__main__":
    main()
