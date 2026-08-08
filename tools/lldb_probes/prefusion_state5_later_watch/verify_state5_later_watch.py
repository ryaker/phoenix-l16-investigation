#!/usr/bin/env python3
import collections
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_state5_later_watch")

EXPECTED = {
    "70mm": {
        "file": "state5_later_70mm.json",
        "hdr": "state5_later_70mm.hdr",
        "counts": {
            "gate_before_hits": 1,
            "gate_after_hits": 1,
            "promotion_events": 1,
            "promoted_records_total": 7,
            "watchpoints_armed": 2,
            "watchpoint_hits": 512,
            "state5_target2_hits": 11,
        },
        "promoted_sets": [[31, 49, 64, 68, 77, 78, 108]],
        "armed_indices": [31, 68],
        "state5_va_counts": {
            "0x241d3b": 1,
            "0x241d85": 1,
            "0x245383": 2,
            "0x24538f": 1,
            "0x25d15c": 4,
            "0x25d16c": 2,
        },
    },
    "150mm": {
        "file": "state5_later_150mm.json",
        "hdr": "state5_later_150mm.hdr",
        "counts": {
            "gate_before_hits": 2,
            "gate_after_hits": 2,
            "promotion_events": 1,
            "promoted_records_total": 9,
            "watchpoints_armed": 1,
            "watchpoint_hits": 256,
            "state5_target2_hits": 5,
            "post_state5_cap_disabled": 0,
        },
        "promoted_sets": [[17, 18, 19, 20, 21, 22, 26, 28, 32]],
        "armed_indices": [17],
        "state5_va_counts": {
            "0x241d3b": 1,
            "0x245383": 1,
            "0x25d15c": 2,
            "0x25d16c": 1,
        },
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_hdr(path, tier):
    require(path.read_bytes()[:16].startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance HDR")


def promoted_sets(gate_after):
    return [
        packet.get("promoted_indices_first32")
        for packet in gate_after
        if packet.get("promoted_count")
    ]


def va_key(sample):
    value = sample.get("libcp_va")
    return "None" if value is None else f"0x{value:x}"


def state5_samples(packet):
    return [
        sample
        for sample in packet.get("watchpoint_samples") or []
        if sample.get("record_now", {}).get("state_0x24") == 5
        and sample.get("record_now", {}).get("target_0x28") == 2
    ]


def verify_tier(tier):
    expected = EXPECTED[tier]
    packet = json.loads((ROOT / expected["file"]).read_text())

    require(packet.get("process_exit_status") == 0, f"{tier}: process exit status {packet.get('process_exit_status')}")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: drive hit step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require(packet.get("disable_after_state5") is False, f"{tier}: expected watchpoints to stay enabled after state5")

    counts = packet.get("counts") or {}
    for name, value in expected["counts"].items():
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")

    require(promoted_sets(packet.get("gate_after") or []) == expected["promoted_sets"], f"{tier}: promoted sets mismatch")
    armed_indices = sorted(item.get("record_index") for item in packet.get("armed") or [])
    require(armed_indices == expected["armed_indices"], f"{tier}: armed indices {armed_indices} != {expected['armed_indices']}")
    require(all((item.get("watchpoint_error") is None and item.get("watchpoint_id")) for item in packet.get("armed") or []), f"{tier}: watchpoint arm error")

    samples = packet.get("watchpoint_samples") or []
    require(len(samples) == expected["counts"]["watchpoint_hits"], f"{tier}: watchpoint sample count mismatch")
    state5 = state5_samples(packet)
    require(len(state5) == expected["counts"]["state5_target2_hits"], f"{tier}: state5 sample count mismatch")
    actual_state5_counts = dict(sorted(collections.Counter(va_key(sample) for sample in state5).items()))
    require(actual_state5_counts == expected["state5_va_counts"], f"{tier}: state5 VA bucket mismatch")
    require(all(sample.get("watched_bytes_at_stop", {}).get("hex") == "0500000002000000" for sample in state5), f"{tier}: state5 sample bytes mismatch")

    verify_hdr(ROOT / expected["hdr"], tier)
    print(
        f"{tier}: OK armed={armed_indices} state5_hits={len(state5)} "
        f"state5_vas={','.join(actual_state5_counts)}"
    )


def main():
    for tier in ("70mm", "150mm"):
        verify_tier(tier)


if __name__ == "__main__":
    main()
