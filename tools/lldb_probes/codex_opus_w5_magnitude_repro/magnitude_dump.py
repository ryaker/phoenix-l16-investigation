import builtins
import json
import math


def reset(label="", mode=""):
    builtins.l16_codex_w5_magnitude = {
        "label": label,
        "mode": mode,
        "captures": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_codex_w5_magnitude"):
        reset()
    return builtins.l16_codex_w5_magnitude


def _frame(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    return process, thread, thread.GetSelectedFrame()


def _xmm_f32s(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    out = []
    for index in range(4):
        if not data.IsValid():
            out.append(None)
            continue
        value = data.GetFloat(error, index * 4)
        out.append(value if error.Success() else None)
    return out


def _capture(debugger, stage, extra=None):
    state = _state()
    process, thread, frame = _frame(debugger)
    packet = {
        "stage": stage,
        "pc": frame.GetPC(),
        "thread_id": thread.GetThreadID(),
        "xmm0": _xmm_f32s(frame, "xmm0"),
        "xmm1": _xmm_f32s(frame, "xmm1"),
        "xmm2": _xmm_f32s(frame, "xmm2"),
    }
    if extra:
        packet.update(extra)
    state["captures"].append(packet)
    print("L16_CODEX_W5_CAPTURE", json.dumps(packet, sort_keys=True))


def capture_score_pre(debugger):
    process, thread, frame = _frame(debugger)
    x0 = _xmm_f32s(frame, "xmm0")[0]
    x1 = _xmm_f32s(frame, "xmm1")[0]
    product = x0 * x1 if x0 is not None and x1 is not None else None
    _capture(
        debugger,
        "score_pre_mul_36e511",
        {
            "factor_xmm0": x0,
            "factor_xmm1": x1,
            "predicted_product": product,
            "predicted_sqrt": math.sqrt(product) if product is not None and product >= 0 else None,
        },
    )


def capture_score_after_mul(debugger):
    frame = _frame(debugger)[2]
    x0 = _xmm_f32s(frame, "xmm0")[0]
    _capture(debugger, "score_after_mul_36e515", {"product_xmm0": x0})


def capture_score_after_sqrt(debugger):
    frame = _frame(debugger)[2]
    x0 = _xmm_f32s(frame, "xmm0")[0]
    _capture(debugger, "score_after_sqrt_36e519", {"score_xmm0": x0})


def capture_recip_pre(debugger):
    x2 = _xmm_f32s(_frame(debugger)[2], "xmm2")[0]
    _capture(
        debugger,
        "recip_pre_rcpss_36a938",
        {
            "sigma_xmm2": x2,
            "predicted_exact_reciprocal": (1.0 / x2) if x2 not in (None, 0.0) else None,
        },
    )


def capture_recip_after(debugger):
    x2 = _xmm_f32s(_frame(debugger)[2], "xmm2")[0]
    _capture(debugger, "recip_after_rcpss_36a93c", {"rcpss_xmm2": x2})


def write_report(debugger, path):
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    if process.IsValid():
        state["process"] = {
            "state": str(process.GetState()),
            "exit_status": process.GetExitStatus(),
            "exit_description": process.GetExitDescription(),
        }
    state["breakpoints"] = []
    for bp in target.breakpoint_iter():
        state["breakpoints"].append({"id": bp.GetID(), "hit_count": bp.GetHitCount()})
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("L16_CODEX_W5_REPORT", path)
