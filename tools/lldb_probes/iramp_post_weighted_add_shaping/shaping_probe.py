import builtins
import struct


def reset():
    builtins.l16_post_weighted_clamp_first = None
    builtins.l16_post_weighted_transform_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


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


def _clamp(value, lo, hi):
    return min(max(value, lo), hi)


def hit_clamp(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    rax = _u(frame, "rax")
    rcx = _u(frame, "rcx")
    rdx = _u(frame, "rdx")
    rsi = _u(frame, "rsi")

    reference_data = _read(process, rdx, 16)
    dest_data = _read(process, rax, 16)
    weighted_data = _read(process, rcx, 16)

    if None in (reference_data, dest_data, weighted_data):
        builtins.l16_post_weighted_clamp_first = {
            "error": "failed to read clamp/update packet",
            "rip": _u(frame, "rip"),
            "rbp": rbp,
            "reference_base_rdx": rdx,
            "dest_base_rax": rax,
            "weighted_base_rcx": rcx,
        }
        return

    reference = _f32s(reference_data)
    dest_before = _f32s(dest_data)
    weighted = _f32s(weighted_data)
    scale_vec = _xmm_f32s(frame, "xmm0")
    clamp_min = _xmm_f32s(frame, "xmm1")
    clamp_max = _xmm_f32s(frame, "xmm2")
    alpha = weighted[3]
    raw_delta = [
        (reference[i] - dest_before[i]) * scale_vec[i] * alpha for i in range(4)
    ]
    clamped_delta = [
        _clamp(raw_delta[i], clamp_min[i], clamp_max[i]) for i in range(4)
    ]
    predicted_after = [
        weighted[i] + dest_before[i] + clamped_delta[i] for i in range(4)
    ]

    builtins.l16_post_weighted_clamp_first = {
        "rip": _u(frame, "rip"),
        "rbp": rbp,
        "remaining_columns_rsi": rsi,
        "reference_addr_rdx": rdx,
        "dest_addr_rax": rax,
        "weighted_addr_rcx": rcx,
        "reference_vec4": reference,
        "dest_vec4_before": dest_before,
        "weighted_vec4": weighted,
        "scale_vec_xmm0": scale_vec,
        "clamp_min_xmm1": clamp_min,
        "clamp_max_xmm2": clamp_max,
        "alpha_from_weighted_lane3": alpha,
        "raw_delta": raw_delta,
        "clamped_delta": clamped_delta,
        "predicted_dest_vec4_after": predicted_after,
    }


def hit_transform(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    rbx = _u(frame, "rbx")
    rdi = _u(frame, "rdi")
    addr = rdi + rbx - 0x10

    vec_data = _read(process, addr, 16)
    if vec_data is None:
        builtins.l16_post_weighted_transform_first = {
            "error": "failed to read transform packet",
            "rip": _u(frame, "rip"),
            "rbp": rbp,
            "addr": addr,
        }
        return

    vec = _f32s(vec_data)
    row0 = _xmm_f32s(frame, "xmm0")
    row1 = _xmm_f32s(frame, "xmm1")
    row2 = _xmm_f32s(frame, "xmm2")
    lane3_source = _xmm_f32s(frame, "xmm3")
    predicted = [
        vec[0] * row0[i] + vec[1] * row1[i] + vec[2] * row2[i]
        for i in range(4)
    ]
    predicted[3] = lane3_source[3]

    builtins.l16_post_weighted_transform_first = {
        "rip": _u(frame, "rip"),
        "rbp": rbp,
        "vec_addr": addr,
        "source_vec4_before_transform": vec,
        "row0_xmm0": row0,
        "row1_xmm1": row1,
        "row2_xmm2": row2,
        "lane3_source_xmm3": lane3_source,
        "predicted_vec4_after_transform": predicted,
    }


def report(label):
    if not hasattr(builtins, "l16_post_weighted_clamp_first"):
        reset()
    print("L16_POST_WEIGHTED_SHAPING_PROBE_BEGIN", label)
    print("clamp_packet", builtins.l16_post_weighted_clamp_first)
    print("transform_packet", builtins.l16_post_weighted_transform_first)
    print("L16_POST_WEIGHTED_SHAPING_PROBE_END", label)
