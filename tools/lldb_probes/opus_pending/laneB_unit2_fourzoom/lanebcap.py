"""Lane B Unit-2 four-zoom capture, run as a single python function from lldb.

Entry: lanebcap.run(lldb, zoom, lri, result_path)

Assumes the process is stopped at `main`. Computes libcp_base, dumps the anchor
disasm at base+0x3eced0 (checks for mulps/maxps/sqrtps), sets a BARE breakpoint
at base+0x369fa4 (the IRAMP accumulator addps), deletes the main breakpoint,
continues, and on the FIRST hit reads the 16 coeff floats at $rbp-0xa0 plus
regs and a short backtrace. Writes everything to result_path as JSON.
"""

import struct
import json


def _libcp_base(target):
    for m in target.module_iter():
        if (m.GetFileSpec().GetFilename() or "") == "libcp.dylib":
            return m.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return None


def run(lldb, zoom, lri, result_path):
    tg = lldb.debugger.GetSelectedTarget()
    base = _libcp_base(tg)
    rec = {"zoom": zoom, "lri": lri}
    if base is None:
        rec["error"] = "libcp_base not found"
        open(result_path, "w").write(json.dumps(rec, indent=2))
        print("LANEB_RESULT_WRITTEN", result_path, "(no base)")
        return
    rec["libcp_base"] = hex(base)
    rec["anchor_va"] = hex(base + 0x3ECED0)
    rec["bp_va"] = hex(base + 0x369FA4)

    # Anchor disasm.
    ins = list(tg.ReadInstructions(lldb.SBAddress(base + 0x3ECED0, tg), 14))
    mn = [i.GetMnemonic(tg) for i in ins]
    rec["anchor_mnemonics"] = mn
    rec["anchor_disasm"] = ["%s %s" % (i.GetMnemonic(tg), i.GetOperands(tg))
                            for i in ins]
    rec["anchorPassed"] = bool("mulps" in mn and "maxps" in mn
                               and "sqrtps" in mn)
    print("LANEB_BASE", hex(base), "ANCHOR_VA", rec["anchor_va"],
          "BP_VA", rec["bp_va"])
    print("anchorPassed", rec["anchorPassed"], "mnemonics", mn)

    # Bare BP at IRAMP accumulator; delete main; continue.
    bp = tg.BreakpointCreateByAddress(base + 0x369FA4)
    rec["bp_locs"] = bp.GetNumLocations()
    print("LANEB_BPSET locs", bp.GetNumLocations(), "id", bp.GetID())
    # delete main (breakpoint id 1)
    tg.BreakpointDelete(1)

    proc = tg.GetProcess()
    proc.Continue()
    st = proc.GetState()
    rec["state_after_continue"] = int(st)
    print("LANEB_STATE_AFTER_CONTINUE", st)

    if st != lldb.eStateStopped:
        rec["capture"] = "NO_FIRST_HIT_PROCESS_EXITED"
        rec["coeff16"] = None
        open(result_path, "w").write(json.dumps(rec, indent=2))
        print("LANEB_RESULT_WRITTEN", result_path, "(no first hit)")
        print("LANEB_COEFF16", None)
        return

    thread = proc.GetSelectedThread()
    f = thread.GetFrameAtIndex(0)
    rbp = f.FindRegister("rbp").GetValueAsUnsigned()
    e = lldb.SBError()
    d = proc.ReadMemory(rbp - 0xA0, 64, e)
    if d and len(d) == 64 and e.Success():
        rec["coeff16"] = list(struct.unpack("<16f", d))
    else:
        rec["coeff16"] = None
        rec["read_err"] = str(e)
    rec["regs"] = {r: hex(f.FindRegister(r).GetValueAsUnsigned())
                   for r in ["rdi", "rdx", "rax", "rsi", "rcx", "rip", "rbp"]}
    bt = []
    n = min(10, thread.GetNumFrames())
    for i in range(n):
        fi = thread.GetFrameAtIndex(i)
        bt.append("#%d %s" % (i, fi.GetFunctionName() or hex(fi.GetPC())))
    rec["bt"] = bt

    open(result_path, "w").write(json.dumps(rec, indent=2))
    print("LANEB_RESULT_WRITTEN", result_path)
    print("LANEB_COEFF16", rec["coeff16"])
