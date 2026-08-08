#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = ROOT / "runs" / "prefusion_block_decision_cascade"

EXPECTED = {
    "28mm": {
        "decision_join_hits": 31,
        "coord_output_call_hits": 9,
        "families": {
            "heavy_244560": {(0, 1, 0): 16},
            "heavy_245a40": {(0, 1, 0): 15},
        },
    },
    "35mm": {
        "decision_join_hits": 31,
        "coord_output_call_hits": 9,
        "families": {
            "heavy_244560": {(0, 1, 0): 16},
            "heavy_245a40": {(0, 1, 0): 15},
        },
    },
    "70mm": {
        "decision_join_hits": 27,
        "coord_output_call_hits": 8,
        "families": {
            "heavy_244560": {(1, 0, 0): 12},
            "heavy_245a40": {(0, 1, 0): 15},
        },
    },
    "150mm": {
        "decision_join_hits": 31,
        "coord_output_call_hits": 9,
        "families": {
            "heavy_244560": {(1, 0, 0): 16},
            "heavy_245a40": {(0, 1, 0): 15},
        },
    },
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_hdr_output(zoom):
    hdr = RUN_DIR / f"block_decision_cascade_{zoom}.hdr"
    require(hdr.exists(), f"{zoom}: missing HDR output {hdr}")
    require(hdr.read_bytes().startswith(b"#?RADIANCE"), f"{zoom}: HDR output is not Radiance data")


def load(zoom):
    with (RUN_DIR / f"block_decision_cascade_{zoom}.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def family_decisions(data):
    out = {}
    for item in data["decisions"]:
        key = (item["active300"], item["active360"], item["abort_flag"])
        family = item["family"]
        out.setdefault(family, {})
        out[family][key] = out[family].get(key, 0) + 1
    return out


def verify_zoom(zoom):
    data = load(zoom)
    counts = data["counts"]
    expected = EXPECTED[zoom]
    require(data["process_exit_status"] == 0, f"{zoom}: nonzero process exit")
    require(data["errors"] == [], f"{zoom}: probe errors {data['errors']}")
    require(data["drive_hit_step_cap"] is False, f"{zoom}: step cap")
    require_hdr_output(zoom)
    require(counts["decision_join_hits"] == expected["decision_join_hits"], f"{zoom}: decision count")
    require(counts["decision_continue"] == expected["decision_join_hits"], f"{zoom}: continue count")
    require(counts["decision_abort"] == 0, f"{zoom}: abort decisions")
    require(counts["sentinel_fill_path_hits"] == 0, f"{zoom}: sentinel path hits")
    require(counts["coord_output_call_hits"] == expected["coord_output_call_hits"], f"{zoom}: coord-output calls")
    require(len(data["decisions"]) == counts["decision_join_hits"], f"{zoom}: missing decision samples")
    got_families = family_decisions(data)
    require(got_families == expected["families"], f"{zoom}: family decisions {got_families}")
    for decision in data["decisions"]:
        active300 = decision["active300"]
        active360 = decision["active360"]
        require(decision["abort_flag"] == 0, f"{zoom}: abort flag at {decision}")
        require((active300, active360) in {(1, 0), (0, 1)}, f"{zoom}: expected exactly one active block {decision}")
    coord_samples = [sample for sample in data["samples"] if sample["role"] == "coord_output_call"]
    require(len(coord_samples) == counts["coord_output_call_hits"], f"{zoom}: missing coord samples")
    for sample in coord_samples:
        block300 = sample["state"]["block300"]["active_0x04"]
        block360 = sample["state"]["block360"]["active_0x04"]
        require((block300, block360) in {(1, 0), (0, 1)}, f"{zoom}: coord call without exactly one active block")
    return {
        "zoom": zoom,
        "decisions": counts["decision_join_hits"],
        "coord": counts["coord_output_call_hits"],
        "families": got_families,
    }


def main():
    for zoom in ("28mm", "35mm", "70mm", "150mm"):
        item = verify_zoom(zoom)
        fam = "; ".join(
            f"{family} {patterns}"
            for family, patterns in sorted(item["families"].items())
        )
        print(f"{zoom}: OK decisions={item['decisions']} coord_output_calls={item['coord']} {fam}")


if __name__ == "__main__":
    main()
