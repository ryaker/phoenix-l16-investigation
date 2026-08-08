"""Stage-3 normalization: who allocates/fills the SensorCharacterization record?

Breaks at libcp.dylib 0x352ce0 and, on the first hit whose black_level != 42.0f,
captures the live backtrace plus the MallocStackLogging allocation history for
the record address (SBProcess.GetHistoryThreads).
"""

import struct

import lldb

_STATE = {"done": False, "out": "/tmp/blackprobe2.txt", "n": 0}


def reset(out_path):
    _STATE["done"] = False
    _STATE["n"] = 0
    _STATE["out"] = out_path


def _rd(proc, addr, n):
    err = lldb.SBError()
    b = proc.ReadMemory(addr, n, err)
    return b if err.Success() else None


def _frames(thread, limit=40):
    out = []
    for i in range(min(thread.GetNumFrames(), limit)):
        f = thread.GetFrameAtIndex(i)
        pc = f.GetPC()
        mod = f.GetModule()
        name = mod.GetFileSpec().GetFilename() if mod else "?"
        base = 0
        if mod:
            for s in mod.section_iter():
                if s.GetName() == "__TEXT":
                    base = s.GetLoadAddress(f.GetThread().GetProcess().GetTarget())
                    break
        off = pc - base if base else 0
        out.append("  #%02d %s+0x%x  pc=0x%x  %s" % (i, name, off, pc, f.GetFunctionName()))
    return out


def _history(proc, addr, tag, lines):
    lines.append("### malloc history %s 0x%x" % (tag, addr))
    tc = proc.GetHistoryThreads(addr)
    n = tc.GetSize()
    lines.append("  history threads: %d" % n)
    for i in range(n):
        th = tc.GetThreadAtIndex(i)
        lines.append(" -- history thread %d: %s" % (i, th.GetQueueName() or th.GetName()))
        lines.extend(_frames(th))


def on_hit(frame, bp_loc, internal_dict):
    if _STATE["done"]:
        return False
    thread = frame.GetThread()
    proc = thread.GetProcess()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    head = _rd(proc, rdi, 8)
    if not head:
        return False
    obj = struct.unpack_from("<Q", head, 0)[0]
    ob = _rd(proc, obj, 0x1A0)
    if not ob:
        return False
    sc = struct.unpack_from("<Q", ob, 0x198)[0]
    scb = _rd(proc, sc, 16)
    if not scb:
        return False
    black = struct.unpack_from("<f", scb, 4)[0]
    _STATE["n"] += 1
    if black == 42.0:
        return False

    lines = ["hit#%d obj=0x%x sc=0x%x black=%r" % (_STATE["n"], obj, sc, black),
             "### live backtrace"]
    lines.extend(_frames(thread))
    try:
        _history(proc, sc, "sc", lines)
    except Exception as exc:  # noqa: BLE001
        lines.append("  history sc failed: %r" % (exc,))
    try:
        _history(proc, obj, "obj", lines)
    except Exception as exc:  # noqa: BLE001
        lines.append("  history obj failed: %r" % (exc,))
    with open(_STATE["out"], "w", encoding="utf-8", errors="replace") as fh:
        fh.write("\n".join(lines))
    _STATE["done"] = True
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for bp in target.breakpoint_iter():
        bp.SetScriptCallbackFunction("black_probe2.on_hit")
