#!/usr/bin/env python3
"""
35mm depth fast probe — sync mode, NO auto-continue.

Targets only the depth-critical BPs (not IRAMP, not SIC which cause 200k+ iterations).
Captures:
  1. Gate byte (0x3b2fa3)
  2. StereoAsyncAPI C1/C2 ctor hit counts (0x3f46d0, 0x3f2c40)
  3. DepthCache C2 ctor (0x3d8780)
  4. Cam-list loop (0x3f30a0) — read EDX for cam_id (direct int32 from vector)
  5. Triangulator (0x20ca00) — hit count (kills after 20 hits or on process exit)
  6. State machine handlers (0x229d80..0x22aee0)

Deliberately omits IRAMP (300+ hits) and SIC (expensive) to keep < 2min.

Run: arch -x86_64 /usr/bin/python3 probe_depth_35mm_fast.py
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
OUT_PATH    = '/tmp/depth_chars_35_fast.hdr'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

# Only depth-specific offsets (no IRAMP/SIC which hammer BP counts)
OFFSETS = {
    'Gate_3b2fa3':           0x3b2fa3,
    'DepthCache_C2_ctor':    0x3d8780,
    'StereoAPI_C1':          0x3f46d0,
    'StereoAPI_C2':          0x3f2c40,
    'StereoAPI_camloop_lo':  0x3f30a0,   # cam_id in EDX = [r12] (direct int32)
    'Triangulator_refine3d': 0x20ca00,
    'SM_229d80':             0x229d80,
    'SM_229e30':             0x229e30,
    'SM_22a040':             0x22a040,
    'SM_22a910':             0x22a910,
    'SM_22aa50':             0x22aa50,
    'SM_22add0':             0x22add0,
    'SM_22aee0':             0x22aee0,
}

BASELINE_28MM = {
    'Gate_3b2fa3':           1,
    'DepthCache_C2_ctor':    1,
    'StereoAPI_C1':          1,
    'StereoAPI_C2':          1,
    'StereoAPI_camloop_lo':  '?',
    'Triangulator_refine3d': 10,
    'SM_229d80': '?', 'SM_229e30': '?', 'SM_22a040': '?',
    'SM_22a910': '?', 'SM_22aa50': '?', 'SM_22add0': '?',
    'SM_22aee0': '?',
}

_hits = collections.Counter()
_cam_loop_ids   = []   # EDX at loop entry = direct cam_id int32
_cam_loop_rdx   = []   # raw EDX values
_tri_rdis       = set()
_gate_byte0     = None
_gate_rdi       = None


def read_u8(process, addr):
    if not addr:
        return None
    err = lldb.SBError()
    data = process.ReadMemory(addr, 1, err)
    return data[0] if err.Success() and len(data) == 1 else None

def get_reg(frame, name):
    reg = frame.FindRegister(name)
    return reg.GetValueAsUnsigned() if reg.IsValid() else 0


def handle_stop(process, bp_id_to_name):
    global _gate_byte0, _gate_rdi
    for tidx in range(process.GetNumThreads()):
        thread = process.GetThreadAtIndex(tidx)
        if thread.GetStopReason() != lldb.eStopReasonBreakpoint:
            continue
        bp_id = thread.GetStopReasonDataAtIndex(0)
        name  = bp_id_to_name.get(bp_id, f'unknown_{bp_id}')
        frame = thread.GetFrameAtIndex(0)
        _hits[name] += 1

        if not frame.IsValid():
            continue

        if name == 'Gate_3b2fa3':
            rdi = get_reg(frame, 'rdi')
            _gate_rdi = rdi
            if _gate_byte0 is None:
                _gate_byte0 = read_u8(process, rdi) if rdi else None

        elif name == 'StereoAPI_camloop_lo':
            # At 0x3f30a0: mov edx, [r12] — r12 = iterator into int32 vector
            # By the time we're here, EDX has been set by that mov
            # The cam_id is in RDX (zero-extended from EDX)
            rdx = get_reg(frame, 'rdx')
            # Also check r12 — that's the current loop pointer, *r12 = cam_id
            # But we can't dereference r12 easily here; EDX is already set
            # Actually: 0x3f30a0 IS the mov edx,[r12] instruction itself
            # So EDX has not been set yet at this point — we need the value AFTER
            # Try r12 dereference instead
            r12 = get_reg(frame, 'r12')
            cam_via_rdx  = rdx & 0xffffffff
            # r12 dereference — this is the actual current cam_id
            cam_via_r12  = None
            if r12:
                err = lldb.SBError()
                d = process.ReadMemory(r12, 4, err)
                if err.Success() and len(d) == 4:
                    cam_via_r12 = struct.unpack('<I', d)[0]
            _cam_loop_rdx.append(rdx)
            _cam_loop_ids.append(cam_via_r12 if cam_via_r12 is not None else cam_via_rdx)

        elif name == 'Triangulator_refine3d':
            rdi = get_reg(frame, 'rdi')
            _tri_rdis.add(rdi)


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
    debugger.SetAsync(False)

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    if not target.IsValid():
        print("ERROR: invalid target")
        sys.exit(1)

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
    time.sleep(0.3)
    print(f"State: {debugger.StateAsCString(process.GetState())}")

    libcp_base = _find_libcp(target)
    if libcp_base is None:
        print("libcp not at entry; async continue to load libs...")
        debugger.SetAsync(True)
        process.Continue()
        time.sleep(2)
        process.Stop()
        time.sleep(0.3)
        debugger.SetAsync(False)
        libcp_base = _find_libcp(target)

    if libcp_base is None:
        print("ERROR: libcp not found")
        process.Kill()
        sys.exit(1)

    print(f"libcp base: 0x{libcp_base:016x}")

    bp_id_to_name = {}
    for name, offset in OFFSETS.items():
        addr = libcp_base + offset
        bp = target.BreakpointCreateByAddress(addr)
        if not bp.IsValid():
            print(f"  WARNING: BP {name} invalid @ 0x{addr:x}")
            continue
        bp_id_to_name[bp.GetID()] = name
        print(f"  BP[{bp.GetID()}] {name} @ libcp+0x{offset:x}")

    print("\nRunning 35mm depth-fast probe (sync, no IRAMP BP)...")
    start_time = time.time()

    # From entry stop, continue
    process.Continue()

    MAX_ITERS = 50000   # depth-only BPs are few, so this covers it
    MAX_TIME  = 300     # 5 min max — depth fires before IRAMP completes
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
            if time.time() - last_report > 15:
                elapsed = time.time() - start_time
                sm_sum = sum(_hits.get(f'SM_{x}', 0) for x in
                             ['229d80','229e30','22a040','22a910','22aa50','22add0','22aee0'])
                print(f"  [{elapsed:.0f}s] Gate={_hits['Gate_3b2fa3']} "
                      f"SAC1={_hits['StereoAPI_C1']} "
                      f"SAC2={_hits['StereoAPI_C2']} "
                      f"DC={_hits['DepthCache_C2_ctor']} "
                      f"Tri={_hits['Triangulator_refine3d']} "
                      f"CAMloop={_hits['StereoAPI_camloop_lo']} "
                      f"SM={sm_sum}")
                last_report = time.time()
            process.Continue()
            iteration += 1

        elif state == lldb.eStateRunning:
            time.sleep(0.05)
        else:
            time.sleep(0.05)

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
    print("\n" + "=" * 72)
    print("35mm DEPTH PIPELINE — FAST PROBE — profile=3")
    print(f"LRI: {LRI_PATH}")
    print("=" * 72)

    rows = [
        ('--- DEPTH PIPELINE INDICATORS ---', None),
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
        print(f"\n  Gate [imageStorageObj+0] = 0x{_gate_byte0:02x}  (0x03 = depth fires)")
    else:
        print(f"\n  Gate [imageStorageObj+0]: NOT CAPTURED (fired in async window)")

    if _cam_loop_ids:
        distinct = sorted(set(x for x in _cam_loop_ids if x is not None and 0 <= x <= 20))
        print(f"\n  StereoAsyncAPI cam-list iterations: {_cam_loop_ids}")
        print(f"  Distinct cam_ids (0-20 filter): {distinct}")
    else:
        print(f"\n  StereoAsyncAPI cam-list: (no hits — fired before BPs armed?)")

    if _tri_rdis:
        print(f"\n  Triangulator distinct self* ptrs: {[hex(x) for x in sorted(_tri_rdis)]}")

    sm_active = [k for k in ['SM_229d80','SM_229e30','SM_22a040','SM_22a910',
                              'SM_22aa50','SM_22add0','SM_22aee0'] if _hits[k] > 0]
    print(f"\n  Active state machine handlers: {sm_active}")

    print("\n" + "=" * 72)
    print("END OF REPORT")
    print("=" * 72)


if __name__ == '__main__':
    main()
