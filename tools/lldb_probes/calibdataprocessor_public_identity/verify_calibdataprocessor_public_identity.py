#!/usr/bin/env python3
"""Verify CalibDataProcessor's installed public State-machine identity."""

from __future__ import annotations

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/"
    "libcp.dylib"
)
RUN_ROOT = ROOT / "runs/state_machine_return_runtime"

ENTRIES = (
    ("runReferenceGroupCams", 0, 0x658350, 0x229DF0),
    ("runReferenceGroupCams", 1, 0x6583D8, 0x229EC0),
    ("runReferenceGroupCams", 2, 0x658458, 0x22A0E0),
    ("runReferenceGroupCams", 3, 0x6584D8, 0x22A9B0),
    ("runReferenceGroupCams", 4, 0x658558, 0x22AAF0),
    ("runReferenceGroupCams", 5, 0x6585D8, 0x22AE60),
    ("runReferenceGroupCams", 6, 0x658658, 0x22AF80),
    ("runHigherGroupCams", 7, 0x6586D8, 0x22BDF0),
    ("runHigherGroupCams", 8, 0x658758, 0x22BEE0),
    ("runHigherGroupCams", 9, 0x6587D8, 0x22C350),
    ("runHigherGroupCams", 10, 0x658858, 0x22CD00),
    ("runHigherGroupCams", 11, 0x6588D8, 0x22D250),
    ("runHigherGroupCams", 12, 0x658958, 0x22E1D0),
)

TIERS = {
    "28mm": "L16_02130",
    "35mm": "L16_03041",
    "70mm": "L16_03434",
    "150mm": "L16_02285",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u64(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def cstring(blob: bytes, offset: int) -> str:
    end = blob.index(b"\0", offset)
    return blob[offset:end].decode("ascii")


def verify_static(blob: bytes) -> None:
    for method, ordinal, address_point, body in ENTRIES:
        require(u64(blob, address_point - 0x10) == 0, f"{method} $_{ordinal}: offset")
        typeinfo = u64(blob, address_point - 0x08)
        require(typeinfo != 0, f"{method} $_{ordinal}: missing typeinfo")
        name = cstring(blob, u64(blob, typeinfo + 0x08))
        require("CalibDataProcessor" in name, f"{method} $_{ordinal}: owner name")
        require(method in name, f"{method} $_{ordinal}: method name")
        require(f"$_{ordinal}" in name, f"{method} $_{ordinal}: lambda ordinal")
        require(
            "NS3_5StateEv" in name,
            f"{method} $_{ordinal}: return type is not State()",
        )
        require(
            u64(blob, address_point + 0x30) == body,
            f"{method} $_{ordinal}: operator body mismatch",
        )

    require(b"State machine\0" in blob, "missing installed State machine label")
    require(
        b"state function has not been registered.\0" in blob,
        "missing dispatcher registration error",
    )
    # Dispatcher calls function-object slot +0x30 and stores EAX to State slot.
    require(
        blob[0x22F3F6 : 0x22F403]
        == bytes.fromhex("488b07488b4030ffd041890424"),
        "dispatcher call/store instruction bytes changed",
    )


def verify_runtime() -> None:
    expected_bodies = {body for _, _, _, body in ENTRIES}
    for tier, lri in TIERS.items():
        report = json.loads(
            (RUN_ROOT / f"state_machine_return_{tier}.json").read_text()
        )
        require(lri in report["label"], f"{tier}: wrong LRI label")
        require(report["errors"] == [], f"{tier}: probe errors")
        require(report["process"]["exit_status"] == 0, f"{tier}: bad exit")
        require(report["drive_hit_step_cap"] is False, f"{tier}: step cap")
        require(report["counts"]["pre_call_0x22f3f6"] == 38, f"{tier}: pre count")
        require(report["counts"]["post_call_0x22f3ff"] == 38, f"{tier}: post count")
        observed = {
            int(event["function_object"]["slot_0x30_va"])
            for event in report["events"]
            if event["kind"] == "pre_call"
        }
        require(observed == expected_bodies, f"{tier}: State body coverage mismatch")
        hdr = RUN_ROOT / f"state_machine_return_{tier}.hdr"
        require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: bad HDR")
        print(f"{tier}: OK calls=38 bodies=13 output=Radiance")


def main() -> None:
    require(LIBCP.is_file(), f"missing installed libcp: {LIBCP}")
    verify_static(LIBCP.read_bytes())
    print(
        "STATIC: OK owner=lt::CalibDataProcessor "
        "methods=runReferenceGroupCams/runHigherGroupCams callbacks=State()"
    )
    verify_runtime()


if __name__ == "__main__":
    main()
