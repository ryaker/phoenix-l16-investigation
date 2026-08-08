#!/usr/bin/env python3
"""Verify the installed public-reference-camera to scorer-family selector."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
EXPECTED_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
SCHEMA = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)
CORPUS = ROOT / "runs/lri_firing_set_census/corpus_firing_sets.json"

WINDOWS = {
    # CaptureStack merge: presence test, LightHeader+0x124 CameraID load,
    # range check, CaptureStack+0x44 store.
    (0xE5545, 0xE555C): "f7c10000010074128bbb24010000e81828050041894544",
    # runReferenceGroupCams construction: CaptureStack+0x44 accessor result
    # copied into the $_1 callback object's +0x10 camera key.
    (0x226CDB, 0x226CE9): "488b3be80d00ecff898514fdffff",
    (0x226DB2, 0x226DE1): "8b8514fdffff488d9d50feffff48899d70feffff488d0d0b16430048898d50feffff4c89a558feffff898560feffff",
    # $_1 camera-key mapping: 8->1, 14->2, all other valid IDs->0.
    (0x229ED8, 0x229EF9): "418b46104983c61083f80e0f94c10fb6c901c983f808b8010000000f45c18945a4",
    # Mode publication into parent+0x450 and transfer to scorer-state+0x234.
    (0x229F68, 0x229F79): "498b3f8b45a4898750040000e847adffff",
    (0x224CEB, 0x224D07): "488d53608b8b50040000488d75e041b8010000004c89f7e879dd0100",
    (0x242AF8, 0x242B01): "8b45d0898334020000",
    # Sole family split: modes 1/2 fall through to family B; mode 0 reaches A.
    (0x244F71, 0x244F84): "418b86340200008d48ff83f9020f83f6010000",
    (0x244FF7, 0x244FFC): "e884350000",
    (0x24517A, 0x245185): "85c04889de0f8527010000",
    (0x245213, 0x245218): "e8882f0000",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    data = LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == EXPECTED_SHA256, "libcp SHA drift")
    for (start, end), expected in WINDOWS.items():
        require(data[start:end].hex() == expected, f"installed window drift 0x{start:x}")

    schema = subprocess.run(
        ["python3", str(SCHEMA)], check=True, text=True, capture_output=True
    ).stdout
    require(
        "5: optional enum image_reference_camera .ltpb.CameraID" in schema,
        "installed LightHeader.image_reference_camera schema missing",
    )
    require("embedded_calibration_proto_schema=OK" in schema, "schema verifier failed")

    corpus = json.loads(CORPUS.read_text())
    wide = "A1,A2,A3,A4,A5,B1,B2,B3,B4,B5"
    tele = "B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6"
    complete = {
        key: value
        for key, value in corpus["reference_firing_set_counts"].items()
        if key.startswith("complete|")
    }
    require(
        complete == {f"complete|0|{wide}": 6078, f"complete|8|{tele}": 3164},
        "complete-corpus public reference/firing invariant",
    )

    print(
        "reference_camera_family_selector=OK "
        "LightHeader.image_reference_camera->CaptureStack+0x44->callback+0x10 "
        "camera8=mode1 camera14=mode2 other=mode0 mode1/2=familyB mode0=familyA"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
