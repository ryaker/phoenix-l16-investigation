"""Companion to stage_vector_probe: capture the stage-15 OUTPUT payload.

The stage executor's STAGE_RETURN site (0x33f3eb) is not bound by
stage_vector_probe.attach(); per-stage "after" states normally come from the
next stage's "before". Stage 15 is last, so its output was never captured.
This callback binds to 0x33f3eb, waits for the active closure's stage-15
return, snapshots the payload, dumps the slots as stage_15_after_slot_*.bin,
writes the report, and kills the process.

Usage (after stage_vector_probe.reset/attach and its breakpoints):
  breakpoint set --shlib libcp.dylib --address 0x33f3eb
  script import final_slot_probe
  ...bind: breakpoint command add -F final_slot_probe.hit <id>
"""
import os

import stage_vector_probe as svp


def hit(frame, bp_loc, internal_dict):
    st = svp._state()
    thread = frame.GetThread()
    if thread.GetThreadID() != st.get("active_thread"):
        return False
    calls = st.get("calls", [])
    if not calls or calls[-1].get("stage_index") != 15:
        return False
    if calls[-1].get("after") is not None:
        return False
    process = thread.GetProcess()
    base = svp._base(process.GetTarget())
    before = calls[-1]["before"]
    try:
        after = svp._snapshot(
            process, before["rtti"]["object"], before["tile_address"], base
        )
        svp._dump_payload_slots(process, after, "stage_15_after")
        calls[-1]["after"] = after
        calls[-1]["after_source"] = "stage_return_final_slot_probe"
        st["complete"] = True
    except Exception as exc:  # noqa: BLE001 - recorded, not raised, in-probe
        st["errors"].append(f"final_slot_probe: {exc!r}")
    report_path = os.path.join(st["output_dir"], "report.json")
    svp.write_report(None, report_path)
    process.Kill()
    return False
