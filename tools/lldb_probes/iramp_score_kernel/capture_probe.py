import builtins
import json
import os
import struct


def reset(output_dir, min_score=0.05):
    builtins.l16_iramp_score_capture = {
        "output_dir": output_dir,
        "min_score": min_score,
        "captured": False,
        "pairs_seen": 0,
        "error": None,
    }
    builtins.l16_iramp_score_pending = {}


def _state():
    return builtins.l16_iramp_score_capture


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def capture(frame, bp_loc, internal_dict):
    state = _state()
    if state["captured"]:
        return False

    process = frame.GetThread().GetProcess()
    scratch_address = _reg(frame, "rdi")
    candidate_address = _reg(frame, "rsi")
    scratch = _read(process, scratch_address, 0x2800)
    candidate = _read(process, candidate_address, 0x1000)
    if scratch is None or candidate is None:
        state["error"] = "failed to read score inputs"
        process.Kill()
        return False

    thread_id = frame.GetThread().GetThreadID()
    builtins.l16_iramp_score_pending[thread_id] = {
        "scratch": scratch,
        "candidate": candidate,
        "metadata": {
            "site": "libcp+0x369e3f",
            "score_target": "libcp+0x36cde0",
            "scratch_address": scratch_address,
            "candidate_address": candidate_address,
            "scratch_size": len(scratch),
            "candidate_size": len(candidate),
            "scratch_first_vec4": list(struct.unpack_from("<4f", scratch, 0)),
            "candidate_first_vec4": list(
                struct.unpack_from("<4f", candidate, 0)
            ),
            "thread_id": thread_id,
        },
    }
    return False


def capture_return(frame, bp_loc, internal_dict):
    state = _state()
    if state["captured"]:
        return False
    thread_id = frame.GetThread().GetThreadID()
    packet = builtins.l16_iramp_score_pending.pop(thread_id, None)
    if packet is None:
        return False
    lldb = builtins.__import__("lldb")
    data = frame.FindRegister("xmm0").GetData()
    error = lldb.SBError()
    score = data.GetFloat(error, 0)
    if not error.Success():
        state["error"] = "failed to read xmm0 return"
        frame.GetThread().GetProcess().Kill()
        return False
    state["pairs_seen"] += 1
    if score < state["min_score"]:
        return False

    output_dir = state["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "scratch.bin"), "wb") as handle:
        handle.write(packet["scratch"])
    with open(os.path.join(output_dir, "candidate.bin"), "wb") as handle:
        handle.write(packet["candidate"])
    score_bits = struct.unpack("<I", struct.pack("<f", score))[0]
    metadata = packet["metadata"]
    metadata["live_score"] = score
    metadata["live_score_bits"] = score_bits
    metadata["pairs_seen"] = state["pairs_seen"]
    with open(os.path.join(output_dir, "capture.json"), "w") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    state["captured"] = True
    state["live_score"] = score
    state["live_score_bits"] = score_bits
    state["thread_id"] = thread_id
    frame.GetThread().GetProcess().Kill()
    return False


def report():
    print("L16_IRAMP_SCORE_CAPTURE", json.dumps(_state(), sort_keys=True))
