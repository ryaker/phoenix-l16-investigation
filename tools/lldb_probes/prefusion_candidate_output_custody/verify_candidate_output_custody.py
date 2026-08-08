#!/usr/bin/env python3
import json
import pathlib


ROOT = pathlib.Path("runs/prefusion_candidate_output_custody")

EXPECTED = {
    "28mm": {
        "file": "custody_28mm.json",
        "log": "custody_28mm.log",
        "hdr": "custody_28mm.hdr",
        "family": "a",
        "record_count": 151,
        "counts": {
            "family_a_wrapper_entry_2481a0": 4,
            "family_a_context_ready_2484a6": 4,
            "family_a_scorer_entry_24c320": 160,
            "family_a_after_executor_2484bd": 4,
            "family_a_gate_call_2484e4": 4,
            "family_b_wrapper_entry_248580": 0,
            "family_b_context_ready_24887b": 0,
            "family_b_scorer_entry_24d610": 0,
            "family_b_after_executor_248892": 0,
            "family_b_gate_call_2488b9": 0,
            "shared_gate_entry_2439b0": 16,
        },
        "scorer_entries": {"a": 32, "b": 0},
    },
    "35mm": {
        "file": "custody_35mm.json",
        "log": "custody_35mm.log",
        "hdr": "custody_35mm.hdr",
        "family": "a",
        "record_count": 154,
        "counts": {
            "family_a_wrapper_entry_2481a0": 4,
            "family_a_context_ready_2484a6": 4,
            "family_a_scorer_entry_24c320": 160,
            "family_a_after_executor_2484bd": 4,
            "family_a_gate_call_2484e4": 4,
            "family_b_wrapper_entry_248580": 0,
            "family_b_context_ready_24887b": 0,
            "family_b_scorer_entry_24d610": 0,
            "family_b_after_executor_248892": 0,
            "family_b_gate_call_2488b9": 0,
            "shared_gate_entry_2439b0": 16,
        },
        "scorer_entries": {"a": 32, "b": 0},
    },
    "70mm": {
        "file": "custody_70mm.json",
        "log": "custody_70mm_solo.log",
        "hdr": "custody_70mm.hdr",
        "family": "b",
        "record_count": 169,
        "counts": {
            "family_a_wrapper_entry_2481a0": 0,
            "family_a_context_ready_2484a6": 0,
            "family_a_scorer_entry_24c320": 0,
            "family_a_after_executor_2484bd": 0,
            "family_a_gate_call_2484e4": 0,
            "family_b_wrapper_entry_248580": 4,
            "family_b_context_ready_24887b": 4,
            "family_b_scorer_entry_24d610": 160,
            "family_b_after_executor_248892": 4,
            "family_b_gate_call_2488b9": 4,
            "shared_gate_entry_2439b0": 16,
        },
        "scorer_entries": {"a": 0, "b": 32},
    },
    "150mm": {
        "file": "custody_150mm.json",
        "log": "custody_150mm.log",
        "hdr": "custody_150mm.hdr",
        "family": "b",
        "record_count": 34,
        "counts": {
            "family_a_wrapper_entry_2481a0": 0,
            "family_a_context_ready_2484a6": 0,
            "family_a_scorer_entry_24c320": 0,
            "family_a_after_executor_2484bd": 0,
            "family_a_gate_call_2484e4": 0,
            "family_b_wrapper_entry_248580": 4,
            "family_b_context_ready_24887b": 4,
            "family_b_scorer_entry_24d610": 136,
            "family_b_after_executor_248892": 4,
            "family_b_gate_call_2488b9": 4,
            "shared_gate_entry_2439b0": 16,
        },
        "scorer_entries": {"a": 0, "b": 32},
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(path.read_text())


def verify_hdr(path, tier):
    data = path.read_bytes()[:16]
    require(data.startswith(b"#?RADIANCE"), f"{tier}: HDR output is not Radiance HDR")


def verify_log(path, tier, json_name, hdr_name):
    text = path.read_text(errors="replace")
    require("Written:" in text and hdr_name in text, f"{tier}: log lacks HDR write line")
    require("L16_PREFUSION_CANDIDATE_OUTPUT_CUSTODY_WROTE" in text, f"{tier}: log lacks JSON write marker")
    require(json_name in text, f"{tier}: log does not reference JSON output")


def verify_vector(tier, vector, expected_record_count):
    require(vector.get("read_ok") is True, f"{tier}: vector read failed")
    require(vector.get("stride") == 44, f"{tier}: vector stride {vector.get('stride')} != 44")
    require(vector.get("record_count") == expected_record_count, f"{tier}: record count {vector.get('record_count')} != {expected_record_count}")
    require(vector.get("byte_len_mod_stride") == 0, f"{tier}: vector byte length not aligned")
    require(vector.get("byte_len") == expected_record_count * 44, f"{tier}: vector byte length mismatch")


def verify_tier(tier):
    expected = EXPECTED[tier]
    packet = read_json(ROOT / expected["file"])

    require(packet.get("drive_hit_step_cap") is False, f"{tier}: drive hit step cap")
    require(not packet.get("errors"), f"{tier}: probe errors {packet.get('errors')}")

    counts = packet.get("counts") or {}
    for name, value in expected["counts"].items():
        require(counts.get(name) == value, f"{tier}: {name} {counts.get(name)} != {value}")

    scorer_entries = packet.get("scorer_entries") or {}
    for family, value in expected["scorer_entries"].items():
        require(len(scorer_entries.get(family) or []) == value, f"{tier}: scorer_entries[{family}] count mismatch")

    known = packet.get("known_output_vectors") or {}
    require(len(known) == 1, f"{tier}: expected one known output vector")
    known_vector_addr = next(iter(known.keys()))
    require(known[known_vector_addr].get("family") == expected["family"], f"{tier}: known vector family mismatch")

    gate_calls = packet.get("gate_calls") or []
    matches = packet.get("shared_gate_matches") or []
    require(len(gate_calls) == 4, f"{tier}: gate call count {len(gate_calls)} != 4")
    require(len(matches) == 4, f"{tier}: shared-gate match count {len(matches)} != 4")

    gate_vector_ptrs = set()
    for call in gate_calls:
        require(call.get("family") == expected["family"], f"{tier}: gate call family mismatch")
        require(call.get("matches_active_output_vec") is True, f"{tier}: gate call did not match active output vector")
        require(call.get("matches_active_gate_state_arg") is True, f"{tier}: gate call did not match active gate state arg")
        vector = call.get("output_vec_at_gate_call") or {}
        verify_vector(tier, vector, expected["record_count"])
        require(call.get("gate_arg_rsi_output_vec") == vector.get("addr"), f"{tier}: gate arg/vector addr mismatch")
        gate_vector_ptrs.add(call.get("gate_arg_rsi_output_vec"))

    match_vector_ptrs = set()
    for match in matches:
        require(match.get("matched_known_output_vec", {}).get("family") == expected["family"], f"{tier}: matched family mismatch")
        vector = match.get("output_vec_at_shared_gate_entry") or {}
        verify_vector(tier, vector, expected["record_count"])
        require(match.get("gate_arg_rsi_output_vec") == vector.get("addr"), f"{tier}: shared gate arg/vector addr mismatch")
        match_vector_ptrs.add(match.get("gate_arg_rsi_output_vec"))

    require(len(gate_vector_ptrs) == 1, f"{tier}: multiple gate output vectors")
    require(gate_vector_ptrs == match_vector_ptrs, f"{tier}: gate/shared vector pointers differ")
    require(f"0x{next(iter(gate_vector_ptrs)):x}" == known_vector_addr, f"{tier}: known vector pointer mismatch")

    verify_log(ROOT / expected["log"], tier, expected["file"], expected["hdr"])
    verify_hdr(ROOT / expected["hdr"], tier)

    print(
        f"{tier}: OK family={expected['family']} record_count={expected['record_count']} "
        f"gate_calls={len(gate_calls)} shared_matches={len(matches)}"
    )


def main():
    for tier in ("28mm", "35mm", "70mm", "150mm"):
        verify_tier(tier)


if __name__ == "__main__":
    main()
