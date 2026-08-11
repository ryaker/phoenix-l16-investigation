#!/usr/bin/env python3
"""Verify installed ColorFusionBayer selection and profile-3 +0xcc tuning."""

import argparse
import hashlib
import pathlib
import struct


EXPECTED_BINARY_SHA256 = (
    "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS " + message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def call_target(data, address):
    require(data[address] == 0xE8, "call opcode at 0x%x" % address)
    displacement = struct.unpack_from("<i", data, address + 1)[0]
    return address + 5 + displacement


def f32s(data, offset, count):
    return struct.unpack_from("<%df" % count, data, offset)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "binary",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(
            "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/"
            "Frameworks/libcp.dylib"
        ),
    )
    args = parser.parse_args()
    data = args.binary.read_bytes()
    require(sha256(data) == EXPECTED_BINARY_SHA256, "installed libcp SHA-256")

    windows = {
        (0x1A89C0, 0x118): "53b2c2bbf4f5be277a9b46b6845746bc72a3db33577b49dbcf179ddf57ed7631",
        (0x1A8D70, 0x279): "d709e406fb5cd0f19201e41e25bfe6e4098e2a8be489b5386c4f0391a6144020",
        (0x40364D, 0x190): "a5caf169f5e6c059117fe9d16d824ad4c93598561d3019ff560bab722196a5fd",
    }
    for (offset, size), expected in windows.items():
        require(
            sha256(data[offset : offset + size]) == expected,
            "body window 0x%x+0x%x" % (offset, size),
        )

    # Constructor: target ID comes from RawImageFactory and lands at +0x140;
    # +0x148/+0x150/+0x158 are zeroed as an int32 vector before initialize.
    require(call_target(data, 0x1A8A8A) == 0x1BEA00, "target-camera getter")
    require(
        data[0x1A8A8F : 0x1A8A95] == bytes.fromhex("898340010000"),
        "target camera stored at ColorFusionBayer+0x140",
    )
    require(
        data[0x1A8AB4 : 0x1A8ABB] == bytes.fromhex("0f118348010000"),
        "source-ID vector begins at ColorFusionBayer+0x148",
    )

    calls = {
        0x1A8D96: 0x1BDB60,
        0x1A8DDC: 0x1BE970,
        0x1A8E00: 0xF2720,
        0x1A8E0F: 0x1BEA00,
        0x1A8E21: 0xF2720,
        0x1A8E2C: 0xF6C60,
        0x1A8E40: 0xF6C60,
        0x1A8E4F: 0xF2750,
        0x1A8E5F: 0xF2720,
        0x1A8EEC: 0x1BE970,
        0x1A8EFF: 0xF2720,
        0x1A8F0E: 0x1BEA00,
        0x1A8F1C: 0xF2720,
        0x1A8F27: 0xF6C60,
        0x1A8F3B: 0xF6C60,
        0x1A8F4A: 0xF2750,
        0x1A8F5A: 0xF2720,
    }
    for address, expected in calls.items():
        require(call_target(data, address) == expected, "selector call 0x%x" % address)
    require(
        data[0x1A8DF0 : 0x1A8DF4] == bytes.fromhex("807f3000"),
        "selector requires CapturedImage.is_enabled at +0x30",
    )
    require(
        data[0x1A8E54 : 0x1A8E5A] == bytes.fromhex("8b48040b0878"),
        "selector rejects negative Bayer-override x/y by sign bit",
    )
    require(
        data[0x1A8E77 : 0x1A8E84] == bytes.fromhex("89014883c10449898e50010000"),
        "accepted camera ID appended to +0x148 int32 vector",
    )

    # Renderer profile 3 has admitted Demosaicking tuple (3,1), so 0x40b2b0
    # returns false. The false branch keeps the key-2/key-4 map at r13.
    require(call_target(data, 0x403078) == 0x40B2B0, "Demosaicking selector call")
    require(
        data[0x40364D : 0x40365A] == bytes.fromhex("84db488d8538ffffff4c0f45e8"),
        "false selector keeps combined key-2/key-4 tuning map",
    )
    require(call_target(data, 0x403664) == 0xF2730, "public SensorData.type getter")
    sensor_to_key = struct.unpack_from("<5i", data, 0x60AA80)
    require(sensor_to_key == (2, 2, 2, 4, 4), "sensor-type-minus-one tuning-key map")
    require(
        sha256(data[0x60AA80 : 0x60AA94])
        == "51b179bafa63884b3a0c3fd9ab9d951e89f3d2b15e4a26c57c1c4be048cbcd29",
        "sensor tuning-key table SHA-256",
    )

    require(call_target(data, 0x4036D5) == 0xF32D0, "public analog-gain getter")
    require(f32s(data, 0x5AE770, 1) == (100.0,), "analog gain scaled by exact 100.0f")
    require(
        data[0x4037C0 : 0x4037DC]
        == bytes.fromhex("498d85c8000000488b8db0feffff488948100f2885a0feffff0f1100"),
        "selected six-float row copied to FusionCacheBayer+0xc8..+0xdc",
    )

    key2 = f32s(data, 0x60A988, 30)
    key4 = f32s(data, 0x60AA00, 30)
    key2_rows = [key2[index : index + 6] for index in range(0, 30, 6)]
    key4_rows = [key4[index : index + 6] for index in range(0, 30, 6)]
    require(
        sha256(data[0x60A988 : 0x60AA00])
        == "0c6e12d8c5dea753c49f71aa8613cbc8bf4a91b1adfa419de1cd7c6664ed568b",
        "key-2 five-row table SHA-256",
    )
    require(
        sha256(data[0x60AA00 : 0x60AA78])
        == "ad33094f937a50550dc207db98ec86126feec3ede553e7cc4123cb8f8daf371b",
        "key-4 five-row table SHA-256",
    )
    require(
        [row[1] for row in key2_rows] == [1.0] * 5,
        "all key-2 gain rows set FusionCacheBayer+0xcc to exact 1.0f",
    )
    require(
        [row[1] for row in key4_rows] == [1.7000000476837158, 1.350000023841858,
                                         1.2000000476837158, 0.75, 0.5],
        "key-4 +0xcc alternatives retained as out-of-scope discriminator",
    )
    print("RESULT profile3 + SENSOR_AR1335(2) selects key 2; +0xcc=1.0f at every gain row")
    print("RESULT selector rule is enabled AND non-target AND same-group AND nonnegative Bayer override")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
