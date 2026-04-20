#!/usr/bin/env python3
"""
LLDB Python API script v3 - better event handling
"""
import lldb
import struct
import time

LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH = '/tmp/test_wb_python3.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

LINEARIZE_OFFSET = 0x352ce0
AWB_KERNEL_OFFSET = 0x3510f0
KNOWN_LIBCP_BASE = 0x108c7a000

def wait_for_stop(process, listener, timeout_sec=30):
    """Wait for stop event using listener"""
    deadline = time.time() + timeout_sec
    event = lldb.SBEvent()

    while time.time() < deadline:
        if listener.WaitForEvent(1, event):
            if lldb.SBProcess.EventIsProcessEvent(event):
                state = lldb.SBProcess.GetStateFromEvent(event)
                state_str = lldb.SBDebugger.StateAsCString(state)
                if state == lldb.eStateStopped:
                    return 'stopped', state
                elif state in [lldb.eStateExited, lldb.eStateCrashed, lldb.eStateDetached]:
                    return state_str, state
    return 'timeout', None

def get_float32(process, addr):
    err = lldb.SBError()
    data = process.ReadMemory(addr, 4, err)
    if err.Success() and len(data) == 4:
        return struct.unpack('<f', data)[0]
    return None

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: Could not create target")
        return

    # Set up listener
    listener = lldb.SBListener("wb_trace_listener")

    # Set breakpoint at LinearizeAndColorScale
    linearize_addr = KNOWN_LIBCP_BASE + LINEARIZE_OFFSET
    print(f"Setting bp at LinearizeAndColorScale: 0x{linearize_addr:x}")
    bp_lin = target.BreakpointCreateByAddress(linearize_addr)
    print(f"  valid={bp_lin.IsValid()}, locations={bp_lin.GetNumLocations()}")

    # Launch WITHOUT stop at entry
    error = lldb.SBError()
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    # No stop at entry - just set breakpoints and let it run

    process = target.LaunchSimple([LRI_PATH, OUT_PATH], None,
                                   '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')

    if not process or not process.IsValid():
        print("Launch failed")
        return

    print(f"Process launched: PID {process.GetProcessID()}")

    # Subscribe to events
    process.GetBroadcaster().AddListener(listener, lldb.SBProcess.eBroadcastBitStateChanged)

    # Wait for stop (breakpoint hit) or exit
    print("Waiting for LinearizeAndColorScale breakpoint...")
    deadline = time.time() + 120
    event = lldb.SBEvent()
    hit_lin = False

    while time.time() < deadline:
        state = process.GetState()
        if state == lldb.eStateStopped:
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            print(f"\nStopped at 0x{pc:x}")

            # Check stop reason
            stop_reason = thread.GetStopReason()
            print(f"Stop reason: {stop_reason} (breakpoint={lldb.eStopReasonBreakpoint})")

            if abs(pc - linearize_addr) < 20:
                hit_lin = True
                print("HIT: LinearizeAndColorScale!")
                # Get ctx
                rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
                print(f"  rdi (filter_obj) = 0x{rdi:x}")

                err = lldb.SBError()
                ctx_ptr = process.ReadPointerFromMemory(rdi, err)
                if err.Success():
                    print(f"  ctx = 0x{ctx_ptr:x}")
                    f0 = get_float32(process, ctx_ptr)
                    f4 = get_float32(process, ctx_ptr + 4)
                    f8 = get_float32(process, ctx_ptr + 8)
                    print(f"  ctx[0]={f0:.7f}  (expect ~0.582)")
                    print(f"  ctx[4]={f4:.7f}  (expect ~1.0)")
                    print(f"  ctx[8]={f8:.7f}  (expect ~0.629)")

                    # Set watchpoint on ctx[0]
                    err2 = lldb.SBError()
                    wp = target.WatchAddress(ctx_ptr, 4, False, True, err2)
                    if err2.Success():
                        print(f"  Watchpoint set on ctx[0] @ 0x{ctx_ptr:x}")
                        # Disable linearize bp
                        bp_lin.SetEnabled(False)
                        # Continue
                        process.Continue()
                        print("  Waiting for watchpoint hit...")

                        # Wait for watchpoint
                        wp_deadline = time.time() + 120
                        while time.time() < wp_deadline:
                            state = process.GetState()
                            if state == lldb.eStateStopped:
                                thread2 = process.GetSelectedThread()
                                frame2 = thread2.GetSelectedFrame()
                                pc2 = frame2.GetPC()
                                offset = pc2 - KNOWN_LIBCP_BASE

                                print(f"\n*** WRITE DETECTED at 0x{pc2:x} (libcp+0x{offset:x}) ***")
                                print(f"Function: {frame2.GetFunctionName()}")
                                print(f"\nCall stack:")
                                for i in range(min(15, thread2.GetNumFrames())):
                                    f = thread2.GetFrameAtIndex(i)
                                    fpc = f.GetPC()
                                    foff = fpc - KNOWN_LIBCP_BASE
                                    print(f"  [{i}] 0x{fpc:x} (libcp+0x{foff:x}) {f.GetFunctionName()}")

                                print(f"\nRegisters at write site:")
                                for rn in ['rax','rbx','rcx','rdx','rsi','rdi','r12','r13','r14','r15']:
                                    reg = frame2.FindRegister(rn)
                                    if reg.IsValid():
                                        print(f"  {rn} = 0x{reg.GetValueAsUnsigned():x}")

                                for xn in ['xmm0','xmm1','xmm2','xmm3']:
                                    reg = frame2.FindRegister(xn)
                                    if reg.IsValid():
                                        raw = reg.GetData().GetRawData(lldb.SBError(), 0, 4)
                                        if raw:
                                            fv = struct.unpack('<f', raw[:4])[0]
                                            print(f"  {xn}[0] = {fv:.7f}")

                                new_val = get_float32(process, ctx_ptr)
                                print(f"\n  New ctx[0] = {new_val}")
                                break
                            elif state == lldb.eStateExited:
                                print("Process exited without watchpoint hit")
                                break
                            time.sleep(0.05)
                        break
                    else:
                        print(f"  Watchpoint error: {err2.GetCString()}")
                        process.Continue()
                else:
                    print(f"  Cannot read ctx ptr: {err.GetCString()}")
                    process.Continue()
            else:
                # Unknown stop - check if it's a different breakpoint or signal
                print(f"  Non-linearize stop. Continuing...")
                process.Continue()

        elif state == lldb.eStateExited:
            exit_code = process.GetExitStatus()
            print(f"Process exited: code={exit_code}")
            if not hit_lin:
                print("LinearizeAndColorScale breakpoint was NOT hit!")
            break
        elif state == lldb.eStateCrashed:
            print("Process crashed!")
            break
        elif state == lldb.eStateRunning:
            time.sleep(0.1)
            continue
        else:
            print(f"State: {lldb.SBDebugger.StateAsCString(state)}")
            time.sleep(0.1)

    lldb.SBDebugger.Destroy(debugger)

if __name__ == '__main__':
    run()
