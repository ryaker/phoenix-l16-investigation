#!/usr/bin/env python3
"""Create a run-local libcp whose IRAMP candidate score returns zero immediately."""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
EXPECTED_SHA256 = (
    "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
)
PATCH_VA = 0x36CDE0
PATCH = bytes.fromhex("0f57c0c3")  # xorps xmm0,xmm0; ret


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("zero_score_static_helpers", STATIC_PATH)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} OUTPUT_LIBCP")
    output = Path(sys.argv[1])
    source = STATIC.LIBCP
    original = source.read_bytes()
    require(hashlib.sha256(original).hexdigest() == EXPECTED_SHA256, "source SHA")
    mapping = STATIC.segments(original)
    offset = STATIC.file_offset(mapping, PATCH_VA)
    require(
        original[offset : offset + 4] == bytes.fromhex("554889e5"),
        "score prologue changed",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)
    patched = bytearray(output.read_bytes())
    patched[offset : offset + len(PATCH)] = PATCH
    output.write_bytes(patched)

    changed = [
        index for index, (old, new) in enumerate(zip(original, patched)) if old != new
    ]
    require(changed == list(range(offset, offset + 4)), f"changed bytes: {changed}")
    print(f"source_sha256={EXPECTED_SHA256}")
    print(f"patch_va=0x{PATCH_VA:x} file_offset=0x{offset:x}")
    print(f"old={original[offset:offset+4].hex()} new={PATCH.hex()}")
    print(f"unsigned_patched_sha256={hashlib.sha256(patched).hexdigest()}")
    print("zero_score_libcp_patch=OK")


if __name__ == "__main__":
    main()
