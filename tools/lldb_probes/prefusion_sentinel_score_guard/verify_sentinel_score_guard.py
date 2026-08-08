#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_sentinel_score_guard")
SENTINEL_HEX = "000080bf000080bf"

MAIN_EXPECTED = {
    "28mm": {
        "after_store_hits": 3,
        "after_store_pair_is_sentinel": 3,
        "after_store_without_pending": 0,
        "watchpoint_guard_hits": 0,
        "watchpoint_guard_known_sentinel_hits": 0,
        "watchpoint_guard_skip_by_flags": 0,
        "watchpoint_guard_not_skip_by_flags": 0,
    },
    "35mm": {
        "after_store_hits": 305,
        "after_store_pair_is_sentinel": 3,
        "after_store_without_pending": 302,
        "watchpoint_guard_hits": 0,
        "watchpoint_guard_known_sentinel_hits": 0,
        "watchpoint_guard_skip_by_flags": 0,
        "watchpoint_guard_not_skip_by_flags": 0,
    },
    "70mm": {
        "after_store_hits": 315,
        "after_store_pair_is_sentinel": 3,
        "after_store_without_pending": 312,
        "watchpoint_guard_hits": 26,
        "watchpoint_guard_known_sentinel_hits": 26,
        "watchpoint_guard_skip_by_flags": 26,
        "watchpoint_guard_not_skip_by_flags": 0,
    },
    "150mm": {
        "after_store_hits": 525,
        "after_store_pair_is_sentinel": 3,
        "after_store_without_pending": 522,
        "watchpoint_guard_hits": 24,
        "watchpoint_guard_known_sentinel_hits": 24,
        "watchpoint_guard_skip_by_flags": 24,
        "watchpoint_guard_not_skip_by_flags": 0,
    },
}

SKIP3_EXPECTED = {
    "28mm": {
        "file": "sentinel_score_guard_28mm_skip3.json",
        "after_store_hits": 7,
        "after_store_pair_is_sentinel": 6,
        "after_store_without_pending": 1,
        "store_y_hits": 6,
    },
    "35mm": {
        "file": "sentinel_score_guard_35mm_skip3.json",
        "after_store_hits": 45,
        "after_store_pair_is_sentinel": 6,
        "after_store_without_pending": 39,
        "store_y_hits": 6,
    },
}

