#!/usr/bin/env python3
import lldb
import sys
import time

sys.stdout.flush()

LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH = '/tmp/test_quick.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

debugger = lldb.SBDebugger.Create()
debugger.SetAsync(True)

target = debugger.CreateTarget(LRI_PROCESS)
print(f"target valid: {target.IsValid()}", flush=True)

process = target.LaunchSimple([LRI_PATH, OUT_PATH], None,
                               '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')

print(f"process: {process}", flush=True)
print(f"PID: {process.GetProcessID()}", flush=True)

# Wait a bit for modules to load
time.sleep(3)

print("Modules:", flush=True)
for module in target.module_iter():
    name = str(module.GetFileSpec().GetFilename())
    if 'libcp' in name and 'libcpan' not in name:
        hdr = module.GetObjectFileHeaderAddress()
        base = hdr.GetLoadAddress(target)
        print(f"  {name}: 0x{base:x}", flush=True)

print("Waiting for exit...", flush=True)
for i in range(120):
    state = process.GetState()
    if state in [lldb.eStateExited, lldb.eStateCrashed]:
        print(f"State: {lldb.SBDebugger.StateAsCString(state)}", flush=True)
        break
    time.sleep(1)

lldb.SBDebugger.Destroy(debugger)
print("Done", flush=True)
