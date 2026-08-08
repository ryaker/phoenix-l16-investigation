#!/usr/bin/env python3
import json
import pathlib
from collections import Counter


WATCH_ROOT = pathlib.Path("runs/prefusion_node_sentinel_downstream_watch")
STATIC_ROOT = pathlib.Path("runs/prefusion_state_22ae60_point_ba")
SENTINEL_HEX = "000080bf000080bf"

EXPECTED_CALLER_COUNTS = {
    "28mm": {
        0x20ADF6: 6,
        0x20BFFA: 6,
        0x20CACA: 6,
        0x20D309: 31,
        0x239C34: 6,
        0x239FD9: 6,
    },
    "35mm": {
        0x20ADF6: 6,
        0x20BFFA: 6,
        0x20CACA: 7,
        0x20D309: 30,
        0x239C34: 6,
        0x239FD9: 6,
    },
    "70mm": {
        0x20ADF6: 6,
        0x20BFFA: 6,
        0x20CACA: 6,
        0x20D309: 0,
        0x239C34: 6,
        0x239FD9: 6,
    },
    "150mm": {
        0x20ADF6: 4,
        0x20BFFA: 4,
        0x20CACA: 5,
        0x20D309: 18,
        0x239C34: 5,
        0x239FD9: 4,
    },
}

STATIC_ANCHORS = {
    "static_disasm_22ae60_22aeb0.log": (
        "0x22ae6e",
        "0x22ae7e",
        "0x22ae87",
        "0x22ae97",
        "0x22ae9c",
    ),
    "static_disasm_20bd60_20c800.log": (
        "0x20bff5",
        "0x20bffa",
        "0x20c020",
        "0x20c114",
        "0x20c154",
        "0x20c2f6",
        "0x20c3e0",
    ),
    "static_disasm_25e4b0_25e5d0.log": (
        "0x25e4f5",
        "0x25e552",
    ),
    "static_disasm_20dbe0_20de10.log": (
        "0x20dca0",
    ),
    "static_disasm_20c800_20d480.log": (
        "0x20cb37",
        "0x20d35e",
    ),
    "static_disasm_20c880_20cfe0_focus.log": (
        "0x20cb37",
    ),
    "static_disasm_20d000_20d380_focus.log": (
        "0x20d35e",
    ),
    "static_disasm_239ac0_23a080.log": (
        "0x239c2f",
        "0x239fd4",
    ),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier):
    hdr = WATCH_ROOT / f"node_sentinel_downstream_{tier}.hdr"
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def load_tier(tier):
    path = WATCH_ROOT / f"node_sentinel_downstream_{tier}.json"
    return json.loads(path.read_text())


def stack_va(sample, index):
    stack = sample.get("stack") or []
    if len(stack) <= index:
        return None
    return stack[index].get("libcp_va")


def validate_static_anchors():
    for filename, anchors in STATIC_ANCHORS.items():
        path = STATIC_ROOT / filename
        require(path.exists(), f"missing static capture {path}")
        text = path.read_text(errors="replace")
        for anchor in anchors:
            require(anchor in text, f"{filename}: missing anchor {anchor}")


def validate_tier(tier):
    packet = load_tier(tier)
    require(packet.get("process_exit_status") == 0, f"{tier}: process did not exit cleanly")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: hit drive step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require_hdr_output(tier)

    samples = packet.get("watchpoint_samples") or []
    counts = Counter(stack_va(sample, 1) for sample in samples)
    expected = EXPECTED_CALLER_COUNTS[tier]
    for caller_va, count in expected.items():
        require(counts.get(caller_va, 0) == count, f"{tier}: caller 0x{caller_va:x} {counts.get(caller_va, 0)} != {count}")
        matching = [sample for sample in samples if stack_va(sample, 1) == caller_va]
        require(len(matching) == count, f"{tier}: caller 0x{caller_va:x} matching sample mismatch")
        for sample in matching:
            pair = sample.get("pair_now") or {}
            require(pair.get("hex") == SENTINEL_HEX, f"{tier}: caller 0x{caller_va:x} non-sentinel pair {pair}")
            require(pair.get("is_sentinel_neg1_neg1") is True, f"{tier}: caller 0x{caller_va:x} sentinel flag false")

    post_copy_samples = [
        sample
        for sample in samples
        if stack_va(sample, 0) is not None
        and 0xE0AE0 <= stack_va(sample, 0) < 0xE0C20
        and stack_va(sample, 1) == 0x20BFFA
    ]
    require(post_copy_samples, f"{tier}: missing 0x20bd60 post-copy samples")

    caller_summary = ",".join(
        f"0x{caller_va:x}:{expected[caller_va]}" for caller_va in sorted(expected)
    )
    print(f"{tier}: OK callers={caller_summary}")


def main():
    validate_static_anchors()
    print(f"static: OK captures={len(STATIC_ANCHORS)}")
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        validate_tier(tier)


if __name__ == "__main__":
    main()
