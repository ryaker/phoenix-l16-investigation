import builtins
import struct


def reset():
    builtins.l16_tuple_consumer_first = None


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


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def _xmm_f32s(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    vals = []
    for index in range(4):
        vals.append(data.GetFloat(error, index * 4) if data.IsValid() else None)
        if not error.Success():
            vals[-1] = None
    return vals


def hit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    rcx = _u(frame, "rcx")
    rdx = _u(frame, "rdx")
    rdi = _u(frame, "rdi")
    r8 = _u(frame, "r8")
    r9 = _u(frame, "r9")
    r15 = _u(frame, "r15")

    third_data = _read(process, rbp - 0x4300, 4)
    adjusted_xy_data = _read(process, rbp - 0x1288, 8)
    source_vec4_data = _read(process, rcx + rdi, 16)
    dest_vec4_data = _read(process, rdx + rdi, 16)

    if None in (third_data, adjusted_xy_data, source_vec4_data, dest_vec4_data):
        builtins.l16_tuple_consumer_first = {
            "error": "failed to read tuple-consumer packet",
            "rip": _u(frame, "rip"),
            "rbp": rbp,
            "source_base_rcx": rcx,
            "dest_base_rdx": rdx,
            "byte_offset_rdi": rdi,
        }
        return

    builtins.l16_tuple_consumer_first = {
        "rip": _u(frame, "rip"),
        "rbp": rbp,
        "partner_record_index_r15": r15,
        "source_base_rcx": rcx,
        "dest_base_rdx": rdx,
        "byte_offset_rdi": rdi,
        "source_row_stride_bytes_r9": r9,
        "dest_row_stride_bytes_r8": r8,
        "third_tuple_scalar_stack": _f32(third_data),
        "adjusted_tuple_xy": _f32s(adjusted_xy_data),
        "multiplier_vec4_xmm0": _xmm_f32s(frame, "xmm0"),
        "running_scalar_sum_xmm2": _xmm_f32s(frame, "xmm2"),
        "source_vec4_before_mul": _f32s(source_vec4_data),
        "dest_vec4_before_add": _f32s(dest_vec4_data),
    }


def report(label):
    if not hasattr(builtins, "l16_tuple_consumer_first"):
        reset()
    print("L16_TUPLE_CONSUMER_PROBE_BEGIN", label)
    print("consumer_packet", builtins.l16_tuple_consumer_first)
    print("L16_TUPLE_CONSUMER_PROBE_END", label)
