#!/usr/bin/env python3
import collections
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_promoted_record_watch")

EXPECTED = {
    "70mm": {
        "file": "promoted_watch_70mm.json",
        "hdr": "promoted_watch_70mm.hdr",
        "counts": {
            "gate_before_hits": 1,
            "gate_after_hits": 1,
            "promotion_events": 1,
            "promoted_records_total": 7,
            "watchpoints_armed": 2,
            "watchpoint_hits": 12,
            "state5_target2_hits": 1,
        },
        "promoted_sets": [[31, 49, 64, 68, 77, 78, 108]],
        "armed_indices": [31, 68],
        "va_counts": {
            "0x241764": 4,
            "0x24176b": 2,
            "0x241d2e": 1,
            "0x241d3b": 1,
            "0x2420d8": 1,
            "0x2420ec": 1,
            "0x2420fc": 1,
            "0x242111": 1,
        },
        "state5_va": "0x241d3b",
    },
    "150mm": {
        "file": "promoted_watch_150mm.json",
        "hdr": "promoted_watch_150mm.hdr",
        "counts": {
            "gate_before_hits": 2,
            "gate_after_hits": 2,
            "promotion_events": 1,
            "promoted_records_total": 10,
            "watchpoints_armed": 2,
            "watchpoint_hits": 44,
            "state5_target2_hits": 1,
        },
        "promoted_sets": [[17, 18, 19, 20, 21, 22, 23, 26, 28, 32]],
        "armed_indices": [17, 22],
        "va_counts": {
            "0x241764": 4,
            "0x24176b": 2,
            "0x241d5d": 1,
            "0x241d6a": 1,
            "0x2420df": 1,
            "0x2420e6": 1,
            "0x242103": 1,
            "0x24210a": 1,
            "0x2474d1": 3,
            "0x2474f4": 2,
            "0x247514": 2,
            "0x247534": 3,
            "0x2476be": 22,
        },
        "state5_va": "0x241d6a",
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_hdr(path, tier):
    require(path.read_bytes()[:16].startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance HDR")


def va_counts(samples):
    counts = collections.Counter()
    for sample in samples:
        counts[f"0x{sample.get('libcp_va'):x}"] += 1
    return dict(sorted(counts.items()))


def promoted_sets(gate_after):
    return [
        packet.get("promoted_indices_first32")
        for packet in gate_after
        if packet.get("promoted_count")
    ]


def verify_tier(tier):
    expected = EXPECTED[tier]
    packet = json.loads((ROOT / expected["file"]).read_text())

    require(packet.get("process_exit_status") == 0, f"{tier}: process exit status {packet.get('process_exit_status')}")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: drive hit step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require(packet.get("disable_after_state5") is True, f"{tier}: disable_after_state5 not true")

    counts = packet.get("counts") or {}
    for name, value in expected["counts"].items():
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")

    gate_after = packet.get("gate_after") or []
    require(all(item.get("matched_active_before_vector") is True for item in gate_after), f"{tier}: gate_after vector mismatch")
    require(promoted_sets(gate_after) == expected["promoted_sets"], f"{tier}: promoted index sets mismatch")

    armed_indices = sorted(item.get("record_index") for item in packet.get("armed") or [])
    require(armed_indices == expected["armed_indices"], f"{tier}: armed indices {armed_indices} != {expected['armed_indices']}")
    require(all((item.get("watchpoint_error") is None and item.get("watchpoint_id")) for item in packet.get("armed") or []), f"{tier}: watchpoint arm error")

    samples = packet.get("watchpoint_samples") or []
    require(len(samples) == expected["counts"]["watchpoint_hits"], f"{tier}: sample count mismatch")
    require(va_counts(samples) == expected["va_counts"], f"{tier}: VA bucket mismatch")

    state5_samples = [
        sample
        for sample in samples
        if sample.get("record_now", {}).get("state_0x24") == 5
        and sample.get("record_now", {}).get("target_0x28") == 2
    ]
    require(len(state5_samples) == 1, f"{tier}: expected one state5 target2 sample")
    state5 = state5_samples[0]
    require(f"0x{state5.get('libcp_va'):x}" == expected["state5_va"], f"{tier}: state5 VA mismatch")
    require(state5.get("watched_bytes_at_stop", {}).get("hex") == "0500000002000000", f"{tier}: state5 watched bytes mismatch")

    verify_hdr(ROOT / expected["hdr"], tier)
    print(
        f"{tier}: OK promoted={expected['promoted_sets'][0]} "
        f"armed={armed_indices} state5={expected['state5_va']}"
    )


def main():
    for tier in ("70mm", "150mm"):
        verify_tier(tier)


if __name__ == "__main__":
    main()
