#!/usr/bin/env python3
"""Verify corrected cross-talk liveness and the stage-6 descriptor join."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs" / "correction_liveness"
REPORTS = [
    "unit1_28mm",
    "unit1_35mm",
    "unit1_70mm",
    "unit1_150mm",
    "unit2_70mm",
]
TRUE_CALLBACK = "remove_crosstalk_float_true_callback_0x30"


def main():
    summaries = {}
    for label in REPORTS:
        report = json.loads((RUNS / f"{label}.json").read_text())
        observed = {
            name: count
            for name, count in report["counts"].items()
            if name.startswith("remove_crosstalk_")
        }
        assert observed[TRUE_CALLBACK] == 1, (label, observed)
        assert all(count == 0 for name, count in observed.items() if name != TRUE_CALLBACK)
        batch = report.get("crosstalk_stop_batches")
        assert batch and batch[0]
        assert {item["site"] for item in batch[0]} == {TRUE_CALLBACK}
        log = (RUNS / f"{label}.log").read_text(errors="replace")
        assert "exited with status = 0" in log
        summaries[label] = {
            "observed_callback": TRUE_CALLBACK,
            "threads_in_stop_batch": len(batch[0]),
            "completed_render": True,
        }

    stage_path = (
        ROOT
        / "runs"
        / "create_stereo_color_public_reconstruction"
        / "unit1_28mm_a1_lineage"
        / "report.json"
    )
    stage = json.loads(stage_path.read_text())
    calls = [
        item
        for item in stage["lineage_samples"]
        if item["site"] == "demosaic_call"
        and item.get("payload_d0_descriptor")
        and item.get("local_input_descriptor")
    ]
    assert calls
    matches = sum(
        item["payload_d0_descriptor"]["allocation"]
        == item["local_input_descriptor"]["allocation"]
        for item in calls
    )
    assert matches == len(calls)
    assert stage["lineage_hits"]["stage5_float_true_callback"] > 0
    assert stage["lineage_hits"]["stage5_float_true_secondary"] == 0

    print(
        json.dumps(
            {
                "reports": summaries,
                "demosaic_handoff": {
                    "captured_calls": len(calls),
                    "same_allocation": matches,
                    "stage5_float_true_callback_hits": stage["lineage_hits"][
                        "stage5_float_true_callback"
                    ],
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
