#!/usr/bin/env python3
"""
Catch Renderer::render and its inner render to verify call path.
Also try to catch the ISP config allocation function at 0x3184d0.
"""
import lldb
import time
import struct

LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH = '/tmp/probe_render_path.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

# Known offsets from static analysis
TARGETS = {
    'Renderer::render': 0x390180,
    'inner_render_3b8ba0': 0x3b8ba0,
    'PropertyAccessor::transform': 0x39d9b0,
    'ISP_alloc_3184d0': 0x3184d0,
    'LinearizeAndColorScale': 0x352ce0,
    'AWB_kernel': 0x3510f0,
    # Try the direct render impl called from transform
    'render_impl_3c70d0': 0x3c70d0,
    # The giant transform body
    'transform_body_3c3430': 0x3c3430,
    # Deserialize
    'deserialize_39cde0': 0x39cde0,
}

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: target invalid")
        return

    # Launch without stop-at-entry, just run
    process = target.LaunchSimple([LRI_PATH, OUT_PATH], None,
                                   '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    if not process or not process.IsValid():
        print("Launch failed")
        return

    print(f"PID: {process.GetProcessID()}")
    time.sleep(2)  # Wait for modules to load

    # Get libcp base
    libcp_base = None
    print("Modules:")
    for m in target.module_iter():
        name = str(m.GetFileSpec().GetFilename())
        base = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
        if 'libcp' in name and 'libcpan' not in name:
            libcp_base = base
            print(f"  *** {name}: 0x{base:x} ***")
        elif 'lri' in name.lower():
            print(f"  {name}: 0x{base:x}")

    if libcp_base is None:
        print("ERROR: libcp not found")
        process.Kill()
        return

    print(f"\nSetting breakpoints (libcp base = 0x{libcp_base:x}):")
    bps = {}
    for name, offset in TARGETS.items():
        addr = libcp_base + offset
        # Verify bytes
        err = lldb.SBError()
        b = process.ReadMemory(addr, 2, err)
        byte_str = bytes(b).hex() if err.Success() else "??"
        bp = target.BreakpointCreateByAddress(addr)
        bps[bp.GetID()] = (name, offset, addr)
        print(f"  [{bp.GetID()}] {name}: 0x{addr:x} bytes={byte_str} valid={bp.IsValid()} locs={bp.GetNumLocations()}")

    print("\nContinuing, waiting for hits...")
    deadline = time.time() + 120
    hit_log = []

    while time.time() < deadline:
        st = process.GetState()
        if st == lldb.eStateStopped:
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            reason = thread.GetStopReason()

            if reason == lldb.eStopReasonBreakpoint:
                bp_id = thread.GetStopReasonDataAtIndex(0)
                info = bps.get(bp_id, ('unknown', 0, 0))
                name, offset, addr = info
                entry = f"HIT: {name} (libcp+0x{offset:x}) at 0x{pc:x}"
                print(f"\n*** {entry} ***")
                hit_log.append(entry)

                # Disable this bp to avoid repeated hits slowing us down
                # But keep enabled so we can count them
                if len(hit_log) >= 10:
                    print(f"10 hits recorded, breaking")
                    break

                process.Continue()

            elif reason == lldb.eStopReasonSignal:
                process.Continue()
            else:
                if pc != 0xffffffffffffffff:
                    print(f"Stop reason={reason} at 0x{pc:x}")
                process.Continue()

        elif st == lldb.eStateExited:
            print(f"\nProcess exited. Total hits: {len(hit_log)}")
            for h in hit_log:
                print(f"  {h}")
            break
        elif st == lldb.eStateCrashed:
            print("CRASHED")
            break
        else:
            time.sleep(0.1)

    if len(hit_log) == 0:
        print("\nNO BREAKPOINTS HIT!")
        print("This means lri_process doesn't use the expected libcp code paths")
        print("\nChecking if process even loaded correctly...")
        # Check exit code
        if process.GetState() == lldb.eStateExited:
            print(f"Exit code: {process.GetExitStatus()}")

    process.Kill()
    lldb.SBDebugger.Destroy(debugger)
    print("Done.")

if __name__ == '__main__':
    run()
