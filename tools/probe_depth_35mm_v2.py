#!/usr/bin/env python3
"""
35mm depth pipeline characterization probe — profile=3, sync mode.

Uses SetAsync(False) + per-thread BP inspection (matches working probe pattern).

Probes:
  1. DepthCache C2 ctor (0x3d8780), StereoAsyncAPI C1 (0x3f46d0), C2 (0x3f2c40)
  2. StereoAsyncAPI cam-list loop entry (0x3f30a0) — cam_id at [rdi+0x60]
  3. Triangulator::refine3dPoints (0x20ca00) — hit count
  4. State machine handlers (0x229d80, 0x229e30, 0x22a040, 0x22a910, 0x22aa50, 0x22add0, 0x22aee0)
  5. Gate (0x3b2fa3)
  6. IRAMP body (0x3661b0) — tile count
  7. SIC init (0x3e0330), IRAMP dispatcher (0x3f6170) — cam_ids

Run: arch -x86_64 /usr/bin/python3 probe_depth_35mm_v2.py
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

LRI_PATH    = '/Volumes/Base Photos/Light/2018-10-25/L16_02951.lri'
OUT_PATH    = '/tmp/depth_chars_35_v2.hdr'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

# libcp-relative VAs
OFFSETS = {
    'DepthCache_C2_ctor':    0x3d8780,
    'StereoAPI_C1':          0x3f46d0,
    'StereoAPI_C2':          0x3f2c40,
    'StereoAPI_camloop_lo':  0x3f30a0,
    'Triangulator_refine3d': 0x20ca00,
    'SM_229d80':             0x229d80,
    'SM_229e30':             0x229e30,
    'SM_22a040':             0x22a040,
    'SM_22a910':             0x22a910,
    'SM_22aa50':             0x22aa50,
    'SM_22add0':             0x22add0,
    'SM_22aee0':             0x22aee0,
    'Gate_3b2fa3':           0x3b2fa3,
    'IRAMP_body':            0x3661b0,
    'SIC_init':              0x3e0330,
    'IRAMP_dispatcher':      0x3f6170,
}

BASELINE_28MM = {
    'DepthCache_C2_ctor':    1,
    'StereoAPI_C1':          1,
    'StereoAPI_C2':          1,
    'StereoAPI_camloop_lo':  '?',
    'Triangulator_refine3d': 10,
    'SM_229d80':  '?', 'SM_229e30': '?', 'SM_22a040': '?',
    'SM_22a910':  '?', 'SM_22aa50': '?', 'SM_22add0': '?',
    'SM_22aee0':  '?',
    'Gate_3b2fa3':           1,
    'IRAMP_body':            300,
    'SIC_init':              5,
    'IRAMP_dispatcher':      7,
}

# Mutable state
_hits = collections.Counter()
_cam_loop_ids   = []   # [rdi+0x60] at StereoAPI cam-list loop entry
_triangulator_ptrs = set()  # distinct rdi values at Triangulator
_dispatcher_cam_ids = []
_sic_cam_ids   = []
_gate_byte0    = None


def read_u32(process, addr):
    if not addr:
        return None
    err = lldb.SBError()
    data = process.ReadMemory(addr, 4, err)
    if err.Success() and len(data) == 4:
        return struct.unpack('<I', data)[0]
    return None

def read_u8(process, addr):
    if not addr:
        return None
    err = lldb.SBError()
    data = process.ReadMemory(addr, 1, err)
    if err.Success() and len(data) == 1:
        return data[0]
    return None

def get_reg(frame, name):
    reg = frame.FindRegister(name)
    if reg.IsValid():
        return reg.GetValueAsUnsigned()
    return 0


def handle_stop(process, bp_id_to_name):
    global _gate_byte0
    for tidx in range(process.GetNumThreads()):
        thread = process.GetThreadAtIndex(tidx)
        if thread.GetStopReason() != lldb.eStopReasonBreakpoint:
            continue
        bp_id = thread.GetStopReasonDataAtIndex(0)
        name = bp_id_to_name.get(bp_id, f'unknown_{bp_id}')
        frame = thread.GetFrameAtIndex(0)
        _hits[name] += 1

        if not frame.IsValid():
            continue

        rdi = get_reg(frame, 'rdi')
        rsi = get_reg(frame, 'rsi')

        if name == 'StereoAPI_camloop_lo':
            cam_id = read_u32(process, rdi + 0x60) if rdi else None
            _cam_loop_ids.append(cam_id)

        elif name == 'Triangulator_refine3d':
            _triangulator_ptrs.add(rdi)

        elif name == 'Gate_3b2fa3':
            if _gate_byte0 is None:
                _gate_byte0 = read_u8(process, rdi) if rdi else None

        elif name == 'SIC_init':
            cam_id = read_u32(process, rdi + 0x60) if rdi else None
            _sic_cam_ids.append(cam_id)

        elif name == 'IRAMP_dispatcher':
            cam_id = read_u32(process, rdi + 0x60) if rdi else None
            _dispatcher_cam_ids.append(cam_id)


def _find_libcp(target):
    for i in range(target.GetNumModules()):
        m = target.GetModuleAtIndex(i)
        fname = m.GetFileSpec().GetFilename()
        if fname and 'libcp' in fname:
            addr = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if addr != lldb.LLDB_INVALID_ADDRESS:
                return addr
    return None


def main():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(False)   # SYNC MODE: Continue() blocks until next stop

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    if not target.IsValid():
        print(f"ERROR: invalid target")
        sys.exit(1)

    # No --profile arg: bridge default is profile=3 per D7 (DESKTOP)
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
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
    time.sleep(0.5)
    print(f"State: {debugger.StateAsCString(process.GetState())}")

    # Find libcp — may need brief continue past dyld
    libcp_base = _find_libcp(target)
    if libcp_base is None:
        print("libcp not at entry; continuing past dyld...")
        debugger.SetAsync(True)
        process.Continue()
        time.sleep(2)
        process.Stop()
        time.sleep(0.3)
        debugger.SetAsync(False)
        libcp_base = _find_libcp(target)

    if libcp_base is None:
        print("ERROR: libcp not found in any module")
        process.Kill()
        sys.exit(1)

    print(f"libcp base: 0x{libcp_base:016x}")

    # Set BPs in sync mode — no callbacks, poll-driven
    bp_id_to_name = {}
    for name, offset in OFFSETS.items():
        addr = libcp_base + offset
        bp = target.BreakpointCreateByAddress(addr)
        if not bp.IsValid():
            print(f"  WARNING: BP {name} invalid @ 0x{addr:x}")
            continue
        bp_id_to_name[bp.GetID()] = name
        print(f"  BP[{bp.GetID()}] {name} @ libcp+0x{offset:x}")

    print(f"\nRunning 35mm profile=3 render (sync mode)...")
    start_time = time.time()

    # First continue from entry stop
    process.Continue()

    MAX_ITERS = 200000
    MAX_TIME  = 600
    iteration = 0
    last_report = time.time()

    while iteration < MAX_ITERS and (time.time() - start_time) < MAX_TIME:
        state = process.GetState()

        if state == lldb.eStateExited:
            elapsed = time.time() - start_time
            print(f"\nProcess exited code={process.GetExitStatus()} elapsed={elapsed:.1f}s")
            break

        if state == lldb.eStateCrashed:
            elapsed = time.time() - start_time
            print(f"\nProcess CRASHED elapsed={elapsed:.1f}s")
            break

        if state == lldb.eStateStopped:
            handle_stop(process, bp_id_to_name)
            if time.time() - last_report > 20:
                elapsed = time.time() - start_time
                sm_sum = sum(_hits.get(f'SM_{x}',0) for x in ['229d80','229e30','22a040','22a910','22aa50','22add0','22aee0'])
                print(f"  [{elapsed:.0f}s] IRAMP={_hits['IRAMP_body']} "
                      f"Tri={_hits['Triangulator_refine3d']} "
                      f"Gate={_hits['Gate_3b2fa3']} "
                      f"StereoC1={_hits['StereoAPI_C1']} "
                      f"SM_sum={sm_sum}")
                last_report = time.time()
            process.Continue()
            iteration += 1

        elif state == lldb.eStateRunning:
            # Sync mode: should not linger here
            time.sleep(0.05)

        else:
            elapsed = time.time() - start_time
            print(f"  [{elapsed:.0f}s] Unexpected state: {debugger.StateAsCString(state)}")
            time.sleep(0.1)

    if iteration >= MAX_ITERS:
        print(f"\nMax iterations ({MAX_ITERS}) reached")
        process.Kill()
    elif (time.time() - start_time) >= MAX_TIME:
        print(f"\nTimeout {MAX_TIME}s; killing")
        process.Kill()

    print_summary()
    try:
        debugger.Destroy()
    except Exception:
        pass


def print_summary():
    print("\n" + "=" * 76)
    print("35mm DEPTH PIPELINE CHARACTERIZATION — profile=3")
    print(f"LRI: {LRI_PATH}")
    print("=" * 76)

    rows = [
        ('--- DEPTH PIPELINE ---', None),
        ('Gate (0x3b2fa3)',                  'Gate_3b2fa3'),
        ('DepthCache C2 ctor (0x3d8780)',    'DepthCache_C2_ctor'),
        ('StereoAsyncAPI C1 (0x3f46d0)',     'StereoAPI_C1'),
        ('StereoAsyncAPI C2 (0x3f2c40)',     'StereoAPI_C2'),
        ('StereoAPI camloop lo (0x3f30a0)',  'StereoAPI_camloop_lo'),
        ('Triangulator refine3dPoints',      'Triangulator_refine3d'),
        ('--- STATE MACHINE ---', None),
        ('SM 0x229d80', 'SM_229d80'), ('SM 0x229e30', 'SM_229e30'),
        ('SM 0x22a040', 'SM_22a040'), ('SM 0x22a910', 'SM_22a910'),
        ('SM 0x22aa50', 'SM_22aa50'), ('SM 0x22add0', 'SM_22add0'),
        ('SM 0x22aee0', 'SM_22aee0'),
        ('--- COLOR PATH (reference) ---', None),
        ('IRAMP body (0x3661b0)',            'IRAMP_body'),
        ('SIC init (0x3e0330)',              'SIC_init'),
        ('IRAMP dispatcher (0x3f6170)',      'IRAMP_dispatcher'),
    ]

    print(f"  {'Probe point':<42} {'35mm hits':>9}  {'28mm base':>9}")
    print("  " + "-" * 65)
    for label, key in rows:
        if key is None:
            print(f"\n  {label}")
            continue
        h35 = _hits[key]
        b28 = BASELINE_28MM.get(key, '?')
        delta = f"  ({h35 - b28:+d})" if isinstance(b28, int) else ''
        print(f"  {label:<42} {h35:>9}  {str(b28):>9}{delta}")

    if _gate_byte0 is not None:
        print(f"\n  Gate [imageStorageObj+0] = 0x{_gate_byte0:02x}  (expect 0x03 for depth to fire)")

    if _cam_loop_ids:
        distinct = sorted(set(x for x in _cam_loop_ids if x is not None))
        print(f"\n  StereoAsyncAPI cam-list: {_cam_loop_ids}  distinct={distinct}")
    else:
        print(f"\n  StereoAsyncAPI cam-list: (no hits)")

    if _triangulator_ptrs:
        print(f"  Triangulator distinct rdi ptrs: {[hex(x) for x in sorted(_triangulator_ptrs)]}")

    if _dispatcher_cam_ids:
        dcams = sorted(set(x for x in _dispatcher_cam_ids if x is not None))
        print(f"  IRAMP dispatcher cam_ids ({_hits['IRAMP_dispatcher']} hits): {dcams}")

    if _sic_cam_ids:
        scams = sorted(set(x for x in _sic_cam_ids if x is not None))
        print(f"  SIC init cam_ids ({_hits['SIC_init']} hits): {scams}")

    sm_active = [k for k in ['SM_229d80','SM_229e30','SM_22a040','SM_22a910',
                              'SM_22aa50','SM_22add0','SM_22aee0'] if _hits[k] > 0]
    print(f"\n  Active state machine handlers: {sm_active}")

    print("\n" + "=" * 76)
    print("END OF REPORT")
    print("=" * 76)


if __name__ == '__main__':
    main()
