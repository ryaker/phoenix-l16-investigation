#!/usr/bin/env python3
"""Map installed ImageGaussian callback RTTI names to callable vtables."""

from __future__ import annotations

import struct
from pathlib import Path


LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/"
    "libcp.dylib"
)
NAME_ADDRESSES = (
    0x5A821F,
    0x5A82A0,
    0x5A82F0,
    0x5A8380,
    0x5A8510,
    0x5A85B0,
    0x5A8610,
    0x5A86C0,
    0x5A8730,
    0x5A87E0,
    0x5F10D0,
    0x5F11B0,
)


def u64(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob: bytes, offset: int) -> str:
    return blob[offset : blob.index(b"\0", offset)].decode("ascii")


def refs(blob: bytes, value: int) -> list[int]:
    needle = struct.pack("<Q", value)
    return [offset for offset in range(len(blob)) if blob.startswith(needle, offset)]


def main() -> None:
    blob = LIBCP.read_bytes()
    for name_address in NAME_ADDRESSES:
        name = cstring(blob, name_address)
        print(f"name=0x{name_address:x} {name}")
        stored_name_address = name_address + (1 if name.startswith("?") else 0)
        for name_ref in refs(blob, stored_name_address):
            if name_ref < 8:
                continue
            typeinfo = name_ref - 8
            print(f"  typeinfo=0x{typeinfo:x}")
            for typeinfo_ref in refs(blob, typeinfo):
                if typeinfo_ref < 8 or u64(blob, typeinfo_ref - 8) != 0:
                    continue
                address_point = typeinfo_ref + 8
                slots = [u64(blob, address_point + 8 * index) for index in range(7)]
                print(
                    f"    address_point=0x{address_point:x} "
                    + " ".join(
                        f"slot+0x{8 * index:x}=0x{value:x}"
                        for index, value in enumerate(slots)
                    )
                )


if __name__ == "__main__":
    main()
