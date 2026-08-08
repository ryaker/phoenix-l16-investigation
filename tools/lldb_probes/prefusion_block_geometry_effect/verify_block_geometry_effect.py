#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "runs" / "prefusion_block_geometry_effect"

EXPECTED_COUNTS = {
    "28mm": {
        "entry_hits": 44,
        "active_entry_hits": 22,
        "inactive_entry_hits": 22,
        "d2a0_return_hits": 22,
        "d2a0_success": 22,
        "d2a0_failure": 0,
        "geom_return_hits": 22,
        "geom_accept": 22,
        "geom_reject": 0,
        "active_clear_hits": 0,
        "return_hits": 44,
        "return_true": 22,
        "return_false": 22,
    },
    "35mm": {
        "entry_hits": 44,
        "active_entry_hits": 22,
        "inactive_entry_hits": 22,
        "d2a0_return_hits": 22,
        "d2a0_success": 22,
        "d2a0_failure": 0,
        "geom_return_hits": 22,
        "geom_accept": 22,
        "geom_reject": 0,
        "active_clear_hits": 0,
        "return_hits": 44,
        "return_true": 22,
        "return_false": 22,
    },
    "70mm": {
        "entry_hits": 44,
        "active_entry_hits": 27,
        "inactive_entry_hits": 17,
        "d2a0_return_hits": 27,
        "d2a0_success": 27,
        "d2a0_failure": 0,
        "geom_return_hits": 27,
        "geom_accept": 25,
        "geom_reject": 2,
        "active_clear_hits": 2,
        "return_hits": 44,
        "return_true": 25,
        "return_false": 19,
    },
    "150mm": {
        "entry_hits": 44,
        "active_entry_hits": 22,
        "inactive_entry_hits": 22,
        "d2a0_return_hits": 22,
        "d2a0_success": 22,
        "d2a0_failure": 0,
        "geom_return_hits": 22,
        "geom_accept": 22,
        "geom_reject": 0,
        "active_clear_hits": 0,
        "return_hits": 44,
        "return_true": 22,
        "return_false": 22,
    },
}


def level_counts(block, level):
    fam_a = block["pair_family_0x30"]["levels"]
    fam_b = block["pair_family_0x48"]["levels"]
    if level >= len(fam_a) or level >= len(fam_b):
        return None, None
    return fam_a[level]["vector"]["elem_count"], fam_b[level]["vector"]["elem_count"]


def load(zoom):
    path = RUN_DIR / f"block_geometry_effect_{zoom}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(zoom):
    hdr = RUN_DIR / f"block_geometry_effect_{zoom}.hdr"
    require(hdr.exists(), f"{zoom}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{zoom}: HDR output is not Radiance data")


def verify_zoom(zoom):
    data = load(zoom)
    counts = data["counts"]
    require(data["process_exit_status"] == 0, f"{zoom}: nonzero exit")
    require(not data["drive_hit_step_cap"], f"{zoom}: step cap")
    require(data["errors"] == [], f"{zoom}: probe errors {data['errors']}")
    require_hdr_output(zoom)
    for key, expected in EXPECTED_COUNTS[zoom].items():
        require(counts.get(key) == expected, f"{zoom}: count {key}={counts.get(key)} expected {expected}")
    require(len(data["entry_samples"]) == counts["entry_hits"], f"{zoom}: incomplete entry samples")
    require(len(data["return_samples"]) == counts["return_hits"], f"{zoom}: incomplete return samples")
    entries = {packet["call_id"]: packet for packet in data["entry_samples"]}
    d2a0 = {packet["call_id"]: packet for packet in data["d2a0_return_samples"]}
    geom = {packet["call_id"]: packet for packet in data["geom_return_samples"]}
    clears = {packet["call_id"]: packet for packet in data["active_clear_samples"]}
    return_true = 0
    return_false = 0
    active_true_growth = 0
    active_clear_count = 0
    inactive_false = 0
    targets_seen = set()
    levels_seen = set()
    max_growth = 0
    for ret in data["return_samples"]:
        cid = ret["call_id"]
        entry = entries[cid]
        level = entry["level_esi"]
        targets_seen.add(entry["block_entry"]["target_0x00"])
        levels_seen.add(level)
        active = entry["block_entry"]["active_0x04"]
        before_a, before_b = level_counts(entry["block_entry"], level)
        after_a, after_b = level_counts(ret["block_return"], level)
        if ret["return_al"]:
            return_true += 1
            require(active == 1, f"{zoom}: true return from inactive entry call {cid}")
            require(cid in d2a0 and d2a0[cid]["d2a0_al"] == 1, f"{zoom}: true return without d2a0 success {cid}")
            require(cid in geom and geom[cid]["geom_al"] == 1, f"{zoom}: true return without geom accept {cid}")
            require(ret["block_return"]["active_0x04"] == 1, f"{zoom}: true return inactive after {cid}")
            require(before_a is not None and before_b is not None, f"{zoom}: true return missing level vectors {cid}")
            growth_a = after_a - before_a
            growth_b = after_b - before_b
            require(growth_a > 0 and growth_b > 0, f"{zoom}: true return without pair-vector growth {cid}")
            require(growth_a == growth_b, f"{zoom}: asymmetric pair-vector growth {cid}")
            max_growth = max(max_growth, growth_a)
            active_true_growth += 1
        else:
            return_false += 1
            if active == 0:
                inactive_false += 1
                require(cid not in d2a0, f"{zoom}: inactive entry reached d2a0 {cid}")
                require(ret["block_return"]["active_0x04"] == 0, f"{zoom}: inactive entry active after {cid}")
            else:
                require(cid in clears, f"{zoom}: active false return without active clear {cid}")
                require(cid in geom and geom[cid]["geom_al"] == 0, f"{zoom}: active false return without geom reject {cid}")
                require(ret["block_return"]["active_0x04"] == 0, f"{zoom}: active clear did not persist {cid}")
                active_clear_count += 1
    require(return_true == counts["return_true"], f"{zoom}: true return recount mismatch")
    require(return_false == counts["return_false"], f"{zoom}: false return recount mismatch")
    require(active_true_growth == counts["return_true"], f"{zoom}: active growth recount mismatch")
    require(active_clear_count == counts["active_clear_hits"], f"{zoom}: active clear recount mismatch")
    require(inactive_false == counts["inactive_entry_hits"], f"{zoom}: inactive false recount mismatch")
    require(targets_seen == {1, 2}, f"{zoom}: targets seen {targets_seen}")
    require(levels_seen == {1, 2, 3}, f"{zoom}: levels seen {levels_seen}")
    return {
        "zoom": zoom,
        "entry_hits": counts["entry_hits"],
        "active_entries": counts["active_entry_hits"],
        "return_true": counts["return_true"],
        "return_false": counts["return_false"],
        "geom_accept": counts["geom_accept"],
        "geom_reject": counts["geom_reject"],
        "active_clears": counts["active_clear_hits"],
        "max_pair_growth": max_growth,
    }


def main():
    summaries = [verify_zoom(zoom) for zoom in ("28mm", "35mm", "70mm", "150mm")]
    for item in summaries:
        print(
            "{zoom}: OK entry={entry_hits} active={active_entries} true={return_true} "
            "false={return_false} geom={geom_accept}/{geom_reject} clears={active_clears} "
            "max_growth={max_pair_growth}".format(**item)
        )


if __name__ == "__main__":
    main()
