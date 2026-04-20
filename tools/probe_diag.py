#!/usr/bin/env python3
"""
Diagnostic: run for 30s with one BP, print stop reasons.
"""
import sys, time, struct

LLDB_PYTHON = '/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python'
if LLDB_PYTHON not in sys.path:
    sys.path.insert(0, LLDB_PYTHON)
import lldb

LRI_PATH    = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH    = '/tmp/diag_probe.hdr'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

def main():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)  # async mode

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    assert target.IsValid()

    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH, '--profile', '2'])
    env = lldb.SBEnvironment()
    env.Set('DYLD_LIBRARY_PATH', LIBCP_DIR, True)
    launch_info.SetEnvironment(env, True)
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    err = lldb.SBError()
    process = target.Launch(launch_info, err)
    assert err.Success(), f"launch error: {err}"
    print(f"Launched PID={process.GetProcessID()}")

    # Wait for entry stop
    deadline = time.time() + 30
    while time.time() < deadline:
        s = process.GetState()
        print(f"  state: {debugger.StateAsCString(s)}")
        if s == lldb.eStateStopped:
            break
        time.sleep(0.5)

    print(f"At entry stop. Finding libcp...")
    libcp_base = None
    for i in range(target.GetNumModules()):
        m = target.GetModuleAtIndex(i)
        fn = m.GetFileSpec().GetFilename()
        if fn and 'libcp' in fn:
            a = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if a != lldb.LLDB_INVALID_ADDRESS:
                libcp_base = a
                print(f"libcp at 0x{a:x}")
                break

    if not libcp_base:
        print("libcp not found at entry, continuing past dyld...")
        process.Continue()
        time.sleep(3)
        process.Stop()
        time.sleep(1)
        for i in range(target.GetNumModules()):
            m = target.GetModuleAtIndex(i)
            fn = m.GetFileSpec().GetFilename()
            if fn and 'libcp' in fn:
                a = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
                if a != lldb.LLDB_INVALID_ADDRESS:
                    libcp_base = a
                    print(f"libcp at 0x{a:x}")
                    break

    if not libcp_base:
        print("ERROR: no libcp")
        process.Kill()
        return

    # Set ONE BP on IRAMP_body
    bp_addr = libcp_base + 0x3661b0
    bp = target.BreakpointCreateByAddress(bp_addr)
    print(f"BP IRAMP_body @ 0x{bp_addr:x}, valid={bp.IsValid()}, locs={bp.GetNumLocations()}")
    print(f"BP ID={bp.GetID()}")

    # Continue
    print("Continuing...")
    process.Continue()

    # Watch for 60s, log all stops
    stop_log = []
    deadline = time.time() + 60
    while time.time() < deadline:
        s = process.GetState()
        if s == lldb.eStateStopped:
            reasons = []
            for ti in range(process.GetNumThreads()):
                t = process.GetThreadAtIndex(ti)
                r = t.GetStopReason()
                reasons.append(f"thread[{ti}] reason={r}")
                if r == lldb.eStopReasonBreakpoint:
                    bid = t.GetStopReasonDataAtIndex(0)
                    reasons[-1] += f" bp_id={bid}"
                    f = t.GetFrameAtIndex(0)
                    pc = f.GetPC()
                    reasons[-1] += f" pc=0x{pc:x}"
            stop_log.append((time.time(), reasons))
            print(f"  STOP: {reasons}")
            if len(stop_log) >= 5:
                print("(got 5 stops, killing)")
                break
            process.Continue()
        elif s in (lldb.eStateExited, lldb.eStateCrashed):
            print(f"Process ended: {debugger.StateAsCString(s)}")
            break
        time.sleep(0.2)

    process.Kill()
    print("Done. Stops logged:")
    for ts, r in stop_log:
        print(f"  {r}")

if __name__ == '__main__':
    main()