COUNT_EXPECTED = {
    "28mm": {
        "file": "sentinel_score_guard_28mm_count.json",
        "after_store_hits": 2368,
        "after_store_pair_is_sentinel": 152,
        "after_store_without_pending": 2216,
        "store_y_hits": 152,
    },
    "35mm": {
        "file": "sentinel_score_guard_35mm_count.json",
        "after_store_hits": 5989,
        "after_store_pair_is_sentinel": 106,
        "after_store_without_pending": 5883,
        "store_y_hits": 106,
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load(path):
    return json.loads((ROOT / path).read_text())


def require_hdr_output(json_name, label):
    hdr = ROOT / json_name.replace(".json", ".hdr")
    require(hdr.exists(), f"{label}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{label}: HDR output is not Radiance data")


def assert_clean(packet, label):
    require(packet.get("process_exit_status") == 0, f"{label}: process did not exit cleanly")
    require(packet.get("drive_hit_step_cap") is False, f"{label}: hit drive step cap")
    require(not packet.get("errors"), f"{label}: probe errors {packet.get('errors')}")


def check_count_map(counts, expected, label):
    for name, value in expected.items():
        require(counts.get(name) == value, f"{label}: {name} {counts.get(name)} != {value}")


def validate_guard_samples(packet, tier, expected_guard_hits):
    guard_samples = packet.get("guard_samples") or []
    require(len(guard_samples) == expected_guard_hits, f"{tier}: guard sample count mismatch")
    for index, sample in enumerate(guard_samples):
        require(sample.get("libcp_va") == 0x218BC4, f"{tier}: guard sample {index} wrong VA")
        stack = sample.get("stack") or []
        require(stack and stack[0].get("libcp_va") == 0x218BC4, f"{tier}: guard sample {index} wrong top frame")
        require(len(stack) > 1 and stack[1].get("libcp_va") == 0x218F81, f"{tier}: guard sample {index} wrong caller")
        pair = sample.get("pair_now") or {}
        require(pair.get("hex") == SENTINEL_HEX, f"{tier}: guard sample {index} non-sentinel pair")
        require(pair.get("is_sentinel_neg1_neg1") is True, f"{tier}: guard sample {index} sentinel flag false")
        flags = sample.get("rflags_after_ucomiss") or {}
        require(flags.get("read_ok") is True, f"{tier}: guard sample {index} flags unreadable")
        require(flags.get("cf") == 0, f"{tier}: guard sample {index} CF not zero")
        require(flags.get("pf") == 0, f"{tier}: guard sample {index} PF not zero")
        require(flags.get("zf") == 0, f"{tier}: guard sample {index} ZF not zero")
        require(flags.get("jae_taken") is True, f"{tier}: guard sample {index} did not mark jae taken")


def validate_main():
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        json_name = f"sentinel_score_guard_{tier}.json"
        packet = load(json_name)
        label = f"{tier} main"
        assert_clean(packet, label)
        require_hdr_output(json_name, label)
        counts = packet.get("counts") or {}
        common = {
            "store_y_hits": 3,
            "sentinel_pairs_skipped_before_arm": 0,
            "watchpoints_armed": 3,
            "watchpoint_hits": 512,
            "watchpoints_disabled_after_cap": 1,
            "breakpoints_disabled_after_arm_limit": 1,
        }
        check_count_map(counts, common, label)
        check_count_map(counts, MAIN_EXPECTED[tier], label)
        validate_guard_samples(packet, tier, MAIN_EXPECTED[tier]["watchpoint_guard_hits"])
        print(
            f"{tier}: OK main guard_hits={counts['watchpoint_guard_hits']} "
            f"skip_by_flags={counts['watchpoint_guard_skip_by_flags']}"
        )


def validate_skip3():
    for tier, expected in SKIP3_EXPECTED.items():
        packet = load(expected["file"])
        label = f"{tier} skip3"
        assert_clean(packet, label)
        require_hdr_output(expected["file"], label)
        counts = packet.get("counts") or {}
        check_count_map(
            counts,
            {
                "sentinel_pairs_skipped_before_arm": 3,
                "watchpoints_armed": 3,
                "watchpoint_hits": 512,
                "watchpoint_guard_hits": 0,
                "watchpoint_guard_skip_by_flags": 0,
                "watchpoint_guard_not_skip_by_flags": 0,
                "watchpoints_disabled_after_cap": 1,
                "breakpoints_disabled_after_arm_limit": 1,
            },
            label,
        )
        check_count_map(
            counts,
            {
                name: value
                for name, value in expected.items()
                if name != "file"
            },
            label,
        )
        require(not packet.get("guard_samples"), f"{label}: unexpected guard samples")
        print(f"{tier}: OK skip3 watched_pairs=3 guard_hits=0")


def validate_count_only():
    for tier, expected in COUNT_EXPECTED.items():
        packet = load(expected["file"])
        label = f"{tier} count"
        assert_clean(packet, label)
        require_hdr_output(expected["file"], label)
        counts = packet.get("counts") or {}
        check_count_map(
            counts,
            {
                "sentinel_pairs_skipped_before_arm": 0,
                "watchpoints_armed": 0,
                "watchpoint_hits": 0,
                "watchpoint_guard_hits": 0,
                "watchpoint_guard_skip_by_flags": 0,
                "watchpoint_guard_not_skip_by_flags": 0,
                "watchpoints_disabled_after_cap": 0,
                "breakpoints_disabled_after_arm_limit": 0,
            },
            label,
        )
        check_count_map(
            counts,
            {
                name: value
                for name, value in expected.items()
                if name != "file"
            },
            label,
        )
        print(
            f"{tier}: OK count_only completed_sentinels="
            f"{counts['after_store_pair_is_sentinel']}"
        )


def main():
    validate_main()
    validate_skip3()
    validate_count_only()


if __name__ == "__main__":
    main()
