#!/usr/bin/env python3
"""Verify the installed and runtime proof for index-5 scheduling nondeterminism."""

from __future__ import annotations

import array
import hashlib
import json
import re
import struct
import subprocess
from collections import defaultdict
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
RMW_BEGIN = 0x277A06
RMW_END = 0x277A16
RMW_SHA256 = "7228de99120380b22f6075397f0d8072d558d80ac9e8c772af2f182de2bc76ff"
EXEC_BEGIN = 0x2D30
EXEC_END = 0x2DE5
EXEC_SHA256 = "675ff90a57802a8e0583eb941d64210e1c578940c41f47ab2dca9b94ca466691"

RUN = ROOT / "runs" / "index5_nondeterminism"
VECTOR_RUN = ROOT / "runs" / "codex_276860_payload_vector_formula"
BASELINE = ROOT / "runs" / "reference_stage_maps" / "campaign"

CONTROLLED = {
    "Unit-1 28mm": (
        ("u1_28_serial2d30_r1", "u1_28_serial2d30_r2"),
        "bdc5699206c440db724c65cc869496ba0102dc5fbd26298235b780cf482b0c1b",
    ),
    "Unit-1 150mm": (
        ("u1_150_serial2d30_r1", "u1_150_serial2d30_r2"),
        "449328abd0b6674b3cba3eb68dff8f497f588feca4cf425bf1a8d6f5f6f96260",
    ),
    "Unit-2 70mm": (
        ("u2_70_serial2d30_r1", "u2_70_serial2d30_r2", "u2_70_serial2d30_r3"),
        "b7f734aa6f91c2cf337fac520227e3d14f78253d98c8495a25b28ae7f6a5e2d9",
    ),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16_map(path: Path) -> array.array[int]:
    data = path.read_bytes()
    require(len(data) == 6_489_600, f"{path}: map size {len(data)}")
    values = array.array("H")
    values.frombytes(data)
    require(len(values) == 3_244_800, f"{path}: word count")
    return values


def metrics(first: array.array[int], second: array.array[int]) -> tuple[float, float, float, int]:
    require(len(first) == len(second), "map length mismatch")
    equal = 0
    within4 = 0
    total = 0
    maximum = 0
    for left, right in zip(first, second):
        delta = abs(left - right)
        equal += delta == 0
        within4 += delta <= 4
        total += delta
        maximum = max(maximum, delta)
    count = len(first)
    return equal / count, within4 / count, total / count, maximum


def verify_static() -> None:
    blob = LIBCP.read_bytes()
    require(sha256(blob) == LIBCP_SHA256, "libcp SHA drift")
    require(sha256(blob[RMW_BEGIN:RMW_END]) == RMW_SHA256, "RMW window drift")
    require(sha256(blob[EXEC_BEGIN:EXEC_END]) == EXEC_SHA256, "executor window drift")

    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    rmw = {
        insn.address: (insn.mnemonic, insn.op_str, bytes(insn.bytes))
        for insn in decoder.disasm(blob[RMW_BEGIN:RMW_END], RMW_BEGIN)
    }
    require(rmw[0x277A06][:2] == ("movdqu", "xmm5, xmmword ptr [r9 + rdx*2]"), "RMW load")
    require(rmw[0x277A0C][:2] == ("paddusw", "xmm5, xmm0"), "RMW add")
    require(rmw[0x277A10][:2] == ("movdqu", "xmmword ptr [r9 + rdx*2], xmm5"), "RMW store")
    require(all(0xF0 not in row[2] for row in rmw.values()), "unexpected lock prefix")

    executor = {
        insn.address: (insn.mnemonic, insn.op_str)
        for insn in decoder.disasm(blob[EXEC_BEGIN:EXEC_END], EXEC_BEGIN)
    }
    anchors = {
        0x2D49: ("mov", "rdi, qword ptr [rdi]"),
        0x2D4C: ("test", "rdi, rdi"),
        0x2D4F: ("je", "0x2d6c"),
        0x2D67: ("jmp", "0x37c0"),
        0x2D6C: ("test", "rcx, rcx"),
        0x2D6F: ("je", "0x2d94"),
        0x2DBA: ("mov", "rdi, qword ptr [r14 + 0x20]"),
        0x2DCC: ("call", "qword ptr [rax + 0x30]"),
        0x2DCF: ("inc", "ebx"),
        0x2DD4: ("jl", "0x2db0"),
    }
    for address, expected in anchors.items():
        require(executor.get(address) == expected, f"executor anchor 0x{address:x}")


def verify_payload_race() -> dict[str, tuple[int, list[int]]]:
    results = {}
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        path = VECTOR_RUN / f"vector_formula_{tier}.json"
        packet = json.loads(path.read_text())
        by_address: dict[int, set[int]] = defaultdict(set)
        for sample in packet["watchpoint_samples"]:
            require(sample["libcp_va"] == 0x277A16, f"{tier}: store PC")
            address = sample["vector_context"]["addresses"]["payload_r9_plus_2rdx"]
            by_address[address].add(sample["thread_id"])
        shared = [(address, sorted(threads)) for address, threads in by_address.items() if len(threads) >= 2]
        require(shared, f"{tier}: no same-address multi-thread payload writes")
        results[tier] = shared[0]
    return results


def verify_live_overlap() -> tuple[int, int, int, int]:
    text = (RUN / "u2_70_mode8_overlap_indexed" / "mode8_overlap.txt").read_text()
    total = int(re.search(r"^total_calls=(\d+)$", text, re.MULTILINE).group(1))
    global_max = int(re.search(r"^global_max_active=(\d+)$", text, re.MULTILINE).group(1))
    match = re.search(
        r"^object\[\d+\]=0x[0-9a-f]+ stereo_index=5 max_active=(\d+) "
        r"first_thread=(\d+) second_thread=(\d+)$",
        text,
        re.MULTILINE,
    )
    require(match is not None, "missing index-5 overlap row")
    active, first, second = map(int, match.groups())
    require(total > 0 and global_max > 1 and active > 1, "no live worker overlap")
    require(first != 0 and second != 0 and first != second, "no distinct index-5 threads")
    return total, global_max, active, len({first, second})


def verify_baseline() -> tuple[float, float, float, int]:
    first = u16_map(BASELINE / "u2_70mm_a_r1" / "index5_hypothesis_index.u16le")
    second = u16_map(BASELINE / "u2_70mm_a_r2" / "index5_hypothesis_index.u16le")
    result = metrics(first, second)
    require(abs(result[0] - 0.5287882149901381) < 1e-15, "baseline exact fraction")
    require(abs(result[1] - 0.9436076183431953) < 1e-15, "baseline within4")
    require(abs(result[2] - 1.1026919995069033) < 1e-15, "baseline MAE")
    require(result[3] == 22, "baseline max delta")
    return result


def verify_failed_controls() -> dict[str, tuple[float, float, float, int]]:
    pairs = {
        "HL_NUM_THREADS=1": ("u2_70_stage_hl1_r1", "u2_70_stage_hl1_r2"),
        "mode8 mutex": ("u2_70_serial_only_r1", "u2_70_serial_only_r2"),
        "HL1+mutex+frozen calibration": ("u2_70_both_controls_r1", "u2_70_both_controls_r2"),
    }
    results = {}
    for label, (left, right) in pairs.items():
        result = metrics(
            u16_map(RUN / left / "index5_hypothesis_index.u16le"),
            u16_map(RUN / right / "index5_hypothesis_index.u16le"),
        )
        require(result[0] < 1.0, f"{label}: unexpectedly exact")
        results[label] = result
    return results


def verify_controlled_maps() -> dict[str, tuple[str, list[int]]]:
    results = {}
    for label, (stems, expected_hash) in CONTROLLED.items():
        hashes = []
        calls = []
        for stem in stems:
            path = RUN / stem / "index5_hypothesis_index.u16le"
            data = path.read_bytes()
            require(len(data) == 6_489_600, f"{stem}: map size")
            hashes.append(sha256(data))
            report = (RUN / stem / "executor_serial.txt").read_text()
            calls.append(int(re.search(r"serial_calls=(\d+)", report).group(1)))
        require(set(hashes) == {expected_hash}, f"{label}: controlled hashes {hashes}")
        require(all(count > 0 for count in calls), f"{label}: no serial calls")
        results[label] = (expected_hash, calls)
    return results


def normalize_geometry(data: bytes) -> bytes:
    stride = 340
    require(len(data) % stride == 0, "geometry packet size")
    output = bytearray()
    for offset in range(0, len(data), stride):
        packet = data[offset : offset + stride]
        built = packet[176:]
        require(len(built) == 0xA4, "built record size")
        output.extend(packet[:176])
        output.extend(built[:0x68])
        output.extend(built[0x80:])
    return bytes(output)


def verify_pre_g42_control() -> tuple[list[int], list[int]]:
    first = RUN / "u2_70_g42_serial2d30_r1"
    second = RUN / "u2_70_g42_serial2d30_r2"
    exact_files = [
        "create_stereo_banks.bin",
        "current_bank_writes.bin",
        "image0.rgba8",
        "image1.rgba8",
        "image2.rgba8",
        "image3.rgba8",
        "image4.rgba8",
        "local_curve.u16le",
        "lookup.f32le",
        "projection_records.bin",
        "report.json",
    ]
    for name in exact_files:
        require((first / name).read_bytes() == (second / name).read_bytes(), f"pre-G42 {name}")
    require(
        normalize_geometry((first / "geometry_banks.bin").read_bytes())
        == normalize_geometry((second / "geometry_banks.bin").read_bytes()),
        "normalized geometry banks",
    )

    writes = (first / "current_bank_writes.bin").read_bytes()
    require(len(writes) % 100 == 0, "current-bank packet size")
    parent = []
    ba = []
    for offset in range(0, len(writes), 100):
        _sequence, camera_id, caller = struct.unpack_from("<IIQ", writes, offset)
        if caller == 0x217BC3:
            parent.append(camera_id)
        elif caller == 0x23D392:
            ba.append(camera_id)
    require(parent == [6, 9, 5, 7], f"controlled parent writes {parent}")
    require(ba == [5, 6, 7, 9, 5, 6, 7, 9], f"controlled BA writes {ba}")
    return parent, ba


def verify_parent_flip() -> tuple[dict, dict]:
    packets = []
    for stem in ("u2_70_parent_r1", "u2_70_parent_r2"):
        report = json.loads((RUN / stem / "parent_decision.json").read_text())
        packet = next(row for row in report["packets"] if row["camera_id"] == 6)
        packets.append(packet)
    accepted, rejected = packets
    require(accepted["observed_accepted"] is True, "key 6 accepted draw")
    require(accepted["winner"]["index"] == 11, "key 6 accepted winner")
    require(accepted["winner"]["score"]["hex"] == "5c674d3f", "key 6 accepted score")
    require(accepted["winner_side"]["hex"] == "00000000", "key 6 accepted side")
    require(rejected["observed_accepted"] is False, "key 6 rejected draw")
    require(rejected["winner"]["score"]["hex"] == "00007041", "key 6 reject score")
    require(rejected["winner_side"]["hex"] == "0000803f", "key 6 reject side")
    return accepted, rejected


def verify_rng_exclusion() -> None:
    path = (
        ROOT
        / "runs"
        / "index5_nondeterminism_random_device"
        / "fixed_seed_r2"
        / "random_device_report.json"
    )
    report = json.loads(path.read_text())
    require(report["fixed_seed"] == 0x12345678, "random-device seed")
    require(report["call_count"] == 0, "random_device reached before G42")


def main() -> None:
    verify_static()
    subprocess.run(
        ["python3", "tools/lldb_probes/g43_direction_vectors/verify_g43_directions.py"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    shared = verify_payload_race()
    total, global_max, index5_max, thread_count = verify_live_overlap()
    baseline = verify_baseline()
    failed = verify_failed_controls()
    controlled = verify_controlled_maps()
    parent, ba = verify_pre_g42_control()
    accepted, rejected = verify_parent_flip()
    verify_rng_exclusion()

    print(
        f"static=OK libcp={LIBCP_SHA256} rmw={RMW_SHA256} executor={EXEC_SHA256} "
        "scratch_init=line/min:2000,pixel:0"
    )
    for tier, (address, threads) in shared.items():
        print(f"{tier}: shared_payload=0x{address:x} threads={threads}")
    print(
        f"Unit-2 70mm overlap: calls={total} global_max={global_max} "
        f"index5_max={index5_max} distinct_threads>={thread_count}"
    )
    print(
        "baseline Unit-2 70mm: exact={:.9%} within4={:.9%} mae={:.9f} max={}".format(
            *baseline
        )
    )
    for label, result in failed.items():
        print(f"failed_control {label}: exact={result[0]:.9%} within4={result[1]:.9%} mae={result[2]:.9f}")
    for label, (digest, calls) in controlled.items():
        print(f"controlled {label}: repeats={len(calls)} sha256={digest} serial_calls={calls}")
    print(f"pre_G42_control: images=5 exact numeric_geometry=exact parent={parent} ba={ba}")
    print(
        "parent_key6_flip: accepted_bits={}/{} rejected_bits={}/{}".format(
            accepted["winner"]["score"]["hex"],
            accepted["winner_side"]["hex"],
            rejected["winner"]["score"]["hex"],
            rejected["winner_side"]["hex"],
        )
    )
    print("random_device_pre_G42_calls=0 result=PROVEN_SCHEDULING_NONDETERMINISM_SUPPRESSIBLE")


if __name__ == "__main__":
    main()
