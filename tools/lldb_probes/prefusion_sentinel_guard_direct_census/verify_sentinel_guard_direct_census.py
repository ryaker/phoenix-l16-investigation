#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_sentinel_guard_direct_census")

EXPECTED = {
    "28mm": {
        "file": "sentinel_guard_direct_28mm.json",
        "store_y_hits": 152,
        "after_store_hits": 2368,
        "after_store_pair_is_sentinel": 152,
        "after_store_without_pending": 2216,
        "unique_sentinel_addrs": 152,
    },
    "35mm": {
        "file": "sentinel_guard_direct_35mm.json",
        "store_y_hits": 106,
        "after_store_hits": 5989,
        "after_store_pair_is_sentinel": 106,
        "after_store_without_pending": 5883,
        "unique_sentinel_addrs": 106,
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(json_name, tier):
    hdr = ROOT / json_name.replace(".json", ".hdr")
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def validate_tier(tier):
    expected = EXPECTED[tier]
    packet = json.loads((ROOT / expected["file"]).read_text())
    require(packet.get("process_exit_status") == 0, f"{tier}: process did not exit cleanly")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: hit drive step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require_hdr_output(expected["file"], tier)
    counts = packet.get("counts") or {}
    for name, value in expected.items():
        if name == "file":
            continue
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")
    for name in (
        "guard_hits",
        "guard_known_sentinel_addr_hits",
        "guard_known_sentinel_pair_hits",
        "guard_known_sentinel_skip_by_flags",
        "guard_known_sentinel_not_skip_by_flags",
        "guard_breakpoint_disabled_after_total_cap",
    ):
        require(counts.get(name) == 0, f"{tier}: {name} {counts.get(name)} != 0")
    require(
        counts.get("after_store_pair_is_sentinel") == counts.get("unique_sentinel_addrs"),
        f"{tier}: completed sentinel count != unique address count",
    )
    print(
        f"{tier}: OK completed_sentinels={counts['after_store_pair_is_sentinel']} "
        f"unique_addrs={counts['unique_sentinel_addrs']} guard_hits={counts['guard_hits']}"
    )


def main():
    for tier in ("28mm", "35mm"):
        validate_tier(tier)


if __name__ == "__main__":
    main()
