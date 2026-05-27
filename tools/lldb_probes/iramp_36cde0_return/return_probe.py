import builtins
import struct


def reset():
    builtins.l16_36cde0_return_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _xmm_low_f32(frame, name):
    error = builtins.__import__("lldb").SBError()
    data = frame.FindRegister(name).GetData()
    if data.IsValid():
        value = data.GetFloat(error, 0)
        if error.Success():
            return value
    return None


def hit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")

    x_data = _read(process, rbp - 0x4310, 4)
    y_data = _read(process, rbp - 0x4320, 4)
    begin_data = _read(process, rbp - 0x1800, 8)
    end_data = _read(process, rbp - 0x17F8, 8)
    rec_off_data = _read(process, rbp - 0x4300, 8)
    r13_data = _read(process, rbp - 0x437C, 4)
    r8_data = _read(process, rbp - 0x4378, 4)

    required = (x_data, y_data, begin_data, end_data, rec_off_data, r13_data, r8_data)
    if None in required:
        builtins.l16_36cde0_return_first = {
            "error": "failed to read stack packet",
            "rip": _u(frame, "rip"),
            "rbp": rbp,
        }
        return

    begin = _u64(begin_data)
    end = _u64(end_data)
    record_offset = _u64(rec_off_data)
    record = begin + record_offset
    r13 = _i32(r13_data)
    r8 = _i32(r8_data)

    stride_data = _read(process, record + 0x58, 4)
    out_base_data = _read(process, record + 0x60, 8)
    if None in (stride_data, out_base_data):
        builtins.l16_36cde0_return_first = {
            "error": "failed to read record output descriptor",
            "rip": _u(frame, "rip"),
            "rbp": rbp,
            "begin": begin,
            "end": end,
            "record_offset": record_offset,
            "record": record,
        }
        return

    stride = _i32(stride_data)
    out_base = _u64(out_base_data)
    out_index = stride * r13 + r8
    out_index_times_3 = out_index * 3
    out_addr_first_float = out_base + out_index_times_3 * 4
    rax = _u(frame, "rax")
    rcx = _u(frame, "rcx")
    diff = end - begin if end >= begin else None

    builtins.l16_36cde0_return_first = {
        "rip": _u(frame, "rip"),
        "rbp": rbp,
        "begin": begin,
        "end": end,
        "diff": diff,
        "npartners": diff // 0x280 if diff is not None else None,
        "record_offset": record_offset,
        "record": record,
        "x_stack_float": _f32(x_data),
        "y_stack_float": _f32(y_data),
        "xmm1_low_float": _xmm_low_f32(frame, "xmm1"),
        "xmm0_low_float": _xmm_low_f32(frame, "xmm0"),
        "descriptor_stride": stride,
        "index_mul": r13,
        "index_add": r8,
        "out_base": out_base,
        "out_index": out_index,
        "out_index_times_3": out_index_times_3,
        "out_addr_first_float": out_addr_first_float,
        "out_base_register": rcx,
        "out_index_times_3_register": rax,
        "out_addr_first_float_register": rcx + rax * 4,
    }


def report(label):
    if not hasattr(builtins, "l16_36cde0_return_first"):
        reset()
    print("L16_36CDE0_RETURN_PROBE_BEGIN", label)
    print("return_packet", builtins.l16_36cde0_return_first)
    print("L16_36CDE0_RETURN_PROBE_END", label)
