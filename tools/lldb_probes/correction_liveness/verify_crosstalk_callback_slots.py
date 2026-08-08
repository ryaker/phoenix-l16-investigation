#!/usr/bin/env python3
"""Verify installed RemoveCrossTalkGeneric callback-slot identities."""

import argparse
import hashlib
import json
import struct
from pathlib import Path


EXPECTED_BINARY_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
VTABLES = {
    "vec4_false": (0x653070, 0xFEBF0, 0x100560),
    "float_false": (0x6530F8, 0x100680, 0x1019A0),
    "vec4_true": (0x653178, 0x103120, 0x1053B0),
    "float_true": (0x6531F8, 0x1054D0, 0x106C80),
}
BODY_RANGES = {
    "executor_2e20": (0x2E20, 0x2F44, "4bcdc02508eddbbe7542902e190179ec8bf4e5f708926fad29b487df435f3c26"),
    "float_true_1054d0": (0x1054D0, 0x106C80, "b18f4a2134ecc02222e640a0e6d8b06d62fdb6a5ff3a13adf5a014b881d8ef9d"),
    "stage5_wrapper_341b30": (0x341B30, 0x341F90, "5551b3413d4f7e2f353c8bad2dca9b5fdc425476ba5d1951a4dd7767b0c27328"),
    "demosaic_handoff_342ca0": (0x342CA0, 0x342F94, "1bd02ccf7ce27f9b8348b8f2670e52bf6468a8df669a4677d96b340afbfb85f2"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "binary",
        nargs="?",
        default="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib",
    )
    args = parser.parse_args()
    data = Path(args.binary).read_bytes()
    binary_sha = hashlib.sha256(data).hexdigest()
    assert binary_sha == EXPECTED_BINARY_SHA256, binary_sha

    vtables = {}
    for name, (address, callback, secondary) in VTABLES.items():
        actual_callback = struct.unpack_from("<Q", data, address + 0x30)[0]
        actual_secondary = struct.unpack_from("<Q", data, address + 0x38)[0]
        assert (actual_callback, actual_secondary) == (callback, secondary)
        vtables[name] = {
            "vtable": address,
            "slot_0x30": actual_callback,
            "slot_0x38": actual_secondary,
        }

    # Both direct virtual-dispatch sites in generic executor 0x2e20 use
    # call qword ptr [rax+0x30].
    assert data[0x2ED5:0x2ED8] == bytes.fromhex("ff5030")
    assert data[0x2F1C:0x2F1F] == bytes.fromhex("ff5030")

    body_hashes = {}
    for name, (begin, end, expected) in BODY_RANGES.items():
        actual = hashlib.sha256(data[begin:end]).hexdigest()
        assert actual == expected, (name, actual)
        body_hashes[name] = actual

    print(
        json.dumps(
            {
                "binary_sha256": binary_sha,
                "executor_slot": 0x30,
                "vtables": vtables,
                "body_sha256": body_hashes,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
