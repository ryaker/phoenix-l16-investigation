#!/usr/bin/env python3
"""Quick check: get libcp base and verify bp location"""
import lldb
import time

LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH = '/tmp/test_check_base.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR")
        return

    # Launch simple
    process = target.LaunchSimple([LRI_PATH, OUT_PATH], None,
                                   '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')

    if not process:
        print("Launch failed")
        return

    print(f"PID: {process.GetProcessID()}")

    # Wait for it to start running
    time.sleep(2)

    # Check module list
    print("\nModules:")
    for module in target.module_iter():
        name = str(module.GetFileSpec().GetFilename())
        if 'libcp' in name or 'lri' in name.lower():
            hdr = module.GetObjectFileHeaderAddress()
            base = hdr.GetLoadAddress(target)
            print(f"  {name}: base=0x{base:x}")
            if 'libcp' in name:
                # Set and check breakpoint
                for offset, label in [(0x352ce0, 'linearize'), (0x3510f0, 'awb_kernel'), (0x33d6a0, 'bayer_lut')]:
                    addr = base + offset
                    bp = target.BreakpointCreateByAddress(addr)
                    print(f"  BP at libcp+0x{offset:x} = 0x{addr:x}: valid={bp.IsValid()}, locs={bp.GetNumLocations()}")
                    target.BreakpointDelete(bp.GetID())

    # Wait for exit
    deadline = time.time() + 120
    while time.time() < deadline:
        state = process.GetState()
        if state == lldb.eStateExited:
            print(f"\nProcess exited: {process.GetExitStatus()}")
            break
        time.sleep(1)

    lldb.SBDebugger.Destroy(debugger)

if __name__ == '__main__':
    run()
