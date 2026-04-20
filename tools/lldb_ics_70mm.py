"""
ICS kernel probe at libcp+0xbf4a0 (ImageConvertColorSpace::$_0)
Target: L16_03434.lri (70mm canonical)

On entry to the lambda body:
  rdi = closure ptr
  [rdi+0x20] = CCM matrix pointer (3x3 floats = 9 * 4 = 36 bytes)

Capture:
  - Total hit count
  - Per distinct matrix-ptr: hit count + 3x3 float values
"""

import lldb
import struct

# Tracking state
hit_count = [0]
matrix_hits = {}    # ptr_int -> hit_count
matrix_data = {}    # ptr_int -> list of 9 floats (read once per ptr)
error_count = [0]


def ics_callback(frame, bp_loc, extra_args, internal_dict):
    """BP callback at libcp+0xbf4a0 entry."""
    hit_count[0] += 1

    process = frame.GetThread().GetProcess()

    # Read rdi = closure ptr
    rdi_val = frame.FindRegister('rdi')
    if not rdi_val.IsValid():
        error_count[0] += 1
        return False

    closure_ptr = rdi_val.GetValueAsUnsigned()
    if closure_ptr == 0:
        error_count[0] += 1
        return False

    # Read [rdi+0x20] = CCM matrix ptr (8 bytes, pointer)
    error_ref = lldb.SBError()
    mat_ptr_bytes = process.ReadMemory(closure_ptr + 0x20, 8, error_ref)
    if not error_ref.Success() or len(mat_ptr_bytes) < 8:
        error_count[0] += 1
        return False

    mat_ptr = struct.unpack('<Q', mat_ptr_bytes)[0]

    # Track hits per matrix ptr
    matrix_hits[mat_ptr] = matrix_hits.get(mat_ptr, 0) + 1

    # Read 3x3 floats once per new ptr
    if mat_ptr not in matrix_data and mat_ptr != 0:
        float_bytes = process.ReadMemory(mat_ptr, 36, error_ref)
        if error_ref.Success() and len(float_bytes) == 36:
            floats = struct.unpack('<9f', float_bytes)
            matrix_data[mat_ptr] = list(floats)
        else:
            matrix_data[mat_ptr] = None

    # Print progress every 50 hits
    if hit_count[0] % 50 == 0:
        print(f"[ICS probe] hit #{hit_count[0]:4d}  mat_ptr=0x{mat_ptr:016x}  distinct={len(matrix_hits)}")

    return False


def print_summary():
    print("\n" + "="*60)
    print(f"ICS::$_0 @libcp+0xbf4a0 — 70mm L16_03434 SUMMARY")
    print(f"  Total hits : {hit_count[0]}")
    print(f"  Errors     : {error_count[0]}")
    print(f"  Distinct CCM ptrs: {len(matrix_hits)}")
    print()

    for i, (ptr, count) in enumerate(sorted(matrix_hits.items(), key=lambda x: -x[1])):
        print(f"  Matrix {i+1}: ptr=0x{ptr:016x}  hits={count}")
        floats = matrix_data.get(ptr)
        if floats is not None:
            print(f"    Row 0: [{floats[0]:+.6f}, {floats[1]:+.6f}, {floats[2]:+.6f}]")
            print(f"    Row 1: [{floats[3]:+.6f}, {floats[4]:+.6f}, {floats[5]:+.6f}]")
            print(f"    Row 2: [{floats[6]:+.6f}, {floats[7]:+.6f}, {floats[8]:+.6f}]")
        else:
            print(f"    (matrix read failed or ptr=0)")
        print()

    print("="*60)
