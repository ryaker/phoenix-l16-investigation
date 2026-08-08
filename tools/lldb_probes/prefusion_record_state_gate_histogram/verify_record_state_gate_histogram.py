#!/usr/bin/env python3
import collections
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_record_state_gate_histogram")

EXPECTED = {
    "28mm": {
        "file": "custody_state_28mm.json",
        "hdr": "custody_state_28mm.hdr",
        "family": "a",
        "gate_calls": 4,
        "record_count": 151,
        "before": {"1:0": 60, "3:2": 346, "4:2": 198},
        "after": {"1:0": 60, "3:2": 346, "4:2": 198},
        "counts": {
            "family_a_gate_before_2484e4": 4,
            "family_a_gate_after_2484e9": 4,
            "family_b_gate_before_2488b9": 0,
            "family_b_gate_after_2488be": 0,
            "selector_entry_241fd0": 31,
            "promoter_entry_2416d0": 26,
            "promoter_direct_state5_store_241828": 0,
            "selector_ge3_state5_store_2422a6": 266,
            "selector_state4_state5_store_242306": 0,
        },
        "disabled_after_cap": [],
    },
    "35mm": {
        "file": "custody_state_35mm.json",
        "hdr": "custody_state_35mm.hdr",
        "family": "a",
        "gate_calls": 4,
        "record_count": 154,
        "before": {"1:0": 12, "3:2": 359, "4:2": 245},
        "after": {"1:0": 12, "3:2": 359, "4:2": 245},
        "counts": {
            "family_a_gate_before_2484e4": 4,
            "family_a_gate_after_2484e9": 4,
            "family_b_gate_before_2488b9": 0,
            "family_b_gate_after_2488be": 0,
            "selector_entry_241fd0": 31,
            "promoter_entry_2416d0": 29,
            "promoter_direct_state5_store_241828": 0,
            "selector_ge3_state5_store_2422a6": 29,
            "selector_state4_state5_store_242306": 4,
        },
        "disabled_after_cap": [],
    },
    "70mm": {
        "file": "custody_state_70mm.json",
        "hdr": "custody_state_70mm.hdr",
        "family": "b",
        "gate_calls": 3,
        "record_count": 169,
        "before": {"1:0": 13, "3:1": 195, "3:2": 19, "4:1": 278, "4:2": 2},
        "after": {"1:0": 13, "3:1": 195, "4:1": 278, "4:2": 21},
        "counts": {
            "family_a_gate_before_2484e4": 0,
            "family_a_gate_after_2484e9": 0,
            "family_b_gate_before_2488b9": 3,
            "family_b_gate_after_2488be": 3,
            "selector_entry_241fd0": 27,
            "promoter_entry_2416d0": 23,
            "promoter_direct_state5_store_241828": 0,
            "selector_ge3_state5_store_2422a6": 512,
            "selector_state4_state5_store_242306": 0,
        },
        "disabled_after_cap": ["selector_ge3_state5_store_2422a6"],
    },
    "150mm": {
        "file": "custody_state_150mm.json",
        "hdr": "custody_state_150mm.hdr",
        "family": "b",
        "gate_calls": 3,
        "record_count": 34,
        "before": {"1:0": 2, "3:1": 36, "3:2": 12, "4:1": 52},
        "after": {"1:0": 2, "3:1": 36, "4:1": 52, "4:2": 12},
        "counts": {
            "family_a_gate_before_2484e4": 0,
            "family_a_gate_after_2484e9": 0,
            "family_b_gate_before_2488b9": 3,
            "family_b_gate_after_2488be": 3,
            "selector_entry_241fd0": 26,
            "promoter_entry_2416d0": 18,
            "promoter_direct_state5_store_241828": 0,
            "selector_ge3_state5_store_2422a6": 116,
            "selector_state4_state5_store_242306": 8,
        },
        "disabled_after_cap": [],
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def aggregate(entries):
    result = collections.Counter()
    for entry in entries:
        hist = entry.get("histogram") or {}
        result.update(hist.get("state_target_counts") or {})
    return dict(sorted(result.items()))


def verify_hdr(path, tier):
    require(path.read_bytes()[:16].startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance HDR")


def verify_hist_entry(tier, entry, family, record_count):
    require(entry.get("family") == family, f"{tier}: family mismatch")
    hist = entry.get("histogram") or {}
    vector = hist.get("vector") or {}
    require(hist.get("read_ok") is True, f"{tier}: histogram read failed")
    require(hist.get("records_truncated") is False, f"{tier}: histogram truncated")
    require(hist.get("records_scanned") == record_count, f"{tier}: records_scanned mismatch")
    require(vector.get("record_count") == record_count, f"{tier}: vector record_count mismatch")
    require(vector.get("stride") == 44, f"{tier}: vector stride mismatch")
    require(vector.get("byte_len") == record_count * 44, f"{tier}: vector byte_len mismatch")
    require(vector.get("byte_len_mod_stride") == 0, f"{tier}: vector byte alignment mismatch")


def verify_tier(tier):
    expected = EXPECTED[tier]
    packet = json.loads((ROOT / expected["file"]).read_text())

    process = packet.get("process") or {}
    require(process.get("exit_status") == 0, f"{tier}: process exit status {process.get('exit_status')}")
    require(process.get("state") == "exited", f"{tier}: process state {process.get('state')}")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: drive hit step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")

    counts = packet.get("counts") or {}
    for name, value in expected["counts"].items():
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")
    require(packet.get("disabled_after_cap") == expected["disabled_after_cap"], f"{tier}: disabled_after_cap mismatch")

    known = packet.get("known_vectors") or {}
    require(len(known) == 1, f"{tier}: expected exactly one known vector")
    known_record = next(iter(known.values()))
    require(known_record.get("family") == expected["family"], f"{tier}: known vector family mismatch")
    require(known_record.get("record_count") == expected["record_count"], f"{tier}: known vector record_count mismatch")

    before = packet.get("gate_before") or []
    after = packet.get("gate_after") or []
    require(len(before) == expected["gate_calls"], f"{tier}: gate_before count mismatch")
    require(len(after) == expected["gate_calls"], f"{tier}: gate_after count mismatch")

    for entry in before:
        verify_hist_entry(tier, entry, expected["family"], expected["record_count"])
    for entry in after:
        verify_hist_entry(tier, entry, expected["family"], expected["record_count"])
        require(entry.get("matched_active_vector") is True, f"{tier}: gate_after did not match active vector")
        require(entry.get("vector_addr") == known_record.get("vector_addr"), f"{tier}: gate_after vector address mismatch")

    require(aggregate(before) == expected["before"], f"{tier}: before aggregate mismatch")
    require(aggregate(after) == expected["after"], f"{tier}: after aggregate mismatch")

    require(not packet.get("selector_entries"), f"{tier}: exact-vector selector entries were not empty")
    require(not packet.get("promoter_entries"), f"{tier}: exact-vector promoter entries were not empty")
    require(not packet.get("state_stores"), f"{tier}: exact-vector state stores were not empty")

    verify_hdr(ROOT / expected["hdr"], tier)

    promoted = expected["before"].get("3:2", 0) - expected["after"].get("3:2", 0)
    print(
        f"{tier}: OK family={expected['family']} gates={expected['gate_calls']} "
        f"record_count={expected['record_count']} promoted_target2={promoted}"
    )


def main():
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        verify_tier(tier)


if __name__ == "__main__":
    main()
