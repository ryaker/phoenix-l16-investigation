#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/codex_source_record_payload_watch")
TIERS = ("28mm", "35mm", "70mm", "150mm")
REQUIRED_TARGET_COUNTS = {
    "caller_pre_29a140": 1,
    "maker_after_299fd0": 1,
    "later_299c70_entry": 1,
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def _zero_hex(size):
    return "00" * size


def validate_report(path):
    packet = json.loads(path.read_text())
    process = packet.get("process", {})
    require(process.get("state") == "exited", f"{path.name}: process did not exit")
    require(process.get("exit_status") == 0, f"{path.name}: nonzero exit {process}")
    require(not packet.get("drive_hit_step_cap"), f"{path.name}: hit step cap")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")

    target_counts = packet.get("target_counts", {})
    for site, expected in REQUIRED_TARGET_COUNTS.items():
        require(
            target_counts.get(site) == expected,
            f"{path.name}: target count {site}={target_counts.get(site)}",
        )

    armed = packet.get("watchpoint_ids", {})
    require(len(armed) == 2, f"{path.name}: expected 2 armed watchpoints, got {armed}")
    for wp_id, meta in armed.items():
        size = meta.get("watch_size")
        require(size == 8, f"{path.name}: watchpoint {wp_id} size {size}")
        require(
            meta.get("bytes_before_hex") == _zero_hex(size),
            f"{path.name}: watchpoint {wp_id} was not zero before watch {meta}",
        )

    hit_counts = packet.get("watchpoint_hit_counts", {})
    require(hit_counts, f"{path.name}: missing watchpoint hit counts")
    require(
        sum(count or 0 for count in hit_counts.values()) >= 1,
        f"{path.name}: no watchpoint hits {hit_counts}",
    )

    samples = packet.get("watchpoint_samples", [])
    require(samples, f"{path.name}: no watchpoint samples")
    require(
        sum(count or 0 for count in hit_counts.values()) == len(samples),
        f"{path.name}: hit-count/sample mismatch {hit_counts} samples={len(samples)}",
    )

    for index, sample in enumerate(samples):
        require(
            sample.get("libcp_va") == 0x277A16,
            f"{path.name}: sample {index} stopped at {sample.get('libcp_va'):#x}",
        )
        disamb = sample.get("store_address_disambiguation")
        if disamb is None:
            regs = sample["registers"]
            watch_addr = sample["watchpoint"]["watch_addr"]
            r9_store_base = regs["r9"] + (2 * regs["rdx"])
            rcx_store_base = regs["rcx"] + (2 * regs["rdx"])
            disamb = {
                "matches_r9_16byte_store": 0 <= watch_addr - r9_store_base < 16,
                "matches_rcx_16byte_store": 0 <= watch_addr - rcx_store_base < 16,
            }
        require(
            disamb.get("matches_r9_16byte_store"),
            f"{path.name}: sample {index} does not match r9 store {disamb}",
        )
        require(
            not disamb.get("matches_rcx_16byte_store"),
            f"{path.name}: sample {index} also matches rcx store {disamb}",
        )
        require(
            sample.get("watched_bytes_now_hex") != sample["watchpoint"].get("bytes_before_hex"),
            f"{path.name}: sample {index} watched bytes unchanged",
        )

    return packet


def main():
    for tier in TIERS:
        path = ROOT / f"payload_watch_{tier}.json"
        require(path.exists(), f"missing report {path}")
        packet = validate_report(path)
        hit_counts = packet.get("watchpoint_hit_counts", {})
        samples = packet.get("watchpoint_samples", [])
        print(
            f"{path.name}: OK samples={len(samples)} "
            f"watch_hits={hit_counts} pc=0x277a16 store=0x277a10"
        )


if __name__ == "__main__":
    main()
