import builtins
import struct


def reset():
    builtins.l16_tuple_post_recip_add_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


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
    rax = _u(frame, "rax")
    rcx = _u(frame, "rcx")
    rdx = _u(frame, "rdx")
    rdi = _u(frame, "rdi")
    r8 = _u(frame, "r8")
    r9 = _u(frame, "r9")
    r10 = _u(frame, "r10")
    r13 = _u(frame, "r13")
    rsi = _u(frame, "rsi")

    recip_packet_data = _read(process, rbp - 0x42F0, 16)
    source_vec4_data = _read(process, r10 + rdi, 16)
    dest_vec4_data = _read(process, rsi + rdi, 16)
    weight_holder_data = _read(process, r13 + 0x28, 8)

    if None in (recip_packet_data, source_vec4_data, dest_vec4_data, weight_holder_data):
        builtins.l16_tuple_post_recip_add_first = {
            "error": "failed to read post-reciprocal weighted-add packet",
            "rip": _u(frame, "rip"),
            "rbp": rbp,
            "r13": r13,
            "source_base_r10": r10,
            "dest_addr_rsi_plus_rdi": rsi + rdi,
            "byte_offset_rdi": rdi,
        }
        return

    weight_holder = _u64(weight_holder_data)
    weight_base_data = _read(process, weight_holder, 8) if weight_holder else None
    weight_base = _u64(weight_base_data) if weight_base_data is not None else 0
    weight_inner_data = _read(process, weight_base + rdx * 4, 4) if weight_base else None
    weight_outer_data = _read(process, weight_base + rcx * 4, 4) if weight_base else None

    if None in (weight_base_data, weight_inner_data, weight_outer_data):
        builtins.l16_tuple_post_recip_add_first = {
            "error": "failed to read weight table packet",
            "rip": _u(frame, "rip"),
            "r13": r13,
            "weight_holder": weight_holder,
            "weight_base": weight_base,
            "inner_index_rdx": rdx,
            "outer_index_rcx": rcx,
        }
        return

    source_vec4 = _f32s(source_vec4_data)
    dest_vec4 = _f32s(dest_vec4_data)
    xmm4 = _xmm_f32s(frame, "xmm4")
    blended_vec4 = list(source_vec4)
    blended_vec4[3] = xmm4[3]
    weight_inner = _f32(weight_inner_data)
    weight_outer = _f32(weight_outer_data)
    weight_product = weight_inner * weight_outer
    predicted_after = [dest_vec4[i] + weight_product * blended_vec4[i] for i in range(4)]

    builtins.l16_tuple_post_recip_add_first = {
        "rip": _u(frame, "rip"),
        "rbp": rbp,
        "dimension_eax": rax & 0xFFFFFFFF,
        "outer_index_rcx": rcx,
        "inner_index_rdx": rdx,
        "byte_offset_rdi": rdi,
        "dest_row_stride_bytes_r8": r8,
        "source_row_stride_bytes_r9": r9,
        "source_base_r10": r10,
        "dest_base_rsi": rsi,
        "r13": r13,
        "reciprocal_packet_stack_rbp_minus_0x42f0": _f32s(recip_packet_data),
        "xmm4_before_blend": xmm4,
        "source_vec4_before_blend": source_vec4,
        "blended_vec4_for_weighted_add": blended_vec4,
        "dest_vec4_before_add": dest_vec4,
        "weight_holder": weight_holder,
        "weight_base": weight_base,
        "weight_inner_at_rdx": weight_inner,
        "weight_outer_at_rcx": weight_outer,
        "weight_product": weight_product,
        "predicted_dest_vec4_after_add": predicted_after,
    }


def report(label):
    if not hasattr(builtins, "l16_tuple_post_recip_add_first"):
        reset()
    print("L16_TUPLE_POST_RECIP_ADD_PROBE_BEGIN", label)
    print("post_recip_add_packet", builtins.l16_tuple_post_recip_add_first)
    print("L16_TUPLE_POST_RECIP_ADD_PROBE_END", label)
