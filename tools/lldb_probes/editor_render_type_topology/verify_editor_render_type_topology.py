#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs" / "editor_render_type_topology"
SITE_NAMES = {
    "renderer_request",
    "init_resamp",
    "process_level0",
    "iramp_entry",
    "src1_wrapper",
    "src2_wrapper",
    "contributor_wrapper",
    "monofusion_worker",
    "min_cost_index",
    "index_to_depth",
    "calibration_compose",
}


def load(name):
    with (RUNS / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def main():
    reports = [load("type1_28mm.json"), load("type2_28mm.json")]
    for report in reports:
        assert set(report["counts"]) == SITE_NAMES
        assert all(report["resolved_locations"][name] == 1 for name in SITE_NAMES)
        assert report["counts"]["renderer_request"] == 1

    type1, type2 = reports
    assert type1["render_type"] == 1
    assert type2["render_type"] == 2
    brush = load("brush_type1_28mm.json")
    assert set(brush["counts"]) == SITE_NAMES
    assert set(brush["post_marker_counts"]) == SITE_NAMES
    assert all(brush["resolved_locations"][name] == 1 for name in SITE_NAMES)
    gui_reports = {
        "28mm": brush["marker_snapshot"],
        "35mm": load("gui_type1_35mm.json")["counts"],
        "70mm": load("gui_type1_70mm.json")["counts"],
        "150mm": load("gui_type1_150mm.json")["counts"],
    }
    for focal, counts in gui_reports.items():
        assert counts["renderer_request"] == 5, (focal, counts)
        assert counts["init_resamp"] > 0, (focal, counts)
        assert counts["process_level0"] > 0, (focal, counts)
        assert counts["iramp_entry"] > 0, (focal, counts)
        assert counts["src1_wrapper"] > 0, (focal, counts)
        assert counts["src2_wrapper"] > 0, (focal, counts)
        assert counts["contributor_wrapper"] > 0, (focal, counts)
    print("editor_render_type_topology=OK")
    for report in reports:
        print(f"type={report['render_type']} counts={report['counts']}")
    print(f"type=1 post_brush={brush['post_marker_counts']}")
    for focal, counts in gui_reports.items():
        print(f"gui_type1 focal={focal} counts={counts}")


if __name__ == "__main__":
    main()
