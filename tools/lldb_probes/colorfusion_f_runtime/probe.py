"""Capture one ColorFusionBayer patch and its emitted weight from libcp.

The probe deliberately records raw float32 bytes.  JSON summaries retain bit
patterns, while the companion verifier replays the installed SSE operation
order without relying on LLDB's float formatting.
"""

import json
import os
import struct

import lldb


STATE = {
    "active_rbp": 0,
    "n": 0,
    "modules": [],
    "numerator": None,
    "entry": None,
    "output": None,
    "done": False,
}
OUT_DIR = os.environ.get(
    "CF_RUNTIME_OUT",
    "/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/colorfusion_f_runtime/u1_28",
)
HARDWARE_ALL = os.environ.get("CF_RUNTIME_HARDWARE_ALL") == "1"


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(proc, addr, size):
    err = lldb.SBError()
    data = proc.ReadMemory(addr, size, err)
    if not err.Success() or len(data) != size:
        raise RuntimeError("read 0x%x+0x%x failed: %s" % (addr, size, err))
    return bytes(data)


def _u64(proc, addr):
    return struct.unpack("<Q", _read(proc, addr, 8))[0]


def _i32s(proc, addr, count):
    return list(struct.unpack("<%di" % count, _read(proc, addr, 4 * count)))


