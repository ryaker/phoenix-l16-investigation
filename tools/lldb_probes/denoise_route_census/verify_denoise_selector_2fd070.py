#!/usr/bin/env python3
"""Verify the Unit-2 0x2fd070 denoise sibling-arm selector."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "runs/denoise_route_census"
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("denoise_selector_static", STATIC_PATH)


def u64(raw: bytes) -> int:
    return struct.unpack("<Q", raw)[0]


def i32s(raw: bytes) -> tuple[int, ...]:
    return struct.unpack("<" + "i" * (len(raw) // 4), raw)


def bytes_at(data: bytes, mapping, va: int, size: int) -> bytes:
    return STATIC.bytes_at(data, mapping, va, size)


def range_hash(data: bytes, mapping, start: int, end: int) -> str:
    return hashlib.sha256(bytes_at(data, mapping, start, end - start)).hexdigest()


def qword(data: bytes, mapping, va: int) -> int:
    return u64(bytes_at(data, mapping, va, 8))


def rip_lea_target(data: bytes, mapping, va: int) -> int:
    raw = bytes_at(data, mapping, va, 7)
    require(raw[:3] == b"\x48\x8d\x35", f"unexpected lea encoding at 0x{va:x}")
    return va + 7 + struct.unpack("<i", raw[3:7])[0]


def verify_static() -> dict:
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == STATIC.LIBCP_SHA256, f"libcp digest changed: {digest}")

    selector_hash = range_hash(data, mapping, 0x2F6420, 0x2F68A0)
    require(
        selector_hash
        == "5f28dc1fdbd035a13e71867718f6865cc1b3c43ebfa70869526f090ae2b7cbb0",
        "selector body changed",
    )
    require(
        range_hash(data, mapping, 0x2FB320, 0x2FC11F)
        == "c6a6926cffdfa8f79b8f6c0caa4a65066ab0b7f42f7ce4e15dc95a1ed65b7861",
        "0x2fb320 body changed",
    )
    require(
        range_hash(data, mapping, 0x2FD070, 0x2FDCE0)
        == "c4660f0f361c2a4e9886d125197181dab9f50b7757c5ce3032197c65f547860a",
        "0x2fd070 body changed",
    )

    false_table_base = 0x2F69EC
    true_table_base = 0x2F6A08
    false_targets = tuple(
        false_table_base + off for off in i32s(bytes_at(data, mapping, false_table_base, 28))
    )
    true_targets = tuple(
        true_table_base + off for off in i32s(bytes_at(data, mapping, true_table_base, 28))
    )
    require(
        false_targets
        == (
            0x2F6712,
            0x2F690E,
            0x2F6791,
            0x2F690E,
            0x2F6882,
            0x2F690E,
            0x2F680A,
        ),
        f"false-arm jump table changed: {false_targets!r}",
    )
    require(
        true_targets
        == (
            0x2F64C4,
            0x2F66C0,
            0x2F6543,
            0x2F66C0,
            0x2F6641,
            0x2F66C0,
            0x2F65C2,
        ),
        f"true-arm jump table changed: {true_targets!r}",
    )

    vtable_workers = {
        0x65A768: qword(data, mapping, 0x65A768 + 0x30),
        0x65A868: qword(data, mapping, 0x65A868 + 0x30),
    }
    require(vtable_workers[0x65A768] == 0x2FB320, "0x65a768 worker slot changed")
    require(vtable_workers[0x65A868] == 0x2FD070, "0x65a868 worker slot changed")

    unsupported = STATIC.cstring(data, mapping, rip_lea_target(data, mapping, 0x2F66D5))
    require(
        b"Unsupported bilateral kernel size!" in unsupported,
        "selector unsupported-size string changed",
    )

    return {
        "libcp_sha256": digest,
        "selector_hash": selector_hash,
        "false_table_targets": false_targets,
        "true_table_targets": true_targets,
        "vtable_workers": vtable_workers,
    }


def load_report(stem: str) -> dict:
    path = RUN_ROOT / f"{stem}.json"
    require(path.exists(), f"missing report {path}")
    report = json.loads(path.read_text())
    require(report["process"]["state"] == "exited", f"{stem}: process state")
    require(report["process"]["exit_status"] == 0, f"{stem}: process exit")
    require(not report["drive_hit_step_cap"], f"{stem}: drive cap")
    require(not report["errors"], f"{stem}: errors {report['errors']}")
    return report


def nonzero(report: dict) -> set[str]:
    return {name for name, value in report["counts"].items() if value}


def descriptor_words(sample: dict, reg: str) -> list[int]:
    return sample["packet"]["descriptors"][reg].get("i32") or []


def helper_kernel_words(report: dict) -> Counter[int]:
    out: Counter[int] = Counter()
    for sample in report["samples"]:
        if sample["site"] == "helper_chain_0x2f53d0":
            words = descriptor_words(sample, "r8")
            require(words, "helper sample missing r8 config")
            out[words[0]] += 1
    return out


def helper_rcx_words(report: dict) -> Counter[tuple[int, ...]]:
    out: Counter[tuple[int, ...]] = Counter()
    for sample in report["samples"]:
        if sample["site"] == "helper_chain_0x2f53d0":
            out[tuple(descriptor_words(sample, "rcx")[:12])] += 1
    return out


def selector_args(report: dict) -> Counter[tuple[int, int]]:
    out: Counter[tuple[int, int]] = Counter()
    for sample in report["samples"]:
        if sample["site"] == "callback_selector_0x2f6420":
            regs = sample["registers"]
            out[(int(regs["r8"]), int(regs["r9"]))] += 1
    return out


def worker_vtables(report: dict, site: str) -> Counter[tuple[int | None, int | None]]:
    out: Counter[tuple[int | None, int | None]] = Counter()
    for sample in report["samples"]:
        if sample["site"] == site:
            callable_packet = sample["packet"]["callable_rdi"]
            out[
                (
                    callable_packet.get("vtable_va"),
                    callable_packet.get("slot_0x30_va"),
                )
            ] += 1
    return out


def stack_contains(report: dict, site: str, va: int) -> bool:
    for sample in report["samples"]:
        if sample["site"] != site:
            continue
        if any(frame.get("libcp_va") == va for frame in sample["stack"]):
            return True
    return False


def verify_runtime() -> dict:
    unit1 = load_report("unit1_35mm_denoise_selector")
    unit2 = load_report("unit2_35mm_denoise_selector")

    common = {
        "helper_chain_0x2f53d0",
        "callback_selector_0x2f6420",
        "bilateral_arm_0x2fb320",
        "ImageDenoiseNLM_positive_0x3066d0",
        "PatchNLM_adapter_0x3070a0",
        "PatchNLM_body_0x3070e0",
        "PatchNLM_normalize_0x307d90",
    }
    require(nonzero(unit1) == common, f"Unit-1 nonzero set changed: {nonzero(unit1)}")
    require(
        nonzero(unit2) == common | {"bilateral_arm_0x2fd070"},
        f"Unit-2 nonzero set changed: {nonzero(unit2)}",
    )

    unit1_helpers = helper_kernel_words(unit1)
    unit2_helpers = helper_kernel_words(unit2)
    require(set(unit1_helpers) == {5}, f"Unit-1 helper kernels changed: {unit1_helpers}")
    require(
        {5, 9}.issubset(set(unit2_helpers)),
        f"Unit-2 helper kernels missing 5/9: {unit2_helpers}",
    )

    require(selector_args(unit1) == Counter({(5, 0): 256}), "Unit-1 selector args changed")
    require(
        (0x65A768, 0x2FB320) in worker_vtables(unit1, "bilateral_arm_0x2fb320"),
        "Unit-1 0x2fb320 vtable/worker mismatch",
    )
    require(
        (0x65A768, 0x2FB320) in worker_vtables(unit2, "bilateral_arm_0x2fb320"),
        "Unit-2 0x2fb320 vtable/worker mismatch",
    )
    require(
        (0x65A868, 0x2FD070) in worker_vtables(unit2, "bilateral_arm_0x2fd070"),
        "Unit-2 0x2fd070 vtable/worker mismatch",
    )
    require(
        stack_contains(unit2, "bilateral_arm_0x2fd070", 0x2F6863),
        "Unit-2 0x2fd070 samples do not return through selector case 0x2f680a",
    )
    require(
        stack_contains(unit1, "bilateral_arm_0x2fb320", 0x2F67E7),
        "Unit-1 0x2fb320 samples do not return through selector case 0x2f6791",
    )

    # The existing four-focal route census remains the broader Unit-1 guard for
    # zero hits at 0x2fd070 across the canonical focal set.
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        report = load_report(f"unit1_{tier}_denoise_algo")
        require(
            int(report["counts"].get("bilateral_arm_0x2fd070", 0)) == 0,
            f"Unit-1 {tier} unexpectedly hit 0x2fd070",
        )

    return {
        "unit1_helper_kernels": dict(unit1_helpers),
        "unit2_helper_kernels": dict(unit2_helpers),
        "unit1_helper_rcx": dict(helper_rcx_words(unit1)),
        "unit2_helper_rcx": dict(helper_rcx_words(unit2)),
    }


def main() -> None:
    static = verify_static()
    runtime = verify_runtime()
    print(
        "denoise_selector_2fd070=OK "
        f"libcp={static['libcp_sha256']} "
        f"dispatch_false=size5->0x2fb320,size9->0x2fd070 "
        f"unit1_helper_kernels={runtime['unit1_helper_kernels']} "
        f"unit2_helper_kernels={runtime['unit2_helper_kernels']}"
    )


if __name__ == "__main__":
    main()
