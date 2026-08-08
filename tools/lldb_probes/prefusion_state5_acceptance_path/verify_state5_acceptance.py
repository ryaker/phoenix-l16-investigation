#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_state5_acceptance_path")

EXPECTED = {
    "70mm": {
        "file": "state5_acceptance_70mm.json",
        "counts": {
            "gate_before_hits": 4,
            "gate_after_hits": 4,
            "promotion_events": 4,
            "promoted_records_total": 257,
            "entry_2416d0_hits": 37,
            "entry_2416d0_target2_hits": 21,
            "entry_2416d0_promoted_overlap_hits": 5,
            "pre_exec_hits": 37,
            "post_exec_hits": 37,
            "store_promoted_overlap_hits": 273,
        },
        "small_sets": [
            {
                "target": 2,
                "selected_count": 9,
                "overlap": [31, 49, 64, 68, 77, 78, 108],
            },
            {
                "target": 2,
                "selected_count": 8,
                "overlap": [79, 122, 134, 141, 142, 143, 148, 156],
            },
        ],
    },
    "150mm": {
        "file": "state5_acceptance_150mm.json",
        "counts": {
            "gate_before_hits": 3,
            "gate_after_hits": 3,
            "promotion_events": 1,
            "promoted_records_total": 10,
            "entry_2416d0_hits": 23,
            "entry_2416d0_target2_hits": 11,
            "entry_2416d0_promoted_overlap_hits": 2,
            "pre_exec_hits": 22,
            "post_exec_hits": 22,
            "store_promoted_overlap_hits": 19,
        },
        "small_sets": [
            {
                "target": 2,
                "selected_count": 10,
                "overlap": [17, 18, 19, 20, 21, 22, 23, 26, 28, 32],
            },
        ],
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(tier):
    hdr = ROOT / EXPECTED[tier]["file"].replace(".json", ".hdr")
    require(hdr.exists(), f"{tier}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance data")


def load_packet(tier):
    path = ROOT / EXPECTED[tier]["file"]
    return json.loads(path.read_text())


def sample_overlap(sample):
    locals_packet = sample.get("locals") or {}
    return sample.get("selected_promoted_overlap") or locals_packet.get(
        "selected_promoted_overlap"
    )


def selected_values(sample):
    locals_packet = sample.get("locals") or {}
    selected_vector = locals_packet.get("selected_vector") or {}
    return selected_vector.get("values") or sample.get("selected_indices_state4_target") or []


def selected_count(sample):
    locals_packet = sample.get("locals") or {}
    count = locals_packet.get("selected_count_cell")
    if count is not None:
        return count
    values = selected_values(sample)
    return len(values)


def find_matching_sample(samples, expected):
    expected_overlap = expected["overlap"]
    for sample in samples:
        if sample.get("target", sample.get("target_r9d")) != expected["target"]:
            continue
        if selected_count(sample) != expected["selected_count"]:
            continue
        if sample_overlap(sample) == expected_overlap:
            return sample
    return None


def validate_small_set(packet, tier, expected):
    for sample_key in ("entry_samples", "pre_exec_samples", "post_exec_samples"):
        sample = find_matching_sample(packet.get(sample_key, []), expected)
        require(sample is not None, f"{tier}: missing {sample_key} for {expected}")
        selected = selected_values(sample)
        overlap = expected["overlap"]
        require(
            set(overlap).issubset(set(selected)),
            f"{tier}: {sample_key} selected vector missing overlap {overlap}",
        )

    stores_by_index = {}
    for store in packet.get("store_samples", []):
        if not store.get("is_promoted_index"):
            continue
        if store.get("target") != expected["target"]:
            continue
        record = store.get("record_now") or {}
        if record.get("state_0x24") != 5 or record.get("target_0x28") != expected["target"]:
            continue
        stores_by_index.setdefault(store.get("selected_index"), []).append(store)

    missing = [index for index in expected["overlap"] if index not in stores_by_index]
    require(not missing, f"{tier}: missing promoted state-5 store samples {missing}")


def validate_tier(tier):
    expected = EXPECTED[tier]
    packet = load_packet(tier)
    require(packet.get("process_exit_status") == 0, f"{tier}: process did not exit cleanly")
    require(packet.get("drive_hit_step_cap") is False, f"{tier}: hit drive step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")
    require_hdr_output(tier)

    counts = packet.get("counts") or {}
    for name, value in expected["counts"].items():
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")
    require(len(packet.get("promotions", [])) == expected["counts"]["promotion_events"], f"{tier}: promotion packet count mismatch")
    require(packet.get("entry_samples"), f"{tier}: missing entry samples")
    require(packet.get("pre_exec_samples"), f"{tier}: missing pre-exec samples")
    require(packet.get("post_exec_samples"), f"{tier}: missing post-exec samples")
    require(packet.get("store_samples"), f"{tier}: missing store samples")

    for small_set in expected["small_sets"]:
        validate_small_set(packet, tier, small_set)

    small_set_summary = ";".join(
        f"target={item['target']}:selected={item['selected_count']}:overlap={len(item['overlap'])}"
        for item in expected["small_sets"]
    )
    print(
        f"{tier}: OK promotions={counts['promotion_events']} "
        f"promoted_records={counts['promoted_records_total']} "
        f"target2_entries={counts['entry_2416d0_target2_hits']} "
        f"overlap_entries={counts['entry_2416d0_promoted_overlap_hits']} "
        f"promoted_store_hits={counts['store_promoted_overlap_hits']} "
        f"small_sets={small_set_summary}"
    )


def main():
    for tier in ("70mm", "150mm"):
        validate_tier(tier)


if __name__ == "__main__":
    main()