def _f32_record(raw):
    vals = struct.unpack("<%df" % (len(raw) // 4), raw)
    bits = struct.unpack("<%dI" % (len(raw) // 4), raw)
    return {"float": list(vals), "bits": ["0x%08x" % b for b in bits]}


def _write_blob(name, raw):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "wb") as f:
        f.write(raw)
    return os.path.basename(path)


def _arm(target, load_addr, callback):
    bp = target.BreakpointCreateByAddress(load_addr)
    bp.SetScriptCallbackFunction(callback)
    return bp


def _capture_entry(frame, vec, ref, out0, out1):
    proc = frame.GetThread().GetProcess()
    beg, end = _u64(proc, vec), _u64(proc, vec + 8)
    if end < beg or (end - beg) % 0x30:
        raise RuntimeError("invalid module vector 0x%x..0x%x" % (beg, end))
    n = (end - beg) // 0x30
    rows = []
    for k in range(n):
        raw = _read(proc, beg + 0x30 * k, 0x30)
        rows.append({
            "k": k,
            "raw_hex": raw.hex(),
            "i32": list(struct.unpack("<12i", raw)),
            "u64": ["0x%016x" % v for v in struct.unpack("<6Q", raw)],
        })
    STATE.update({
        "active_rbp": -1,
        "n": n,
        "entry": {
            "module_vector_object": "0x%x" % vec,
            "module_begin": "0x%x" % beg,
            "module_end": "0x%x" % end,
            "reference_descriptor": "0x%x" % ref,
            "reference_descriptor_raw_hex": _read(proc, ref, 0x30).hex(),
            "first_output_descriptor": "0x%x" % out0,
            "second_output_descriptor": "0x%x" % out1,
            "modules": rows,
        },
    })


def _capture_selection_from_stack(frame):
    """Join the worker capture to the owning ColorFusionBayer camera IDs."""
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module.IsValid():
        raise RuntimeError("libcp.dylib module not found")
    base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    for index in range(frame.GetThread().GetNumFrames()):
        candidate = frame.GetThread().GetFrameAtIndex(index)
        pc = candidate.GetPCAddress().GetLoadAddress(target)
        relative = pc - base
        if not (0x1AAB40 <= relative < 0x1AAF90):
            continue
        this = _reg(candidate, "r12")
        begin = _u64(process, this + 0x148)
        end = _u64(process, this + 0x150)
        if end < begin or (end - begin) % 4:
            raise RuntimeError("invalid camera vector 0x%x..0x%x" % (begin, end))
        count = (end - begin) // 4
        ids = _i32s(process, begin, count) if count else []
        STATE["camera_selection"] = {
            "process_caller": "libcp+0x%x" % relative,
            "object": "0x%x" % this,
            "target_camera_id": struct.unpack(
                "<i", _read(process, this + 0x140, 4)
            )[0],
            "source_camera_ids": ids,
            "mode_0x198": _read(process, this + 0x198, 1)[0],
            "initialized_0x199": _read(process, this + 0x199, 1)[0],
        }
        return
    raise RuntimeError("ColorFusionBayer::process caller not found in stack")


def on_entry(frame, bp_loc, internal_dict):
    """Enter at a Rosetta-safe function boundary, then arm the first inner stop."""
    proc = frame.GetThread().GetProcess()
    _capture_entry(
        frame,
        _reg(frame, "rcx"),
        _reg(frame, "rdx"),
        _reg(frame, "rdi"),
        _reg(frame, "rsi"),
    )
    target = proc.GetTarget()
    pc = frame.GetPCAddress().GetLoadAddress(target)
    target.BreakpointDelete(bp_loc.GetBreakpoint().GetID())
    _arm(target, pc + (0x19D096 - 0x19C790), "probe.on_wiener_call")
    return False


def on_wiener_call(frame, bp_loc, internal_dict):
    """Capture the exact 256xvec4 operands passed to 0x18eb00."""
    if STATE["done"]:
        return False
    proc = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    if STATE["active_rbp"] == 0:
        _capture_entry(
            frame,
            _u64(proc, rbp - 0x5388),
            _u64(proc, rbp - 0x53D0),
            _u64(proc, rbp - 0x5408),
            _u64(proc, rbp - 0x5400),
        )
    if STATE["active_rbp"] == -1:
        STATE["active_rbp"] = rbp
    if rbp != STATE["active_rbp"] or len(STATE["modules"]) >= STATE["n"]:
        return False

    k = _reg(frame, "r14")
    source_addr = _reg(frame, "rdi")
    reference_addr = _reg(frame, "rdx")
    coeff_addr = _reg(frame, "rcx")
    noise_addr = _reg(frame, "r8")
    source = _read(proc, source_addr, 0x1000)
    reference = _read(proc, reference_addr, 0x1000)
    coeff = _read(proc, coeff_addr, 0x1000)
    noise = _read(proc, noise_addr, 0x10)
    prefix = "module_%02d" % k
    rec = {
        "sequence": len(STATE["modules"]),
        "k_register": k,
        "patch_xyxy": _i32s(proc, rbp - 0x52b0, 4),
        "source_roi_xyxy": _i32s(proc, rbp - 0x52d8, 4),
        "source_addr": "0x%x" % source_addr,
        "reference_addr": "0x%x" % reference_addr,
        "source_file": _write_blob(prefix + "_source_vec4_f32.bin", source),
        "reference_file": _write_blob(prefix + "_reference_vec4_f32.bin", reference),
        "coeff_file": _write_blob(prefix + "_coeff_vec4_f32.bin", coeff),
        "noise": _f32_record(noise),
    }
    STATE["modules"].append(rec)
    if not HARDWARE_ALL:
        pre = bp_loc.GetBreakpoint()
        pre.SetEnabled(False)
        STATE["pre_bp_id"] = pre.GetID()
        target = proc.GetTarget()
        pc = frame.GetPCAddress().GetLoadAddress(target)
        _arm(target, pc + 5, "probe.on_wiener_return")
    return False


def on_wiener_return(frame, bp_loc, internal_dict):
    if STATE["done"] or not STATE["modules"]:
        return False
    rbp = _reg(frame, "rbp")
    if rbp != STATE["active_rbp"]:
        return False
    rec = STATE["modules"][-1]
    if "m" not in rec:
        rec["m"] = _f32_record(_read(frame.GetThread().GetProcess(), rbp - 0x52f0, 0x10))
    if not HARDWARE_ALL:
        target = frame.GetThread().GetProcess().GetTarget()
        target.BreakpointDelete(bp_loc.GetBreakpoint().GetID())
        if len(STATE["modules"]) < STATE["n"]:
            target.FindBreakpointByID(STATE["pre_bp_id"]).SetEnabled(True)
        else:
            pc = frame.GetPCAddress().GetLoadAddress(target)
            _arm(target, pc + (0x19D514 - 0x19D09B), "probe.on_numerator")
    return False


def on_numerator(frame, bp_loc, internal_dict):
    if STATE["done"] or STATE["numerator"] is not None:
        return False
    rbp = _reg(frame, "rbp")
    if rbp != STATE["active_rbp"] or len(STATE["modules"]) != STATE["n"]:
        return False
    proc = frame.GetThread().GetProcess()
    STATE["numerator"] = {
        "A": _f32_record(_read(proc, rbp - 0x5380, 0x10)),
        "B": _f32_record(_read(proc, rbp - 0x5370, 0x10)),
        "A2_plus_B": _f32_record(_read(proc, rbp - 0x5330, 0x10)),
    }
    if not HARDWARE_ALL:
        target = proc.GetTarget()
        target.BreakpointDelete(bp_loc.GetBreakpoint().GetID())
        pc = frame.GetPCAddress().GetLoadAddress(target)
        _arm(target, pc + (0x19D69A - 0x19D514), "probe.on_output")
    return False


def on_output(frame, bp_loc, internal_dict):
    """Capture the normalized second-output descriptor, then end the run."""
    if STATE["done"]:
        return False
    rbp = _reg(frame, "rbp")
    if rbp != STATE["active_rbp"] or STATE["numerator"] is None:
        return False
    proc = frame.GetThread().GetProcess()
    desc = _u64(proc, rbp - 0x5400)
    raw = _read(proc, desc, 0x30)
    STATE["output"] = {
        "descriptor": "0x%x" % desc,
        "raw_hex": raw.hex(),
        "i32": list(struct.unpack("<12i", raw)),
        "u64": ["0x%016x" % v for v in struct.unpack("<6Q", raw)],
    }
    STATE["done"] = True
    summarize()
    if not HARDWARE_ALL:
        proc.GetTarget().BreakpointDelete(bp_loc.GetBreakpoint().GetID())
    proc.Kill()
    return False


def summarize():
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "capture.json")
    with open(path, "w") as f:
        json.dump(STATE, f, indent=2, sort_keys=True)
    print("CF_RUNTIME_SUMMARY " + path)


def manual_pre(frame):
    """Synchronous LLDB entry helper used with `thread step-out`."""
    proc = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    if STATE["active_rbp"] == 0:
        _capture_entry(
            frame,
            _u64(proc, rbp - 0x5388),
            _u64(proc, rbp - 0x53D0),
            _u64(proc, rbp - 0x5408),
            _u64(proc, rbp - 0x5400),
        )
        STATE["active_rbp"] = rbp
        _capture_selection_from_stack(frame)
        proc.GetTarget().FindBreakpointByID(1).SetThreadID(
            frame.GetThread().GetThreadID()
        )
    if rbp != STATE["active_rbp"]:
        raise RuntimeError("worker frame changed")
    k = _reg(frame, "r14")
    source_addr = _reg(frame, "rdi")
    reference_addr = _reg(frame, "rdx")
    coeff_addr = _reg(frame, "rcx")
    noise_addr = _reg(frame, "r8")
    prefix = "module_%02d" % k
    STATE["modules"].append({
        "sequence": len(STATE["modules"]),
        "k_register": k,
        "patch_xyxy": _i32s(proc, rbp - 0x52B0, 4),
        "source_roi_xyxy": _i32s(proc, rbp - 0x52D8, 4),
        "source_addr": "0x%x" % source_addr,
        "reference_addr": "0x%x" % reference_addr,
        "source_file": _write_blob(
            prefix + "_source_vec4_f32.bin", _read(proc, source_addr, 0x1000)
        ),
        "reference_file": _write_blob(
            prefix + "_reference_vec4_f32.bin", _read(proc, reference_addr, 0x1000)
        ),
        "coeff_file": _write_blob(
            prefix + "_coeff_vec4_f32.bin", _read(proc, coeff_addr, 0x1000)
        ),
        "noise": _f32_record(_read(proc, noise_addr, 0x10)),
    })
    summarize()


def manual_post(frame):
    rbp = _reg(frame, "rbp")
    if rbp != STATE["active_rbp"] or not STATE["modules"]:
        raise RuntimeError("return is not the captured worker")
    STATE["modules"][-1]["m"] = _f32_record(
        _read(frame.GetThread().GetProcess(), rbp - 0x52F0, 0x10)
    )
    summarize()


def manual_numerator(frame):
    rbp = _reg(frame, "rbp")
    if rbp != STATE["active_rbp"]:
        raise RuntimeError("numerator is not the captured worker")
    proc = frame.GetThread().GetProcess()
    STATE["numerator"] = {
        "A": _f32_record(_read(proc, rbp - 0x5380, 0x10)),
        "B": _f32_record(_read(proc, rbp - 0x5370, 0x10)),
        "A2_plus_B": _f32_record(_read(proc, rbp - 0x5330, 0x10)),
    }
    ret = _u64(proc, rbp + 8)
    bp = proc.GetTarget().BreakpointCreateByAddress(ret)
    bp.SetOneShot(True)
    bp.SetThreadID(frame.GetThread().GetThreadID())
    STATE["worker_return"] = "0x%x" % ret
    STATE["return_bp_id"] = bp.GetID()
    summarize()


def arm_numerator(frame):
    target = frame.GetThread().GetProcess().GetTarget()
    pc = frame.GetPCAddress().GetLoadAddress(target)
    bp = target.BreakpointCreateByAddress(pc + (0x19D514 - 0x19D09B))
    bp.SetOneShot(True)
    bp.SetThreadID(frame.GetThread().GetThreadID())
    STATE["numerator_bp_id"] = bp.GetID()


def manual_output(frame):
    proc = frame.GetThread().GetProcess()
    desc = int(STATE["entry"]["second_output_descriptor"], 16)
    raw = _read(proc, desc, 0x30)
    data_ptr = struct.unpack_from("<Q", raw, 0x20)[0]
    data = _read(proc, data_ptr, 0x1000)
    STATE["output"] = {
        "descriptor": "0x%x" % desc,
        "raw_hex": raw.hex(),
        "i32": list(struct.unpack("<12i", raw)),
        "u64": ["0x%016x" % v for v in struct.unpack("<6Q", raw)],
        "first_256_vec4_file": _write_blob("output_first_256_vec4_f32.bin", data),
        "first_8_vec4": _f32_record(data[: 8 * 16]),
    }
    STATE["done"] = True
    summarize()
