#!/usr/bin/env python3
"""
Wait for libcp to actually load (poll module list), then set breakpoints.
Use __TEXT section load address for reliable base.

This avoids the _main-too-early problem and the wrong-LRI problem.
"""
import lldb
import time
import struct

LRI_PATH = '/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri'
OUT_PATH = '/tmp/probe_waitlibcp.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

LINEARIZE_OFFSET = 0x352ce0
AWB_OFFSET = 0x3510f0
LAMBDA_OFFSET = 0x342730
CALLER_OFFSET = 0x350ff0
WB_PROC_OFFSET = 0x2d2f10  # WB processing function that uses gains

def find_libcp(target):
    for m in target.module_iter():
        fname = str(m.GetFileSpec().GetFilename())
        if 'libcp' in fname and 'libcpan' not in fname:
            return m
    return None

def get_module_base(target, m):
    """Get load address via __TEXT section (most reliable)."""
    sec = m.FindSection("__TEXT")
    if sec.IsValid():
        addr = sec.GetLoadAddress(target)
        if addr != lldb.LLDB_INVALID_ADDRESS and addr != 0:
            return addr
    # Fallback: header address
    hdr = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return hdr

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: target invalid")
        return

    # Launch without stop-at-entry — just run
    process = target.LaunchSimple([LRI_PATH, OUT_PATH], None,
                                  '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    if not process or not process.IsValid():
        print("Launch failed")
        return

    pid = process.GetProcessID()
    print(f"PID: {pid}")

    # Poll for libcp to appear in module list (max 15 seconds)
    print("Waiting for libcp to load...")
    libcp_module = None
    deadline = time.time() + 15
    while time.time() < deadline:
        libcp_module = find_libcp(target)
        if libcp_module is not None:
            break
        # Check if process already exited
        st = process.GetState()
        if st in (lldb.eStateExited, lldb.eStateCrashed):
            print(f"Process already done (state={st}) before libcp loaded!")
            break
        time.sleep(0.2)

    if libcp_module is None:
        print("ERROR: libcp never appeared in module list")
        # List all modules for diagnosis
        print("Modules present:")
        for m in target.module_iter():
            fname = str(m.GetFileSpec().GetFilename())
            base = get_module_base(target, m)
            print(f"  {fname}: 0x{base:x}")
        process.Kill()
        return

    libcp_base = get_module_base(target, libcp_module)
    libcp_fname = str(libcp_module.GetFileSpec().GetFilename())
    print(f"\nlibcp found: {libcp_fname}")
    print(f"  __TEXT base: 0x{libcp_base:x}")

    # Verify bytes at LinearizeAndColorScale
    lin_addr = libcp_base + LINEARIZE_OFFSET
    err = lldb.SBError()
    mem = process.ReadMemory(lin_addr, 8, err)
    if err.Success():
        b = bytes(mem)
        ok = b[:4] == bytes([0x55, 0x48, 0x89, 0xe5])
        print(f"  LinearizeAndColorScale bytes: {b.hex()} {'OK' if ok else 'WRONG!'}")
    else:
        print(f"  Cannot read at lin_addr=0x{lin_addr:x}: {err.GetCString()}")
        # Try stopping the process and re-reading
        process.Stop()
        time.sleep(0.5)
        mem = process.ReadMemory(lin_addr, 8, err)
        if err.Success():
            b = bytes(mem)
            ok = b[:4] == bytes([0x55, 0x48, 0x89, 0xe5])
            print(f"  (after stop) LinearizeAndColorScale bytes: {b.hex()} {'OK' if ok else 'WRONG!'}")
        else:
            print(f"  Still cannot read: {err.GetCString()}")

    # Set breakpoints
    addrs = {
        'LinearizeAndColorScale': libcp_base + LINEARIZE_OFFSET,
        'AWB_kernel': libcp_base + AWB_OFFSET,
        'lambda_342730': libcp_base + LAMBDA_OFFSET,
        'caller_350ff0': libcp_base + CALLER_OFFSET,
        'WBprocess_2d2f10': libcp_base + WB_PROC_OFFSET,
    }

    print(f"\nSetting breakpoints:")
    bps = {}
    for name, addr in addrs.items():
        # Verify bytes first
        mem2 = process.ReadMemory(addr, 2, err)
        byte_str = bytes(mem2).hex() if err.Success() else "??"
        bp = target.BreakpointCreateByAddress(addr)
        bps[bp.GetID()] = (name, addr - libcp_base)
        print(f"  [{bp.GetID()}] {name}: 0x{addr:x} bytes={byte_str} locs={bp.GetNumLocations()}")

    # Ensure process is running
    st = process.GetState()
    if st == lldb.eStateStopped:
        print("\nProcess was stopped, continuing...")
        process.Continue()
    elif st == lldb.eStateRunning:
        print("\nProcess is running, waiting for hits...")
    elif st == lldb.eStateExited:
        print("\nERROR: Process already exited before breakpoints could fire!")
        return
    else:
        print(f"\nUnexpected state: {st}, continuing...")
        process.Continue()

    deadline = time.time() + 200  # L16_03434 takes ~2 min
    hit_log = []
    last_status = time.time()

    while time.time() < deadline:
        st = process.GetState()

        # Print progress every 30 seconds
        if time.time() - last_status > 30:
            print(f"  Still waiting... state={st}, elapsed={time.time()-deadline+200:.0f}s")
            last_status = time.time()

        if st == lldb.eStateStopped:
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            reason = thread.GetStopReason()

            if reason == lldb.eStopReasonBreakpoint:
                bp_id = thread.GetStopReasonDataAtIndex(0)
                bp_name, bp_offset = bps.get(bp_id, ('unknown', 0))
                fname = frame.GetFunctionName() or "??"
                rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
                rsi = frame.FindRegister("rsi").GetValueAsUnsigned()
                rdx = frame.FindRegister("rdx").GetValueAsUnsigned()
                rcx = frame.FindRegister("rcx").GetValueAsUnsigned()

                entry = (f"HIT: {bp_name} libcp+0x{bp_offset:x} PC=0x{pc:x} "
                         f"func={fname} rdi=0x{rdi:x} rsi=0x{rsi:x} rdx=0x{rdx:x} rcx=0x{rcx:x}")
                print(f"\n*** {entry} ***")
                hit_log.append(entry)

                # Print call stack
                for i in range(min(8, thread.GetNumFrames())):
                    f = thread.GetFrameAtIndex(i)
                    foff = f.GetPC() - libcp_base
                    print(f"  [{i}] libcp+0x{foff:x} {f.GetFunctionName()}")

                if len(hit_log) >= 10:
                    print("10 hits, stopping")
                    break
                process.Continue()

            elif reason == lldb.eStopReasonSignal:
                sig = thread.GetStopReasonDataAtIndex(0)
                print(f"  Signal {sig} - continuing")
                process.Continue()
            else:
                if pc != 0xffffffffffffffff:
                    print(f"  Stop reason={reason} at 0x{pc:x}")
                process.Continue()

        elif st == lldb.eStateExited:
            code = process.GetExitStatus()
            print(f"\nProcess exited (code={code}). Total hits: {len(hit_log)}")
            break
        elif st == lldb.eStateCrashed:
            print("\nCRASHED")
            break
        else:
            time.sleep(0.1)

    print("\n=== FINAL SUMMARY ===")
    print(f"libcp base: 0x{libcp_base:x}")
    if hit_log:
        for h in hit_log:
            print(f"  {h}")
    else:
        print("  NO BREAKPOINT HITS")
        print("\nDiagnosis: if process exited with code 0 but zero hits,")
        print("either the base address is wrong, or these code paths are not used.")

    process.Kill()
    lldb.SBDebugger.Destroy(debugger)
    print("Done.")

if __name__ == '__main__':
    run()
