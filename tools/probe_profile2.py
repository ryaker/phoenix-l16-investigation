"""
profile=2 (CAMERA) characterization probe at 28mm L16_02130.lri
Counts hits on 7 VAs, captures cam_ids at SIC init + IRAMP dispatcher.
"""

import lldb
import sys
import collections

# libcp slide (consistent across runs)
SLIDE = 0x108c7a000

# Offsets from truth doc + probe brief
IRAMP_BODY        = SLIDE + 0x3661b0   # Halide body — count iterations
SIC_INIT          = SLIDE + 0x3e0330   # SIC init — capture cam_id from [rdx+0x60]
DEPTH_CACHE_CTOR  = SLIDE + 0x3eaf00   # DepthCache C2 ctor
STEREO_C1         = SLIDE + 0x3f46d0   # StereoAsyncAPI C1 ctor
STEREO_C2         = SLIDE + 0x3f2c40   # StereoAsyncAPI C2 ctor
TRIANGULATOR      = SLIDE + 0x20ca00   # Triangulator::refine3dPoints
CCM_INTERP        = SLIDE + 0x350bc0   # CCMInterpBetweenCalib
IRAMP_DISPATCHER  = SLIDE + 0x3f6170   # IRAMP filter dispatcher — cam_id gate

hit_counts = collections.Counter()
sic_cam_ids = []
dispatcher_cam_ids = []

def make_bp_handler(name, capture_cam_id=False, target_list=None):
    def handler(frame, bp_loc, extra_args, internal_dict):
        hit_counts[name] += 1
        if capture_cam_id:
            # cam_id getter at [rdx+0x60] — rdx holds per_cam object ptr at entry
            # For SIC_INIT: rdi = self (SIC*), rsi = config ptr, rdx = per_cam obj
            # For IRAMP_DISPATCHER: rdi = self, rsi = cam_obj ptr
            # cam_id field offset 0x60 in per_cam object
            try:
                thread = frame.GetThread()
                regs = frame.GetRegisters()[0]  # general purpose
                reg_dict = {r.GetName(): r.GetValueAsUnsigned() for r in regs}
                # At SIC init entry: rsi carries per_cam ptr (from initResAmp code path)
                # At dispatcher entry: rsi carries per_cam ptr
                rsi = reg_dict.get('rsi', 0)
                if rsi:
                    proc = frame.GetThread().GetProcess()
                    err = lldb.SBError()
                    cam_id = proc.ReadUnsignedFromMemory(rsi + 0x60, 4, err)
                    if err.Success():
                        if target_list is not None:
                            target_list.append(cam_id)
            except Exception as e:
                pass
        return False  # don't stop
    return handler

def setup_breakpoints(debugger, target):
    bps = {}

    bp = target.BreakpointCreateByAddress(IRAMP_BODY)
    bp.SetCallback(make_bp_handler('IRAMP_body'))
    bp.SetAutoContinue(True)
    bps['IRAMP_body'] = bp

    bp = target.BreakpointCreateByAddress(SIC_INIT)
    bp.SetCallback(make_bp_handler('SIC_init', capture_cam_id=True, target_list=sic_cam_ids))
    bp.SetAutoContinue(True)
    bps['SIC_init'] = bp

    bp = target.BreakpointCreateByAddress(DEPTH_CACHE_CTOR)
    bp.SetCallback(make_bp_handler('DepthCache_ctor'))
    bp.SetAutoContinue(True)
    bps['DepthCache_ctor'] = bp

    bp = target.BreakpointCreateByAddress(STEREO_C1)
    bp.SetCallback(make_bp_handler('StereoAsyncAPI_C1'))
    bp.SetAutoContinue(True)
    bps['StereoAsyncAPI_C1'] = bp

    bp = target.BreakpointCreateByAddress(STEREO_C2)
    bp.SetCallback(make_bp_handler('StereoAsyncAPI_C2'))
    bp.SetAutoContinue(True)
    bps['StereoAsyncAPI_C2'] = bp

    bp = target.BreakpointCreateByAddress(TRIANGULATOR)
    bp.SetCallback(make_bp_handler('Triangulator_refine3d'))
    bp.SetAutoContinue(True)
    bps['Triangulator_refine3d'] = bp

    bp = target.BreakpointCreateByAddress(CCM_INTERP)
    bp.SetCallback(make_bp_handler('CCMInterp'))
    bp.SetAutoContinue(True)
    bps['CCMInterp'] = bp

    bp = target.BreakpointCreateByAddress(IRAMP_DISPATCHER)
    bp.SetCallback(make_bp_handler('IRAMP_dispatcher', capture_cam_id=True, target_list=dispatcher_cam_ids))
    bp.SetAutoContinue(True)
    bps['IRAMP_dispatcher'] = bp

    return bps

def __lldb_init_module(debugger, internal_dict):
    print("[probe_profile2] Module loaded. Run: profile2_run")

def profile2_run(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    if not target:
        print("ERROR: No target selected")
        return

    setup_breakpoints(debugger, target)
    print("[probe_profile2] Breakpoints set. Running process...")

    process = target.GetProcess()
    if process and process.GetState() == lldb.eStateStopped:
        process.Continue()

    # Wait for completion
    import time
    deadline = time.time() + 300  # 5 minute timeout
    while time.time() < deadline:
        state = process.GetState()
        if state in (lldb.eStateExited, lldb.eStateCrashed):
            break
        time.sleep(2)

    print_results()

def print_results():
    print("\n=== PROFILE=2 HIT COUNT RESULTS ===")
    print(f"IRAMP_body (libcp+0x3661b0):        {hit_counts.get('IRAMP_body', 0)}")
    print(f"SIC_init (libcp+0x3e0330):           {hit_counts.get('SIC_init', 0)}")
    print(f"DepthCache_ctor (libcp+0x3eaf00):   {hit_counts.get('DepthCache_ctor', 0)}")
    print(f"StereoAsyncAPI_C1 (libcp+0x3f46d0): {hit_counts.get('StereoAsyncAPI_C1', 0)}")
    print(f"StereoAsyncAPI_C2 (libcp+0x3f2c40): {hit_counts.get('StereoAsyncAPI_C2', 0)}")
    print(f"Triangulator_refine3d (0x20ca00):   {hit_counts.get('Triangulator_refine3d', 0)}")
    print(f"CCMInterp (libcp+0x350bc0):         {hit_counts.get('CCMInterp', 0)}")
    print(f"IRAMP_dispatcher (libcp+0x3f6170):  {hit_counts.get('IRAMP_dispatcher', 0)}")
    print(f"\nSIC cam_ids (order of init):  {sic_cam_ids}")
    print(f"Dispatcher cam_ids (all hits): {dispatcher_cam_ids}")
    print(f"Unique SIC cam_ids: {sorted(set(sic_cam_ids))}")
    print(f"Unique dispatcher cam_ids: {sorted(set(dispatcher_cam_ids))}")
