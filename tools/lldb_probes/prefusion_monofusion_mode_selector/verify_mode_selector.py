#!/usr/bin/env python3
"""Verify MonoFusion mode selection and canonical profile-3 exclusion."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs"
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/"
    "libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def call_target(data: bytes, address: int) -> int:
    require(data[address] == 0xE8, f"0x{address:x} is not a direct call")
    return address + 5 + struct.unpack_from("<i", data, address + 1)[0]


def load_report(path: Path) -> dict:
    require(path.is_file(), f"missing report {path}")
    report = json.loads(path.read_text())
    require(not report["errors"], f"probe errors in {path}: {report['errors']}")
    return report


def verify_hdr(path: Path) -> None:
    require(path.is_file(), f"missing completed HDR {path}")
    with path.open("rb") as handle:
        header = b""
        while b"\n\n" not in header:
            chunk = handle.read(256)
            require(chunk, f"truncated HDR header {path}")
            header += chunk
        resolution = header.split(b"\n\n", 1)[1].splitlines()[0]
    require(
        re.fullmatch(rb"-Y 7824 \+X 10432", resolution) is not None,
        f"wrong HDR dimensions in {path}: {resolution!r}",
    )


def verify_static(data: bytes) -> None:
    windows = {
        (0x40B2B0, 0x40B320):
            "2078efb4f54727495d0eacb57e3e7a782f6319d89bfc2e7e3b7d9d4050a0121e",
        (0x4066F8, 0x40677C):
            "0bafe14e8c38af4ba6ed10e748be5e0a2e7e7d0c06379b24a3b4b83ce46753bc",
        (0x1B1360, 0x1B13B3):
            "498ef8b067a17d6f834fc517381798cd5c75e106052897cdaa125d19ccb6a25a",
        (0x1B37A0, 0x1B3B90):
            "fd7050fe98d956bb6af528836e48bfb7666960f0829b93ac946b9cb15cd16bbc",
        (0x40B1D0, 0x40B27C):
            "8a4a859bf74f36b4a8b6cc4ecaf0c5926cc8c2eecfb664ffcb9540ccb403d1f3",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(data[start:end]).hexdigest()
        require(actual == expected, f"static window drift 0x{start:x}..0x{end:x}")

    require(call_target(data, 0x406746) == 0x40B2B0, "selector call changed")
    require(call_target(data, 0x40676B) == 0x1B17B0, "constructor call changed")
    require(call_target(data, 0x1B3599) == 0x1B37A0, "worker call changed")
    require(call_target(data, 0x1B3AAE) == 0x19F790, "mode-1 call changed")
    require(call_target(data, 0x1B3B61) == 0x1A3C00, "mode-0 call changed")
    require(
        data[0x1B1389:0x1B138C] == bytes.fromhex("458806"),
        "constructor mode-byte store changed",
    )
    require(
        data[0x1B39C6:0x1B39CB] == bytes.fromhex("803b007425"),
        "worker mode branch changed",
    )
    require(data.count(b"Invalid Renderer profile!") == 1, "profile guard changed")
    require(
        b"PipelineBase12Demosaicking" in data,
        "installed PipelineBase::Demosaicking RTTI missing",
    )


def verify_profile_matrix() -> dict:
    expected = {
        0: (0, 1, 0, 0, None),
        1: (1, 1, 1, 0, 48),
        2: (2, 1, 1, 0, 48),
        3: (3, 1, 0, 282, 0),
    }
    output = {}
    base = RUNS / "prefusion_monofusion_mode_selector"
    for profile, (enum_value, byte_4, mode, mode0, mode1) in expected.items():
        report = load_report(base / f"profile{profile}.json")
        require(len(report["selector_calls"]) == 1, f"profile {profile} selector count")
        selector = report["selector_calls"][0]
        require(selector["enum_i32"] == enum_value, f"profile {profile} enum")
        require(selector["byte_4"] == byte_4, f"profile {profile} byte 4")
        require(selector["returned_mode"] == mode, f"profile {profile} return")
        require(
            [row["stored_mode"] for row in report["constructor_stores"]] == [mode],
            f"profile {profile} constructor mode",
        )
        if profile:
            require(set(report["worker_modes"]) == {mode}, f"profile {profile} worker")
            require(report["mode0_calls"] == mode0, f"profile {profile} mode-0 count")
            require(report["mode1_calls"] == mode1, f"profile {profile} mode-1 count")
            verify_hdr(base / f"profile{profile}.hdr")
        else:
            require(not report["worker_modes"], "profile 0 unexpectedly reached worker")
            require(report["mode0_calls"] == report["mode1_calls"] == 0, "profile 0 calls")
        output[str(profile)] = {
            "config": [enum_value, byte_4],
            "mode": mode,
            "mode0_calls": report["mode0_calls"],
            "mode1_calls": report["mode1_calls"],
        }
    return output


def verify_canonical_scope() -> dict:
    wide = {}
    worker_root = RUNS / "prefusion_monofusion_worker"
    for label in ("unit1_28mm", "unit1_35mm", "unit2_28mm"):
        report = load_report(worker_root / f"{label}.json")
        require(report["worker_entries"], f"no worker entries for {label}")
        require(
            {row["mode_0x00"] for row in report["worker_entries"]} == {0},
            f"nonzero canonical wide mode in {label}",
        )
        require(not report["mode1_calls_0x19f790"], f"mode 1 reached in {label}")
        require(report["mode0_calls_0x1a3c00"], f"mode 0 absent in {label}")
        wide[label] = len(report["mode0_calls_0x1a3c00"])

    tele = {}
    identity_root = RUNS / "prefusion_monofusion_identity"
    for label in ("unit1_70mm", "unit1_150mm", "unit2_70mm"):
        report = load_report(identity_root / f"{label}.json")
        for key in (
            "field20_stores",
            "initialize_entries",
            "initialize_commits",
            "process_entries",
            "process_returns",
            "wide_adapter_calls",
        ):
            require(not report[key], f"tele MonoFusion activity {label}:{key}")
        require(report["tele_adapter_calls"], f"tele direct adapter absent in {label}")
        tele[label] = len(report["tele_adapter_calls"])
    return {"wide_mode0_calls": wide, "tele_direct_adapter_calls": tele}


def main() -> None:
    data = LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    verify_static(data)
    matrix = verify_profile_matrix()
    canonical = verify_canonical_scope()
    report = {
        "libcp_sha256": LIBCP_SHA256,
        "profile_matrix": matrix,
        "canonical_scope": canonical,
    }
    output = RUNS / "prefusion_monofusion_mode_selector/verification.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        "PASS MonoFusion selector "
        "profiles=0->0,1->1,2->1,3->0 "
        "canonical_wide=mode0 canonical_tele=no-MonoFusion"
    )
    print(f"report={output}")


if __name__ == "__main__":
    main()
