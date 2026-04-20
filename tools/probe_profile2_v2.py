#!/usr/bin/env python3
"""
profile=2 (CAMERA) characterization probe at 28mm L16_02130.lri
v2: poll-loop based counting — no callback registration needed.
     At each eStateStopped, check which BP fired, read registers, continue.

Run: arch -x86_64 /usr/bin/python3 probe_profile2_v2.py
"""

import sys
import os
import struct
import time
import collections

LLDB_PYTHON = '/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python'
if LLDB_PYTHON not in sys.path:
    sys.path.insert(0, LLDB_PYTHON)

import lldb

LRI_PATH      = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH      = '/tmp/p2_28mm_v2.hdr'
LRI_PROCESS   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR     = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

# libcp-relative offsets
OFFSETS = {
    'IRAMP_body':            0x3661b0,
    'SIC_init':              0x3e0330,
    'DepthCache_ctor':       0x3eaf00,
    'StereoAsyncAPI_C1':     0x3f46d0,
    'StereoAsyncAPI_C2':     0x3f2c40,
    'Triangulator_refine3d': 0x20ca00,
    'CCMInterp':             0x350bc0,
    'IRAMP_dispatcher':      0x3f6170,
}

P3_BASELINE = {
    'IRAMP_body':            300,
    'SIC_init':              5,
    'DepthCache_ctor':       0,   # 0 on bridge per §6
    'StereoAsyncAPI_C1':     0,
    'StereoAsyncAPI_C2':     0,
    'Triangulator_refine3d': 0,
    'CCMInterp':             12,
    'IRAMP_dispatcher':      '?',
}

_hits = collections.Counter()
_sic_cam_rdi = []
_sic_cam_rsi = []
_disp_rsi_raw = []
_disp_rdi_mem = []
_ccm_regs = []


def read_u32(process, addr):
    if not addr:
        return None
    err = lldb.SBError()
    data = process.ReadMemory(addr, 4, err)
    if err.Success() and len(data) == 4:
        return struct.unpack('<I', data)[0]
    return None


def get_regs(frame):
    """Return dict of general-purpose register values."""
    r = {}
    gp = frame.GetRegisters().GetFirstValueByName('General Purpose Registers')
    if not gp.IsValid():
        # Try index 0
        gp = frame.GetRegisters()[0]
    for i in range(gp.GetNumChildren()):
        child = gp.GetChildAtIndex(i)
        r[child.GetName()] = child.GetValueAsUnsigned()
    return r


def handle_stop(process, bp_id_to_name):
    """
    Called when process stops. Inspects all stopped threads, identifies
    which BP fired (if any), reads registers, increments counters.
    """
    for thread_idx in range(process.GetNumThreads()):
        thread = process.GetThreadAtIndex(thread_idx)
        stop_reason = thread.GetStopReason()

        if stop_reason != lldb.eStopReasonBreakpoint:
            continue

        # GetStopReasonDataAtIndex(0) = bp_id, (1) = location_id
        bp_id = thread.GetStopReasonDataAtIndex(0)
        name = bp_id_to_name.get(bp_id, f'unknown_bp_{bp_id}')

        frame = thread.GetFrameAtIndex(0)
        if not frame.IsValid():
            _hits[name] += 1
            continue

        regs = get_regs(frame)
        rdi = regs.get('rdi', 0)
        rsi = regs.get('rsi', 0)

        _hits[name] += 1

        if name == 'SIC_init':
            _sic_cam_rdi.append(read_u32(process, rdi + 0x60) if rdi else None)
            _sic_cam_rsi.append(read_u32(process, rsi + 0x60) if rsi else None)

        elif name == 'IRAMP_dispatcher':
            _disp_rsi_raw.append(rsi)
            _disp_rdi_mem.append(read_u32(process, rdi + 0x60) if rdi else None)

        elif name == 'CCMInterp':
            _ccm_regs.append((rdi, rsi))


