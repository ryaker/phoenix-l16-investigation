#!/usr/bin/env python3
"""
Diagnostic v2: verify BP fires on IRAMP body, log thread/BP details.
Key change: don't force-stop after dyld init. Instead wait longer for
the process to load fully (it will output something), then set BPs.
Use async=True and poll state cleanly.
"""
import sys, time, struct, os

LLDB_PYTHON = '/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python'
if LLDB_PYTHON not in sys.path:
    sys.path.insert(0, LLDB_PYTHON)
import lldb

LRI_PATH    = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH    = '/tmp/diag2_probe.hdr'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

def find_libcp(target):
    for i in range(target.GetNumModules()):
        m = target.GetModuleAtIndex(i)
        fn = m.GetFileSpec().GetFilename()
        if fn and 'libcp' in fn:
            a = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if a != lldb.LLDB_INVALID_ADDRESS and a > 0:
                return a
    return None

def main():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    assert target.IsValid(), "invalid target"

    # Launch WITHOUT stop at entry — let it run freely
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH, '--profile', '2'])
    env = lldb.SBEnvironment()
    env.Set('DYLD_LIBRARY_PATH', LIBCP_DIR, True)
    launch_info.SetEnvironment(env, True)
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    # No stop at entry — process runs freely

    err = lldb.SBError()
    process = target.Launch(launch_info, err)
    assert err.Success(), f"launch: {err}"
    print(f"Launched PID={process.GetProcessID()} (no stop at entry)")

    # Wait briefly for dyld to load everything, then interrupt
    time.sleep(2)
    print("Interrupting to set BPs...")
    process.Stop()
    time.sleep(1)

    s = process.GetState()
    print(f"State after Stop(): {debugger.StateAsCString(s)}")

    libcp_base = find_libcp(target)
    print(f"libcp: {'0x{:x}'.format(libcp_base) if libcp_base else 'NOT FOUND'}")
    if not libcp_base:
        print("All modules:")
        for i in range(target.GetNumModules()):
            m = target.GetModuleAtIndex(i)
            a = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            print(f"  {m.GetFileSpec().GetFilename()} @ 0x{a:x}")
        process.Kill()
        return

    # Set BPs
    bp_addr = libcp_base + 0x3661b0
    bp = target.BreakpointCreateByAddress(bp_addr)
    bp2_addr = libcp_base + 0x3e0330  # SIC_init
    bp2 = target.BreakpointCreateByAddress(bp2_addr)
    bp3_addr = libcp_base + 0x3f6170  # dispatcher
    bp3 = target.BreakpointCreateByAddress(bp3_addr)

    print(f"IRAMP_body BP: valid={bp.IsValid()} locs={bp.GetNumLocations()} @ 0x{bp_addr:x}")
    print(f"SIC_init BP:   valid={bp2.IsValid()} locs={bp2.GetNumLocations()} @ 0x{bp2_addr:x}")
    print(f"Dispatcher BP: valid={bp3.IsValid()} locs={bp3.GetNumLocations()} @ 0x{bp3_addr:x}")

    # Check disasm at BP address to verify it looks like function entry
    instrs = target.ReadInstructions(lldb.SBAddress(bp_addr, target), 3)
    print(f"\nDisasm at IRAMP_body (0x{bp_addr:x}):")
    for ins in instrs:
        print(f"  0x{ins.GetAddress().GetLoadAddress(target):x}: {ins.GetMnemonic(target)} {ins.GetOperands(target)}")

    instrs2 = target.ReadInstructions(lldb.SBAddress(bp2_addr, target), 3)
    print(f"\nDisasm at SIC_init (0x{bp2_addr:x}):")
    for ins in instrs2:
        print(f"  0x{ins.GetAddress().GetLoadAddress(target):x}: {ins.GetMnemonic(target)} {ins.GetOperands(target)}")

    # Resume and count BP hits for up to 120s
    print("\nResuming and watching for BP hits (120s timeout)...")
    process.Continue()

    hit_iramp = 0
    hit_sic = 0
    hit_disp = 0
    start = time.time()
    deadline = start + 120
    last_report = start

    while time.time() < deadline:
        s = process.GetState()
        if s == lldb.eStateExited:
            print(f"\nProcess exited (code={process.GetExitStatus()}) at {time.time()-start:.1f}s")
            break
        if s == lldb.eStateCrashed:
            print(f"\nCrash at {time.time()-start:.1f}s")
            break
        if s == lldb.eStateStopped:
            # Check threads for BP reason
            any_bp = False
            for ti in range(process.GetNumThreads()):
                t = process.GetThreadAtIndex(ti)
                r = t.GetStopReason()
                if r == lldb.eStopReasonBreakpoint:
                    any_bp = True
                    bid = t.GetStopReasonDataAtIndex(0)
                    f = t.GetFrameAtIndex(0)
                    pc = f.GetPC() if f.IsValid() else 0
                    if bid == bp.GetID():
                        hit_iramp += 1
                        if hit_iramp <= 3:
                            print(f"  IRAMP hit #{hit_iramp} @ 0x{pc:x} thread[{ti}]")
                    elif bid == bp2.GetID():
                        hit_sic += 1
                        if hit_sic <= 10:
                            # read cam_id
                            rdi = f.FindRegister('rdi').GetValueAsUnsigned()
                            rsi = f.FindRegister('rsi').GetValueAsUnsigned()
                            print(f"  SIC hit #{hit_sic} rdi=0x{rdi:x} rsi=0x{rsi:x}")
                    elif bid == bp3.GetID():
                        hit_disp += 1
                        if hit_disp <= 20:
                            rsi = f.FindRegister('rsi').GetValueAsUnsigned()
                            print(f"  DISP hit #{hit_disp} rsi={rsi} (cam_id?)")
            if not any_bp:
                # Not a BP stop — check reason
                for ti in range(process.GetNumThreads()):
                    t = process.GetThreadAtIndex(ti)
                    r = t.GetStopReason()
                    if r != lldb.eStopReasonNone:
                        print(f"  Non-BP stop: thread[{ti}] reason={r}")
            process.Continue()

        if time.time() - last_report > 10:
            print(f"  [{time.time()-start:.0f}s] IRAMP={hit_iramp} SIC={hit_sic} DISP={hit_disp}")
            last_report = time.time()
        time.sleep(0.05)

    print(f"\nFinal: IRAMP={hit_iramp} SIC={hit_sic} DISP={hit_disp}")
    if os.path.exists(OUT_PATH):
        print(f"Output: {OUT_PATH} ({os.path.getsize(OUT_PATH)/1e6:.1f} MB)")
    process.Kill()

if __name__ == '__main__':
    main()
