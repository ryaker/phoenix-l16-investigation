#!/usr/bin/env python3
"""Verify installed ColorFusion reference/source plane construction custody."""

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
        (0x1AB2D0, 0xA3B): "e89e28272f3c3fe9140765cd3cc7038c22d722576e3b6da5ce20945268afaded",
        (0x1AD390, 0x6A5): "9462874714c619ba5efbe2d837ae4de8d42107c00bcdf260bff36c8873f6eb02",
        (0x19BD20, 0x130): "cec5feac47a36ad5c92b0060aa5d2af39b163521880ade07115e01069f83d78b",
        (0x19C310, 0x46E): "38bd01d02aa4cdb51b4655e6b3e8ef788e2f7ec22206c18563a4b643b453b763",
        (0xBFEF0, 0x518): "0b6dbe686f831618774838d715e2d8be3c7c45bd5a0ac0082f4580129de67035",
        (0x1AAB40, 0x372): "d8d0af35693a301329756cf9fe3a254e30f1997ebff86da7a20ad57159d66790",
    }
    for (offset, size), expected in windows.items():
        require(
            sha256(data[offset : offset + size]) == expected,
            "body window 0x%x+0x%x" % (offset, size),
        )

    # initialize: target and each source take the same scalar multiply then
    # Bayer pack route. Each source's flow is produced and retained separately.
    calls = {
        0x1AB4B7: 0x1AD390,
        0x1AB4C7: 0x19BD20,
        0x1AB9BD: 0x1991E0,
        0x1ABA80: 0x1AD390,
        0x1ABA8F: 0x19BD20,
        0x1AAD5D: 0x19C790,
        0x19BDB7: 0x5440,
        0x19C4ED: 0xBFEF0,
        0x19C51F: 0xBFEF0,
    }
    for address, expected in calls.items():
        require(call_target(data, address) == expected, "call edge 0x%x -> 0x%x" % (address, expected))

    require(
        data[0x1AAD24 : 0x1AAD3D]
        == bytes.fromhex("4d8d842428010000498d8c2400010000498d542470f30f5ccb"),
        "core receives flows +0x128, source planes +0x100, reference +0x70 separately",
    )
    require(
        data[0x19BD44 : 0x19BD5B]
        == bytes.fromhex("8b43108b4b1489ca09c2f6c2010f8599000000d1f8d1f9"),
        "packer requires even extents and halves width/height",
    )
    require(
        data[0x19BD67 : 0x19BD7B]
        == bytes.fromhex("488db578ffffffba080000004c89f7e8c537e7ff"),
        "packer allocates eight bytes per half-resolution pixel",
    )
    require(
        data[0x19BD97 : 0x19BDBC]
        == bytes.fromhex("488d054abc4b00488945a04c8975a848895db0488db570ffffff4c89f74c89fae88496e6ff"),
        "packer dispatches installed vtable 0x6579e8",
    )
    require(
        b"PackBayerImageProtoTypeINS2_8vec4x16fEf" in data,
        "RTTI names PackBayerImageProtoType<vec4x16f,float>",
    )
    require(
        data[0x19C4DF : 0x19C4F2].startswith(bytes.fromhex("b901000000"))
        and data[0x19C514 : 0x19C524].startswith(bytes.fromhex("b901000000")),
        "both scalar rows use 0xbfef0 conversion mode 1",
    )
    require(
        data[0x19C5C0 : 0x19C5F3]
        == bytes.fromhex(
            "8d7a014863ff66458b4c7d004863d266418b5c550066418b0456"
            "66418b3c7e6644894cf1fa66895cf1fc668944f1fe66893cf1"
        ),
        "tail pack lane order is top-right, top-left, bottom-left, bottom-right",
    )
    require(
        struct.unpack_from("<4I", data, 0x5AB7A0) == (0x38800000,) * 4
        and struct.unpack_from("<4I", data, 0x5AB7C0) == (0x477FE000,) * 4
        and struct.unpack_from("<4I", data, 0x5AB7D0) == (0xC8000000,) * 4,
        "Float16 conversion boundary/max/exponent constants",
    )

    print("RESULT stored reference/source planes are half-resolution vec4x16f, not vec4x32f")
    print("RESULT lane order is [TR,TL,BL,BR]; flow descriptors remain a parallel vector")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
