#!/usr/bin/env python3
"""
Stop at _main, enumerate actual libcp base, set bp at LinearizeAndColorScale,
then continue. Report whether bp fires.
"""
import lldb
import time

LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH = '/tmp/probe_stop.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

LINEARIZE_OFFSET = 0x352ce0
AWB_OFFSET = 0x3510f0

def wait_stopped(process, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = process.GetState()
        if st == lldb.eStateStopped:
            return 'stopped'
        if st == lldb.eStateExited:
            return 'exited'
        if st == lldb.eStateCrashed:
            return 'crashed'
        time.sleep(0.05)
    return 'timeout'

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: target invalid")
        return

    # Launch with stop at entry so we can enumerate modules
    error = lldb.SBError()
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry | lldb.eLaunchFlagDisableASLR)

    process = target.Launch(launch_info, error)
    if error.Fail():
        print(f"Launch error: {error.GetCString()}")
        return

    print(f"PID: {process.GetProcessID()}")

    # Wait for initial stop at entry
    result = wait_stopped(process, timeout=15)
    print(f"Entry stop: {result}")
    if result != 'stopped':
        return

    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    print(f"Entry PC: 0x{frame.GetPC():x}")

    # Continue to let dyld load all libraries, then stop again
    # Set a bp at _main so we stop after libraries are loaded
    # _main is at 0x100000820 in lri_process
    MAIN_OFFSET = 0x820  # within lri_process text
    lri_module = None
    for m in target.module_iter():
        name = str(m.GetFileSpec().GetFilename())
        if 'lri_process' in name:
            lri_module = m
            break

    if lri_module:
        lri_base = lri_module.GetObjectFileHeaderAddress().GetLoadAddress(target)
        main_addr = lri_base + MAIN_OFFSET
        print(f"lri_process base: 0x{lri_base:x}, _main addr: 0x{main_addr:x}")
        bp_main = target.BreakpointCreateByAddress(main_addr)
        print(f"  _main bp: valid={bp_main.IsValid()}, locs={bp_main.GetNumLocations()}")
    else:
        print("lri_process module not found at entry; using fixed addr")
        bp_main = target.BreakpointCreateByAddress(0x100000820)

    # Continue past dyld entry to _main
    process.Continue()
    result = wait_stopped(process, timeout=20)
    print(f"\nPost-dyld stop: {result}")
    if result != 'stopped':
        print("Never reached _main!")
        process.Kill()
        return

    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    print(f"At _main PC: 0x{frame.GetPC():x}")

    # NOW enumerate loaded modules — all dylibs should be loaded
    print("\nLoaded modules (relevant):")
    libcp_base = None
    for m in target.module_iter():
        name = str(m.GetFileSpec().GetFilename())
        hdr = m.GetObjectFileHeaderAddress()
        base = hdr.GetLoadAddress(target)
        if 'libcp' in name and 'libcpan' not in name:
            libcp_base = base
            print(f"  *** {name}: base=0x{base:x} ***")
        elif 'lri' in name.lower() or 'light' in name.lower():
            print(f"  {name}: base=0x{base:x}")

    if libcp_base is None:
        # Try to find it by iterating all
        print("libcp not found yet, listing all:")
        for m in target.module_iter():
            name = str(m.GetFileSpec().GetFilename())
            hdr = m.GetObjectFileHeaderAddress()
            base = hdr.GetLoadAddress(target)
            print(f"  {name}: base=0x{base:x}")
        process.Kill()
        return

    # Compute target addresses
    linearize_addr = libcp_base + LINEARIZE_OFFSET
    awb_addr = libcp_base + AWB_OFFSET
    print(f"\nLinearizeAndColorScale: 0x{linearize_addr:x} (libcp+0x{LINEARIZE_OFFSET:x})")
    print(f"AWB kernel:             0x{awb_addr:x} (libcp+0x{AWB_OFFSET:x})")

    # Verify bytes at these addresses
    err = lldb.SBError()
    bytes_lin = process.ReadMemory(linearize_addr, 4, err)
    if err.Success():
        import struct
        b = bytes(bytes_lin)
        print(f"Bytes at LinearizeAndColorScale: {b.hex()} (expect: 55 48 89 e5)")
    else:
        print(f"Cannot read memory at 0x{linearize_addr:x}: {err.GetCString()}")

    # Delete _main bp
    target.BreakpointDelete(bp_main.GetID())

    # Set bp at LinearizeAndColorScale
    bp_lin = target.BreakpointCreateByAddress(linearize_addr)
    bp_awb = target.BreakpointCreateByAddress(awb_addr)
    print(f"\nbp_lin: valid={bp_lin.IsValid()}, locs={bp_lin.GetNumLocations()}")
    print(f"bp_awb: valid={bp_awb.IsValid()}, locs={bp_awb.GetNumLocations()}")

    # Also set bp at bayer_lut builder as sanity check
    bayer_addr = libcp_base + 0x33d6a0
    bp_bayer = target.BreakpointCreateByAddress(bayer_addr)
    print(f"bp_bayer(0x33d6a0): valid={bp_bayer.IsValid()}, locs={bp_bayer.GetNumLocations()}")

    # Continue and wait for any bp hit or exit
    print("\nContinuing, waiting for breakpoint...")
    process.Continue()

    deadline = time.time() + 120
    hit_count = 0
    while time.time() < deadline:
        st = process.GetState()
        if st == lldb.eStateStopped:
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            stop_reason = thread.GetStopReason()

            if stop_reason == lldb.eStopReasonBreakpoint:
                hit_count += 1
                offset = pc - libcp_base
                fname = frame.GetFunctionName()
                print(f"\n*** BP HIT #{hit_count} at 0x{pc:x} (libcp+0x{offset:x}) ***")
                print(f"  Function: {fname}")

                # Print call stack
                for i in range(min(8, thread.GetNumFrames())):
                    f = thread.GetFrameAtIndex(i)
                    foff = f.GetPC() - libcp_base
                    print(f"  [{i}] libcp+0x{foff:x} {f.GetFunctionName()}")

                if hit_count >= 3:
                    print("(stopping after 3 hits)")
                    break

                process.Continue()
            elif stop_reason == lldb.eStopReasonWatchpoint:
                pc_off = pc - libcp_base
                print(f"\n*** WATCHPOINT at 0x{pc:x} (libcp+0x{pc_off:x}) ***")
                for i in range(min(6, thread.GetNumFrames())):
                    f = thread.GetFrameAtIndex(i)
                    foff = f.GetPC() - libcp_base
                    print(f"  [{i}] libcp+0x{foff:x} {f.GetFunctionName()}")
                break
            elif stop_reason == lldb.eStopReasonSignal:
                sig = thread.GetStopReasonDataAtIndex(0)
                import signal
                try:
                    signame = signal.Signals(sig).name
                except:
                    signame = str(sig)
                print(f"  Signal {signame} - continuing")
                process.Continue()
            else:
                if pc != 0xffffffffffffffff:
                    print(f"  Unexplained stop at 0x{pc:x}, reason={stop_reason} - continuing")
                process.Continue()

        elif st == lldb.eStateExited:
            exit_code = process.GetExitStatus()
            print(f"\nProcess exited: code={exit_code}")
            if hit_count == 0:
                print("NONE of the breakpoints were hit!")
            break
        elif st == lldb.eStateCrashed:
            print("\nProcess CRASHED")
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            print(f"  PC: 0x{frame.GetPC():x}")
            for i in range(min(6, thread.GetNumFrames())):
                f = thread.GetFrameAtIndex(i)
                print(f"  [{i}] 0x{f.GetPC():x} {f.GetFunctionName()}")
            break
        else:
            time.sleep(0.1)

    process.Kill()
    lldb.SBDebugger.Destroy(debugger)
    print("\nDone.")

if __name__ == '__main__':
    run()
