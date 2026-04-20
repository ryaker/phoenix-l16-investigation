"""
ICS probe module for LLDB at 70mm.
Import via: command script import ics_probe_70mm_module.py
Then use: breakpoint command add --python-function ics_probe_70mm_module.ics_callback <bp_id>

Summary via: script ics_probe_70mm_module.print_summary()
"""

import struct
import sys

hit_count  = [0]
matrix_hits = {}   # mat_ptr_int -> count
matrix_data = {}   # mat_ptr_int -> list[float] or None
error_count = [0]


def ics_callback(frame, bp_loc, extra_args, internal_dict):
    """
    BP callback for ImageConvertColorSpace::$_0 at libcp+0xbf4a0.
    rdi = closure ptr; [rdi+0x20] = CCM matrix ptr; matrix = 9 * float32
    Return True = stop; False = continue
    """
    import struct as _struct
    import sys as _sys

    hit_count[0] += 1
    process = frame.GetThread().GetProcess()

    rdi_reg = frame.FindRegister('rdi')
    if not rdi_reg.IsValid():
        error_count[0] += 1
        return False

    closure_ptr = rdi_reg.GetValueAsUnsigned()
    if closure_ptr == 0:
        error_count[0] += 1
        return False

    import lldb
    err = lldb.SBError()
    mat_ptr_bytes = process.ReadMemory(closure_ptr + 0x20, 8, err)
    if not err.Success() or len(mat_ptr_bytes) < 8:
        error_count[0] += 1
        return False

    mat_ptr = _struct.unpack('<Q', mat_ptr_bytes)[0]
    matrix_hits[mat_ptr] = matrix_hits.get(mat_ptr, 0) + 1

    if mat_ptr not in matrix_data and mat_ptr != 0:
        float_bytes = process.ReadMemory(mat_ptr, 36, err)
        if err.Success() and len(float_bytes) == 36:
            matrix_data[mat_ptr] = list(_struct.unpack('<9f', float_bytes))
        else:
            matrix_data[mat_ptr] = None

    if hit_count[0] % 50 == 0:
        _sys.stdout.write(f"[ICS 70mm] hit={hit_count[0]:4d}  mat_ptr=0x{mat_ptr:016x}  distinct={len(matrix_hits)}\n")
        _sys.stdout.flush()

    return False  # continue — do NOT stop


def print_summary():
    print()
    print("=" * 60)
    print(f"VERDICT: ICS::$_0 @libcp+0xbf4a0  70mm L16_03434")
    print(f"  Total hits       : {hit_count[0]}")
    print(f"  Distinct matrices: {len(matrix_hits)}")
    print(f"  Errors           : {error_count[0]}")
    print()

    for rank, (ptr, count) in enumerate(sorted(matrix_hits.items(), key=lambda x: -x[1])):
        print(f"  Matrix {rank+1}: ptr=0x{ptr:016x}  hits={count}")
        floats = matrix_data.get(ptr)
        if floats is not None:
            print(f"    Row 0: [{floats[0]:+.6f}, {floats[1]:+.6f}, {floats[2]:+.6f}]")
            print(f"    Row 1: [{floats[3]:+.6f}, {floats[4]:+.6f}, {floats[5]:+.6f}]")
            print(f"    Row 2: [{floats[6]:+.6f}, {floats[7]:+.6f}, {floats[8]:+.6f}]")
        else:
            print(f"    (matrix read failed)")
        print()
    print("=" * 60)