def main():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(False)  # sync mode: process.Continue() blocks until stop

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    if not target.IsValid():
        print(f"ERROR: target invalid")
        sys.exit(1)

    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH, '--profile', '2'])
    env = lldb.SBEnvironment()
    env.Set('DYLD_LIBRARY_PATH', LIBCP_DIR, True)
    launch_info.SetEnvironment(env, True)
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    err = lldb.SBError()
    process = target.Launch(launch_info, err)
    if not err.Success() or not process.IsValid():
        print(f"ERROR launching: {err}")
        sys.exit(1)

    print(f"Launched PID={process.GetProcessID()}")

    # In sync mode, launch with stop-at-entry should already be stopped
    # Wait a moment
    time.sleep(1)
    print(f"State after launch: {debugger.StateAsCString(process.GetState())}")

    # Find libcp
    libcp_base = _find_libcp(target)
    if libcp_base is None:
        # dyld not done yet — continue past entry to get past dyld, then stop again
        print("libcp not found at entry. Running past dyld init...")
        # Set a BP at main() to catch after all libs load
        # Actually: just continue briefly, the process will keep running
        # Switch to async, continue, sleep, stop, switch back
        debugger.SetAsync(True)
        process.Continue()
        time.sleep(2)
        process.Stop()
        time.sleep(0.5)
        debugger.SetAsync(False)
        libcp_base = _find_libcp(target)

    if libcp_base is None:
        print("ERROR: libcp not found")
        process.Kill()
        sys.exit(1)

    print(f"libcp base: 0x{libcp_base:016x}")

    # Set BPs
    bp_id_to_name = {}
    for name, offset in OFFSETS.items():
        addr = libcp_base + offset
        bp = target.BreakpointCreateByAddress(addr)
        if not bp.IsValid():
            print(f"  WARNING: BP {name} invalid at 0x{addr:x}")
            continue
        bp_id_to_name[bp.GetID()] = name
        print(f"  BP[{bp.GetID()}] {name} @ 0x{addr:x}")

    print(f"\nRunning profile=2 (sync mode, BP-driven poll)...")
    start_time = time.time()

    # In sync mode, Continue() blocks until next stop.
    # We loop: handle stop -> continue -> handle stop -> ...
    # Until process exits.
    MAX_ITERATIONS = 100000
    MAX_TIME = 600

    # First continue from entry stop
    process.Continue()

    iteration = 0
    last_report = time.time()

    while iteration < MAX_ITERATIONS and (time.time() - start_time) < MAX_TIME:
        state = process.GetState()

        if state == lldb.eStateExited:
            elapsed = time.time() - start_time
            print(f"\nProcess exited. Code={process.GetExitStatus()}, elapsed={elapsed:.1f}s")
            break
        if state == lldb.eStateCrashed:
            elapsed = time.time() - start_time
            print(f"\nProcess CRASHED after {elapsed:.1f}s")
            break
        if state == lldb.eStateStopped:
            handle_stop(process, bp_id_to_name)
            # Progress report
            if time.time() - last_report > 20:
                elapsed = time.time() - start_time
                print(f"  [{elapsed:.0f}s] IRAMP={_hits['IRAMP_body']} SIC={_hits['SIC_init']} CCM={_hits['CCMInterp']} DISP={_hits['IRAMP_dispatcher']}")
                last_report = time.time()
            process.Continue()
            iteration += 1
        elif state == lldb.eStateRunning:
            # Still running — in async mode this would be normal
            # In sync mode shouldn't happen after Continue()
            time.sleep(0.1)
        else:
            print(f"  Unexpected state: {debugger.StateAsCString(state)}")
            time.sleep(0.1)

    if iteration >= MAX_ITERATIONS:
        print(f"\nMax iterations ({MAX_ITERATIONS}) reached")
        process.Kill()
    elif (time.time() - start_time) >= MAX_TIME:
        print(f"\nTimeout after {MAX_TIME}s")
        process.Kill()

    print_summary()


def _find_libcp(target):
    for i in range(target.GetNumModules()):
        m = target.GetModuleAtIndex(i)
        fname = m.GetFileSpec().GetFilename()
        if fname and 'libcp' in fname:
            addr = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if addr != lldb.LLDB_INVALID_ADDRESS:
                return addr
    return None


def print_summary():
    print("\n" + "="*72)
    print("PROFILE=2 (CAMERA) vs PROFILE=3 (DESKTOP) @ 28mm L16_02130")
    print("="*72)
    print(f"{'Probe point':<35} {'p=2 hits':>10}  {'p=3 baseline':>14}  {'delta':>8}")
    print("-"*72)
    rows = [
        ('IRAMP_body (0x3661b0)',            'IRAMP_body'),
        ('SIC_init (0x3e0330)',              'SIC_init'),
        ('DepthCache_ctor (0x3eaf00)',       'DepthCache_ctor'),
        ('StereoAsyncAPI_C1 (0x3f46d0)',     'StereoAsyncAPI_C1'),
        ('StereoAsyncAPI_C2 (0x3f2c40)',     'StereoAsyncAPI_C2'),
        ('Triangulator_refine3d (0x20ca00)', 'Triangulator_refine3d'),
        ('CCMInterp (0x350bc0)',             'CCMInterp'),
        ('IRAMP_dispatcher (0x3f6170)',      'IRAMP_dispatcher'),
    ]
    for label, key in rows:
        p2 = _hits[key]
        p3 = P3_BASELINE.get(key, '?')
        delta = f"{p2-p3:+d}" if isinstance(p3, int) else '?'
        print(f"  {label:<33} {p2:>10}  {str(p3):>14}  {delta:>8}")

    print()
    valid_rdi = [x for x in _sic_cam_rdi if x is not None and 0 <= x <= 15]
    valid_rsi = [x for x in _sic_cam_rsi if x is not None and 0 <= x <= 15]
    print(f"SIC_init [rdi+0x60] raw: {_sic_cam_rdi[:20]}")
    print(f"SIC_init [rsi+0x60] raw: {_sic_cam_rsi[:20]}")
    print(f"  unique valid [rdi+0x60]: {sorted(set(valid_rdi))}")
    print(f"  unique valid [rsi+0x60]: {sorted(set(valid_rsi))}")
    print()

    valid_disp = [x for x in _disp_rsi_raw if 0 <= x <= 15]
    valid_disp_m = [x for x in _disp_rdi_mem if x is not None and 0 <= x <= 15]
    print(f"IRAMP_dispatcher rsi (cam_id?): {_disp_rsi_raw[:30]}")
    print(f"IRAMP_dispatcher [rdi+0x60]:    {_disp_rdi_mem[:30]}")
    print(f"  unique rsi in [0,15]: {sorted(set(valid_disp))}")
    print(f"  unique mem [rdi+0x60] in [0,15]: {sorted(set(valid_disp_m))}")
    print()

    print(f"CCMInterp total calls: {len(_ccm_regs)}")
    if _ccm_regs:
        unique_rdi = sorted(set(r for r, _ in _ccm_regs))
        unique_rsi = sorted(set(r for _, r in _ccm_regs))
        print(f"  Unique rdi (dest buf ptrs): {len(unique_rdi)}")
        print(f"  Unique rsi:                 {len(unique_rsi)}")

    print()
    if os.path.exists(OUT_PATH):
        sz = os.path.getsize(OUT_PATH)
        print(f"Output: {OUT_PATH} ({sz:,} bytes = {sz/1e6:.1f} MB)")
    else:
        print(f"Output NOT found: {OUT_PATH}")
    print("="*72)


if __name__ == '__main__':
    main()
