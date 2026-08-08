"""Dump every prologue-derived stack slot of highlight-restore kernel 0x30b9f0.

BP at 0x30bcae -- just after the last prologue store (movaps [rbp-0x270], xmm8).
"""
import struct, json, builtins
import lldb

SLOTS = [0x260, 0x1f0, 0x100, 0x270, 0xe0, 0xd0, 0x180, 0x1b0, 0xf0,
         0x170, 0x1c0, 0x1d0, 0x1e0, 0x160, 0x250, 0x24c, 0x13c, 0x140,
         0x200, 0x1a0, 0x190, 0x150, 0x110]
INTS = [0x134, 0x138, 0x94, 0x104, 0x294, 0x2b4, 0x2a8, 0x240]


def reset(outpath):
    builtins.l16_c = {"out": outpath, "done": False, "d": {}}


def hit(frame, bp_loc, internal_dict):
    st = builtins.l16_c
    if st["done"]:
        return False
    st["done"] = True
    try:
        bp_loc.GetBreakpoint().SetEnabled(False)
    except Exception:
        pass
    proc = frame.GetThread().GetProcess()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    d = st["d"]
    for off in SLOTS:
        e = lldb.SBError()
        b = proc.ReadMemory(rbp - off, 16, e)
        if e.Success():
            d["f_0x%x" % off] = list(struct.unpack("<4f", b))
    for off in INTS:
        e = lldb.SBError()
        b = proc.ReadMemory(rbp - off, 4, e)
        if e.Success():
            d["i_0x%x" % off] = struct.unpack("<i", b)[0]
    return False


def drive(debugger, cap=2000000):
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while n < cap:
        s = proc.GetState()
        if s != lldb.eStateStopped:
            break
        proc.Continue()
        n += 1
    print("L16_C drive iterations=%d state=%d" % (n, proc.GetState()))


def report():
    st = builtins.l16_c
    print("L16_C_BEGIN")
    for k in sorted(st["d"]):
        print(k, st["d"][k])
    open(st["out"], "w").write(json.dumps(st["d"], indent=1))
    print("L16_C_END")
